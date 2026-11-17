"""Score a bot against benchmark rows with a judge."""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from .dataset import Row
from .judge import Judge

log = logging.getLogger("ifbot.eval")

WORKER = Path(__file__).resolve().parent / "worker.py"
DEFAULT_TIMEOUT = 60.0


class BotRunError(RuntimeError):
    """The bot could not be run (crash, hang, or unreadable output)."""


def load_package(bot_dir: Path):
    name = "_ifbot_eval_" + uuid.uuid4().hex[:8]
    spec = importlib.util.spec_from_file_location(
        name, str(bot_dir / "__init__.py"), submodule_search_locations=[str(bot_dir)]
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        _unload(name)
        raise
    return module


def _unload(prefix: str) -> None:
    for key in [k for k in sys.modules if k == prefix or k.startswith(prefix + ".")]:
        del sys.modules[key]


def _replies_inprocess(bot_dir: Path, rows: Sequence[Row]) -> List[Dict[str, str]]:
    package = load_package(bot_dir)
    try:
        out = []
        for row in rows:
            bot = package.Bot(seed=0)  # fresh conversation per row
            reply = bot.respond(row.instruction)
            out.append({"id": row.id, "text": reply.text, "module": reply.module})
        return out
    finally:
        _unload(package.__name__)


def _replies_isolated(bot_dir: Path, rows: Sequence[Row], timeout: float) -> List[Dict[str, str]]:
    payload = json.dumps([{"id": r.id, "instruction": r.instruction} for r in rows])
    env = {"PATH": os.environ.get("PATH", ""), "PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1"}
    with tempfile.TemporaryDirectory(prefix="ifbot-run-") as cwd:  # empty cwd: nothing to read
        try:
            proc = subprocess.run(
                [sys.executable, "-I", str(WORKER), str(bot_dir)],
                input=payload,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                env=env,
            )
        except subprocess.TimeoutExpired:
            raise BotRunError("bot run timed out after %gs" % timeout)
    if proc.returncode != 0:
        tail = proc.stderr.strip().splitlines()[-1:] or ["no stderr"]
        raise BotRunError("bot run failed (exit %d): %s" % (proc.returncode, tail[0][:200]))
    try:
        data = json.loads(proc.stdout)
        if not isinstance(data, list) or len(data) != len(rows):
            raise ValueError("wrong number of replies")
        for item in data:
            if not isinstance(item.get("text"), str):
                raise ValueError("reply text is not a string")
    except (ValueError, AttributeError) as exc:
        raise BotRunError("bot run produced unreadable output: %s" % exc)
    return data


def evaluate(
    bot_package_dir: Union[str, Path],
    rows: Sequence[Row],
    judge: Judge,
    isolate: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """Score the bot package in bot_package_dir. Every row starts a fresh conversation.

    isolate=True answers the rows in a separate interpreter (use it for code you do not trust).
    Raises BotRunError if an isolated run crashes or times out.
    """
    bot_dir = Path(bot_package_dir).resolve()
    replies = _replies_isolated(bot_dir, rows, timeout) if isolate else _replies_inprocess(bot_dir, rows)
    by_id = {r["id"]: r for r in replies}

    wins = 0
    by_category = {}  # type: Dict[str, Dict[str, Any]]
    failures = []  # type: List[Dict[str, str]]
    for row in rows:
        reply = by_id[row.id]
        try:
            won = bool(judge.judge(row.instruction, row.output, reply["text"]))
        except Exception:
            log.exception("judge raised on %s; counting as a loss", row.id)
            won = False
        cat = by_category.setdefault(row.category, {"wins": 0, "total": 0})
        cat["total"] += 1
        if won:
            wins += 1
            cat["wins"] += 1
        else:
            failures.append(
                {
                    "id": row.id,
                    "category": row.category,
                    "instruction": row.instruction,
                    "reference": row.output,
                    "reply": reply["text"],
                    "module": reply.get("module", ""),
                }
            )
    for cat in by_category.values():
        cat["win_rate"] = cat["wins"] / cat["total"] if cat["total"] else 0.0
    total = len(rows)
    return {
        "win_rate": wins / total if total else 0.0,
        "wins": wins,
        "total": total,
        "by_category": by_category,
        "failures": failures,
    }
