"""The gate: validate a candidate, test it, score it on held-out data, keep it only if it is better.

Candidate code is never imported into this process. Its tests and its answers both run in
separate interpreters with a timeout. The static checks here are a tripwire against obvious
cheating, not a sandbox.
"""

from __future__ import annotations

import ast
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from ..evals.dataset import Row, load_rows
from ..evals.judge import Judge, OverlapJudge
from ..evals.run import DEFAULT_TIMEOUT, BotRunError, evaluate
from ..paths import bot_dir, data_path, ledger_path, resolve_root
from .ledger import Ledger
from .workspace import IGNORE, bot_test_files

log = logging.getLogger("ifbot.gate")

ALLOWED_TOP_LEVEL = {"bot", "tests", "data", "BRIEF.md"}
ALLOWED_BOT_SUFFIXES = {".py", ".json", ".txt"}
MAX_BOT_BYTES = 500_000

FORBIDDEN_IMPORTS = {
    "subprocess", "socket", "ssl", "urllib", "http", "ftplib", "smtplib", "poplib", "imaplib",
    "telnetlib", "xmlrpc", "socketserver", "ctypes", "multiprocessing", "webbrowser", "builtins",
    "gc", "inspect", "asyncio", "threading", "signal", "pty", "shutil",
}
ENGINE_ONLY_IMPORTS = {"importlib", "pkgutil"}  # discovery lives in bot/engine.py
FORBIDDEN_NAMES = {"eval", "exec", "compile", "__import__", "breakpoint"}
FORBIDDEN_OS_ATTRS = {
    "system", "popen", "fork", "forkpty", "kill", "killpg", "startfile",
    "posix_spawn", "posix_spawnp",
}
FORBIDDEN_OS_PREFIXES = ("exec", "spawn")
FORBIDDEN_ATTRS = {"_getframe", "_current_frames"}

_FALLBACK_STDLIB = frozenset(
    """__future__ abc argparse array ast base64 bisect calendar cmath collections colorsys copy
    csv dataclasses datetime decimal difflib enum errno fnmatch fractions functools gettext glob
    heapq hashlib html itertools json keyword locale logging math numbers operator os pathlib
    pkgutil pprint random re secrets statistics string struct sys textwrap time types typing
    unicodedata uuid warnings weakref zlib importlib""".split()
)


def _stdlib() -> frozenset:
    return getattr(sys, "stdlib_module_names", _FALLBACK_STDLIB)


@dataclass
class GateResult:
    candidate: str
    accepted: bool
    reason: str
    tests_passed: Optional[bool] = None
    dev_win_rate: Optional[float] = None
    heldout_win_rate: Optional[float] = None
    bot_lines: Optional[int] = None


# ---------------------------------------------------------------------------------- validation


