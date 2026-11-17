"""A few stock replies for everyday chat."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..arbiter import Proposal

if TYPE_CHECKING:  # pragma: no cover
    from ..engine import Context

# (all of these tokens, reply, confidence). First match by confidence wins.
RULES = [
    (("how", "are", "you"), "I'm doing fine, thank you. How about you?", 0.85),
    (("what", "is", "your", "name"), "My name is ifbot.", 0.9),
    (("who", "are", "you"), "I'm ifbot, a small rules-based chatbot.", 0.85),
    (("what", "can", "you", "do"), "I can chat a little, do simple sums, and answer a few questions.", 0.85),
    (("who", "made", "you"), "I was written as a tiny seed bot for people and agents to grow.", 0.8),
]
_THANKS = ("thanks", "thank")
_BYE = ("bye", "goodbye", "goodnight")


def propose(ctx: "Context") -> Optional[Proposal]:
    tokens = set(ctx.tokens)
    best = None
    for needed, reply, confidence in RULES:
        if all(n in tokens for n in needed):
            if best is None or confidence > best.confidence:
                best = Proposal(reply, confidence)
    if best is not None:
        return best
    if any(t in tokens for t in _THANKS) and len(ctx.tokens) <= 8:
        return Proposal("You're welcome! Happy to help.", 0.85)
    if any(t in tokens for t in _BYE) or ("see" in tokens and "you" in tokens and "later" in tokens):
        return Proposal("Goodbye! Talk to you soon.", 0.85)
    return None
