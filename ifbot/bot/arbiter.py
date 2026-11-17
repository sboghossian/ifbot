"""Pick one proposal. Deterministic: highest confidence wins, ties go to the module name."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

FALLBACK_TEXT = "I'm not sure how to answer that yet."


@dataclass(frozen=True)
class Proposal:
    text: str
    confidence: float


@dataclass(frozen=True)
class Reply:
    text: str
    module: str
    confidence: float


def _valid(p: object) -> bool:
    return (
        isinstance(p, Proposal)
        and isinstance(p.text, str)
        and p.text.strip() != ""
        and isinstance(p.confidence, (int, float))
        and p.confidence == p.confidence  # not NaN
    )


def choose(proposals: List[Tuple[str, Proposal]]) -> Reply:
    """proposals is a list of (module_name, Proposal). Invalid entries are ignored."""
    good = [(name, p) for name, p in proposals if _valid(p)]
    if not good:
        return Reply(FALLBACK_TEXT, "arbiter", 0.0)
    # Highest confidence first, then alphabetical module name.
    good.sort(key=lambda item: (-min(max(float(item[1].confidence), 0.0), 1.0), item[0]))
    name, best = good[0]
    return Reply(best.text, name, min(max(float(best.confidence), 0.0), 1.0))
