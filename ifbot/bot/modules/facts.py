"""A small lookup table of facts. Each row: keywords that must all be present, and the answer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..arbiter import Proposal

if TYPE_CHECKING:  # pragma: no cover
    from ..engine import Context

FACTS = [
    (("water", "boil"), "Water boils at 100 degrees Celsius at sea level."),
    (("water", "freeze"), "Water freezes at 0 degrees Celsius."),
    (("closest", "star"), "The closest star to Earth is the Sun."),
    (("states", "matter"), "The three common states of matter are solid, liquid, and gas."),
    (("capital", "france"), "The capital of France is Paris."),
    (("days", "week"), "There are seven days in a week."),
    (("minutes", "hour"), "There are sixty minutes in an hour."),
    (("hours", "day"), "There are twenty-four hours in a day."),
]


def _forms(tokens):
    """Tokens plus a crude singular of each, so 'boils' matches 'boil'."""
    out = set(tokens)
    for t in tokens:
        if len(t) > 3 and t.endswith("s"):
            out.add(t[:-1])
    return out


def propose(ctx: "Context") -> Optional[Proposal]:
    seen = _forms(ctx.tokens)
    best = None
    for keys, answer in FACTS:
        if all(k in seen for k in keys):
            confidence = min(0.7 + 0.05 * len(keys), 0.9)
            if best is None or confidence > best.confidence:
                best = Proposal(answer, confidence)
    return best
