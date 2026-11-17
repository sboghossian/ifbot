"""Say hello back."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..arbiter import Proposal
from ..understand import correct
from .name import extract_name

if TYPE_CHECKING:  # pragma: no cover
    from ..engine import Context

_GREETINGS = ("hello", "hi", "hey", "hiya", "howdy", "yo", "greetings", "hallo", "ciao")
_DAYPARTS = ("morning", "afternoon", "evening")
_VARIANTS = (
    "Hello! How can I help you today?",
    "Hi there! What can I do for you?",
)


def _greeting_kind(tokens):
    """Return 'daypart:<x>', 'plain' or None, looking at the first few tokens."""
    head = [correct(t, _GREETINGS) for t in tokens[:3]]
    if len(head) >= 2 and head[0] == "good" and head[1] in _DAYPARTS:
        return "daypart:" + head[1]
    if any(t in _GREETINGS for t in head[:2]):
        return "plain"
    return None


def propose(ctx: "Context") -> Optional[Proposal]:
    kind = _greeting_kind(ctx.tokens)
    if kind is None:
        return None
    # A greeting followed by a real question should not win over the answer.
    confidence = 0.9 if len(ctx.tokens) <= 6 else 0.3
    name = ctx.memory.user_name
    if kind.startswith("daypart:"):
        opener = "Good %s" % kind.split(":", 1)[1]
    else:
        opener = ctx.rng.choice(("Hello", "Hi"))
    if name:
        intro = " Nice to meet you." if extract_name(ctx.raw) else ""
        return Proposal("%s, %s!%s How can I help?" % (opener, name, intro), confidence)
    if kind.startswith("daypart:"):
        return Proposal("%s! How can I help you today?" % opener, confidence)
    return Proposal(ctx.rng.choice(_VARIANTS), confidence)