def _norm(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def _walk_files(base: Path) -> List[Path]:
    out = []
    for dirpath, dirnames, filenames in os.walk(str(base)):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for name in sorted(dirnames + filenames):
            out.append(Path(dirpath) / name)
    return out


def check_layout(candidate_dir: Path, root: Path) -> Optional[str]:
    """Reject files outside bot/, and any change to the tests or data the workspace shipped."""
    if not candidate_dir.is_dir():
        return "candidate directory does not exist: %s" % candidate_dir
    if not (candidate_dir / "bot").is_dir() or (candidate_dir / "bot").is_symlink():
        return "candidate has no bot/ directory"
    for entry in sorted(candidate_dir.iterdir()):
        if entry.name in (".DS_Store",):
            continue
        if entry.name not in ALLOWED_TOP_LEVEL:
            return "candidate adds files outside bot/: %s" % entry.name
        if entry.is_symlink():
            return "candidate contains a symlink: %s" % entry.name

    shipped = {"tests/" + f.name: f.read_bytes() for f in bot_test_files(root)}
    shipped["data/dev.jsonl"] = data_path(root, "dev").read_bytes()
    for sub in ("tests", "data"):
        base = candidate_dir / sub
        if not base.exists():
            continue
        for path in _walk_files(base):
            if path.is_symlink():
                return "candidate contains a symlink: %s" % path.relative_to(candidate_dir)
            if path.suffix == ".pyc" or path.name == ".DS_Store" or path.is_dir():
                continue
            rel = path.relative_to(candidate_dir).as_posix()
            if rel not in shipped:
                return "candidate adds files outside bot/: %s" % rel
            if path.read_bytes() != shipped[rel]:
                return "candidate edits files outside bot/: %s" % rel
    return None


def _string_constants(tree: ast.AST) -> List[str]:
    return [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def _json_strings(value: Any) -> List[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in list(value.keys()) + list(value.values()) for s in _json_strings(v)]
    if isinstance(value, list):
        return [s for v in value for s in _json_strings(v)]
    return []


def _check_ast(tree: ast.AST, rel: Path) -> Optional[str]:
    stdlib = _stdlib()
    depth = len(rel.parts) - 1  # directories between bot/ and the file
    is_engine = rel.as_posix() == "engine.py"
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                problem = _check_module(alias.name, stdlib, is_engine)
                if problem:
                    return "%s: %s" % (rel, problem)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                if node.level > depth + 1:
                    return "%s: relative import escapes the bot package" % rel
                continue
            problem = _check_module(node.module or "", stdlib, is_engine)
            if problem:
                return "%s: %s" % (rel, problem)
            if node.module == "os":
                for alias in node.names:
                    if alias.name in FORBIDDEN_OS_ATTRS or alias.name.startswith(FORBIDDEN_OS_PREFIXES):
                        return "%s: forbidden call os.%s" % (rel, alias.name)
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            return "%s: forbidden builtin %s" % (rel, node.id)
        elif isinstance(node, ast.Attribute):
            if node.attr in FORBIDDEN_ATTRS:
                return "%s: forbidden attribute %s" % (rel, node.attr)
            if isinstance(node.value, ast.Name) and node.value.id == "os":
                if node.attr in FORBIDDEN_OS_ATTRS or node.attr.startswith(FORBIDDEN_OS_PREFIXES):
                    return "%s: forbidden call os.%s" % (rel, node.attr)
    return None


def _check_module(name: str, stdlib: frozenset, is_engine: bool) -> Optional[str]:
    root_name = name.split(".")[0]
    if root_name in FORBIDDEN_IMPORTS:
        return "forbidden import %s" % root_name
    if root_name in ENGINE_ONLY_IMPORTS:
        return None if is_engine else "import %s is only allowed in engine.py" % root_name
    if root_name not in stdlib:
        return "import outside the standard library: %s" % root_name
    return None


def check_bot_source(bot: Path, heldout: Sequence[Row]) -> Optional[str]:
    """Static checks on a bot directory. Returns a reason string if it must be rejected."""
    if not (bot / "__init__.py").is_file():
        return "bot/ has no __init__.py"
    total = 0
    texts = []  # type: List[Tuple[Path, str, List[str]]]  (relpath, full text, string literals)
    for path in _walk_files(bot):
        rel = path.relative_to(bot)
        if path.is_symlink():
            return "bot/ contains a symlink: %s" % rel.as_posix()
        if path.is_dir():
            continue
        if path.suffix == ".pyc":
            continue
        if path.suffix not in ALLOWED_BOT_SUFFIXES:
            return "bot/ contains an unexpected file type: %s" % rel.as_posix()
        total += path.stat().st_size
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return "bot/%s is not valid UTF-8" % rel.as_posix()
        literals = []  # type: List[str]
        if path.suffix == ".py":
            try:
                tree = ast.parse(text, filename=str(rel))
            except SyntaxError as exc:
                return "syntax error in bot/%s: %s" % (rel.as_posix(), exc.msg)
            problem = _check_ast(tree, rel)
            if problem:
                return problem
            literals = _string_constants(tree)
        elif path.suffix == ".json":
            try:
                literals = _json_strings(json.loads(text))
            except ValueError:
                return "bot/%s is not valid JSON" % rel.as_posix()
        else:
            literals = text.splitlines()
        texts.append((rel, text, literals))
    if total > MAX_BOT_BYTES:
        return "bot/ is larger than %d bytes" % MAX_BOT_BYTES
    return _check_heldout_leak(texts, heldout)


def _check_heldout_leak(texts, heldout: Sequence[Row]) -> Optional[str]:
    """Reject if a held-out instruction (or long reference answer) appears verbatim."""
    for rel, text, literals in texts:
        whole = " %s " % _norm(text)
        joined = " %s " % _norm(" ".join(literals))
        constants = {_norm(s) for s in literals}
        for row in heldout:
            for label, value in (("instruction", row.instruction), ("reference answer", row.output)):
                needle = _norm(value)
                if not needle:
                    continue
                long_enough = len(needle.split()) >= 5
                if not long_enough and row.category == "smalltalk":
                    continue  # "good morning" is in every chatbot; it is not a leak
                hit = (long_enough and (" %s " % needle in whole or " %s " % needle in joined)) or (
                    needle in constants
                )
                if hit:
                    return "bot/%s contains held-out %s %s" % (rel.as_posix(), label, row.id)
    return None


def validate(candidate_dir: Union[str, Path], root: Optional[Union[str, Path]] = None) -> Optional[str]:
    """Layout and source checks. Returns None if the candidate may proceed."""
    root = resolve_root(root)
    candidate_dir = Path(candidate_dir)
    problem = check_layout(candidate_dir, root)
    if problem:
        return problem
    return check_bot_source(candidate_dir / "bot", load_rows(data_path(root, "heldout")))


# ---------------------------------------------------------------------------------- running


def _child_env() -> Dict[str, str]:
    return {"PATH": os.environ.get("PATH", ""), "PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1"}


def run_bot_tests(stage: Path, timeout: float) -> Tuple[bool, str]:
    """Run the real bot tests against stage/bot in a subprocess."""
    cmd = [sys.executable, "-I", "-m", "unittest", "discover", "-s", "tests", "-p", "test_bot_*.py"]
    try:
        proc = subprocess.run(
            cmd, cwd=str(stage), env=_child_env(), capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return False, "tests timed out after %gs" % timeout
    tail = (proc.stderr.strip().splitlines() or proc.stdout.strip().splitlines() or [""])[-1]
    return proc.returncode == 0, tail


def _stage(bot_src: Path, root: Path, stage: Path) -> None:
    shutil.copytree(str(bot_src), str(stage / "bot"), symlinks=True, ignore=IGNORE)
    (stage / "tests").mkdir()
    for f in bot_test_files(root):
        shutil.copy2(str(f), str(stage / "tests" / f.name))


def count_lines(bot: Path) -> int:
    n = 0
    for path in _walk_files(bot):
        if path.suffix == ".py" and path.is_file():
            n += sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    return n


def candidate_id(bot: Path) -> str:
    h = hashlib.sha1()
    for path in _walk_files(bot):
        if path.is_file() and path.suffix != ".pyc":
            h.update(path.relative_to(bot).as_posix().encode())
            h.update(path.read_bytes())
    return "cand-" + h.hexdigest()[:8]


def install_bot(new_bot: Path, root: Path) -> None:
    """Replace ifbot/bot with new_bot, keeping the old copy until the swap succeeds."""
    target = bot_dir(root)
    fresh, old = target.with_name("bot.new"), target.with_name("bot.old")
    for leftover in (fresh, old):
        if leftover.exists():
            shutil.rmtree(str(leftover))
    shutil.copytree(str(new_bot), str(fresh), ignore=IGNORE)
    target.rename(old)
    try:
        fresh.rename(target)
    except OSError:
        old.rename(target)
        raise
    shutil.rmtree(str(old))


def _record_baseline(root: Path, ledger: Ledger, judge: Judge, timeout: float) -> None:
    dev = load_rows(data_path(root, "dev"))
    heldout = load_rows(data_path(root, "heldout"))
    with tempfile.TemporaryDirectory(prefix="ifbot-gate-") as tmp:
        stage = Path(tmp)
        _stage(bot_dir(root), root, stage)
        tests_ok, _ = run_bot_tests(stage, timeout)
        dev_rate = evaluate(stage / "bot", dev, judge, isolate=True, timeout=timeout)["win_rate"]
        held_rate = evaluate(stage / "bot", heldout, judge, isolate=True, timeout=timeout)["win_rate"]
        ledger.append(
            {
                "candidate": "baseline",
                "tests_passed": tests_ok,
                "dev_win_rate": dev_rate,
                "heldout_win_rate": held_rate,
                "accepted": True,
                "reason": "baseline: current bot recorded",
                "bot_lines": count_lines(stage / "bot"),
            }
        )


def submit(
    candidate_dir: Union[str, Path],
    root: Optional[Union[str, Path]] = None,
    judge: Optional[Judge] = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> GateResult:
    """Run the full gate on a candidate workspace and record the outcome in the ledger."""
    root = resolve_root(root)
    judge = judge or OverlapJudge()
    candidate_dir = Path(candidate_dir).resolve()
    ledger = Ledger(ledger_path(root))

    if ledger.best() is None:
        _record_baseline(root, ledger, judge, timeout)
    best = ledger.best()
    assert best is not None

    cid = candidate_id(candidate_dir / "bot") if (candidate_dir / "bot").is_dir() else "cand-none"

    def finish(accepted: bool, reason: str, **fields: Any) -> GateResult:
        result = GateResult(cid, accepted, reason, **fields)
        ledger.append(
            {
                "candidate": cid,
                "tests_passed": result.tests_passed,
                "dev_win_rate": result.dev_win_rate,
                "heldout_win_rate": result.heldout_win_rate,
                "accepted": accepted,
                "reason": reason,
                "bot_lines": result.bot_lines,
            }
        )
        log.info("%s %s: %s", cid, "ACCEPTED" if accepted else "rejected", reason)
        return result

    problem = validate(candidate_dir, root)
    if problem:
        return finish(False, "invalid: " + problem)

    dev = load_rows(data_path(root, "dev"))
    heldout = load_rows(data_path(root, "heldout"))
    with tempfile.TemporaryDirectory(prefix="ifbot-gate-") as tmp:
        stage = Path(tmp)
        _stage(candidate_dir / "bot", root, stage)  # work on a private copy from here on
        lines = count_lines(stage / "bot")

        tests_ok, detail = run_bot_tests(stage, timeout)
        if not tests_ok:
            return finish(False, "tests failed: " + detail, tests_passed=False, bot_lines=lines)
        try:
            dev_rate = evaluate(stage / "bot", dev, judge, isolate=True, timeout=timeout)["win_rate"]
            held_rate = evaluate(stage / "bot", heldout, judge, isolate=True, timeout=timeout)["win_rate"]
        except BotRunError as exc:
            return finish(False, "bot run failed: %s" % exc, tests_passed=True, bot_lines=lines)

        common = dict(tests_passed=True, dev_win_rate=dev_rate, heldout_win_rate=held_rate, bot_lines=lines)
        if held_rate > best:
            install_bot(stage / "bot", root)
            return finish(
                True, "held-out win rate %.3f beats best %.3f" % (held_rate, best), **common
            )
        return finish(
            False,
            "held-out win rate %.3f does not beat best %.3f" % (held_rate, best),
            **common
        )
