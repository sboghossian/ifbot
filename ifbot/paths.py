"""Where things live in a checkout. Everything is relative to a project root."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

DEFAULT_ROOT = Path(__file__).resolve().parent.parent


def resolve_root(root: Optional[Union[str, Path]] = None) -> Path:
    return Path(root).resolve() if root is not None else DEFAULT_ROOT


def bot_dir(root: Path) -> Path:
    return root / "ifbot" / "bot"


def data_path(root: Path, split: str) -> Path:
    if split not in ("dev", "heldout"):
        raise ValueError("split must be 'dev' or 'heldout', got %r" % (split,))
    return root / "data" / (split + ".jsonl")


def tests_dir(root: Path) -> Path:
    return root / "tests"


def ledger_path(root: Path) -> Path:
    return root / "runs" / "ledger.jsonl"
