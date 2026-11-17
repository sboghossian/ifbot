"""Always answers, at near-zero confidence, so something comes back when nothing else matches."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..arbiter import Proposal

if TYPE_CHECKING:  # pragma: no cover
    from ..engine import Context

_VARIANTS = (
    "I don't know that one yet. Could you rephrase it?",
    "I'm not sure how to answer that yet. Try asking another way.",
)


def propose(ctx: "Context") -> Optional[Proposal]:
    if not ctx.tokens:
        return Proposal("I didn't catch anything. Say something and I'll do my best.", 0.05)
    return Proposal(ctx.rng.choice(_VARIANTS), 0.01)
