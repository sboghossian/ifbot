"""Build a candidate workspace: everything a proposer needs, and nothing held out."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Union

from ..evals.dataset import load_rows
from ..evals.judge import Judge, OverlapJudge
from ..evals.run import evaluate
from ..paths import bot_dir, data_path, resolve_root, tests_dir

IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")
MAX_FAILURES_IN_BRIEF = 15


def bot_test_files(root: Path) -> List[Path]:
    """The tests a candidate must pass: test_bot_*.py plus the loader helper they share."""
    t = tests_dir(root)
    return sorted(t.glob("test_bot_*.py")) + [p for p in [t / "botload.py"] if p.exists()]


def build_brief(root: Path, judge: Optional[Judge] = None) -> str:
    judge = judge or OverlapJudge()
    report = evaluate(bot_dir(root), load_rows(data_path(root, "dev")), judge)
    lines = [
        "# Brief",
        "",
        "You are improving a small rules-only chatbot. Edit files under `bot/` only.",
        "",
        "## Rules",
        "",
        "- Change only files inside `bot/`. Anything added or edited elsewhere gets the submission rejected.",
        "- Python standard library only. Inside `bot/`, import your own code with relative imports.",
        "- Do not use subprocess, socket, urllib, http, os.system, eval, exec, compile or __import__.",
        "- No network, no models, no API keys. Answers come from rules and data in `bot/`.",
        "- Run `python -m unittest discover -s tests` from this directory before you stop. Failing tests are a reject.",
        "- You can read `data/dev.jsonl`. Do not look for other data. A different, held-out set of questions "
        "from the same categories decides whether your change is kept.",
        "- Copying reference answers from the dev file word for word will not help: the scoring set has different "
        "questions. Write rules that generalise to the category.",
        "- Add a `propose(ctx)` module under `bot/modules/` or edit an existing one. See `bot/modules/__init__.py`.",
        "",
        "## Current score on dev",
        "",
        "Offline overlap judge (token F1 against the reference): %d of %d questions won (%.3f)."
        % (report["wins"], report["total"], report["win_rate"]),
        "",
        "## Dev questions the bot is currently losing",
        "",
    ]
    for f in report["failures"][:MAX_FAILURES_IN_BRIEF]:
        lines += [
            "- [%s] %s" % (f["category"], f["instruction"]),
            "  - reference: %s" % f["reference"],
            "  - bot said:  %s" % f["reply"],
        ]
    more = len(report["failures"]) - MAX_FAILURES_IN_BRIEF
    if more > 0:
        lines.append("- ... and %d more in data/dev.jsonl" % more)
    lines.append("")
    return "\n".join(lines)


def new_workspace(
    root: Optional[Union[str, Path]] = None,
    dest: Optional[Union[str, Path]] = None,
    judge: Optional[Judge] = None,
) -> Path:
    """Create a workspace with a copy of bot/, the bot tests, dev data and BRIEF.md.

    The held-out file is never copied. Returns the workspace path.
    """
    root = resolve_root(root)
    ws = Path(dest) if dest is not None else Path(tempfile.mkdtemp(prefix="ifbot-ws-"))
    ws.mkdir(parents=True, exist_ok=True)

    shutil.copytree(str(bot_dir(root)), str(ws / "bot"), ignore=IGNORE)
    (ws / "tests").mkdir(exist_ok=True)
    for f in bot_test_files(root):
        shutil.copy2(str(f), str(ws / "tests" / f.name))
    (ws / "data").mkdir(exist_ok=True)
    shutil.copy2(str(data_path(root, "dev")), str(ws / "data" / "dev.jsonl"))
    (ws / "BRIEF.md").write_text(build_brief(root, judge), encoding="utf-8")
    return ws
