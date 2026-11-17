"""Learn the user's name ("I'm Sam") and answer "what's my name"."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Optional

from ..arbiter import Proposal

if TYPE_CHECKING:  # pragma: no cover
    from ..engine import Context

_NAME = r"([A-Za-z][A-Za-z'\-]{1,19})"
_STRONG = [
    re.compile(r"\bmy name is\s+" + _NAME, re.IGNORECASE),
    re.compile(r"\bcall me\s+" + _NAME, re.IGNORECASE),
]
_WEAK = re.compile(r"\b(?:i am|i'm|i’m|im)\s+" + _NAME + r"(\s*[.!,;]*\s*)$", re.IGNORECASE)
_WEAK_MID = re.compile(r"\b(?:i am|i'm|i’m)\s+" + _NAME, re.IGNORECASE)

# Words that follow "I'm" but are not names.
_NOT_NAMES = frozenset(
    """a an the not so very really just fine good great well ok okay tired hungry happy sad bored sick
    sorry back here there new in on at from with going looking trying wondering asking thinking
    student teacher late early ready sure glad afraid curious interested lost confused busy
    alone online home free done""".split()
)

_ASK_MY_NAME = (
    ("what", "is", "my", "name"),
    ("who", "am", "i"),
    ("do", "you", "know", "my", "name"),
    ("do", "you", "remember", "my", "name"),
    ("tell", "me", "my", "name"),
)


def _clean(word: str) -> Optional[str]:
    low = word.lower()
    if low in _NOT_NAMES or low.endswith("ing") or low.endswith("ed"):
        return None
    return word[0].upper() + word[1:]


def extract_name(raw: str) -> Optional[str]:
    """Return a name if the message introduces one, else None."""
    for pattern in _STRONG:
        m = pattern.search(raw)
        if m:
            return m.group(1)[0].upper() + m.group(1)[1:]
    # "I'm Sam": accept a capitalised word anywhere, or a lowercase word that ends the message.
    m = _WEAK_MID.search(raw)
    if m and m.group(1)[0].isupper():
        return _clean(m.group(1))
    m = _WEAK.search(raw)
    if m:
        return _clean(m.group(1))
    return None


def _asks_my_name(tokens) -> bool:
    joined = " ".join(tokens)
    return any(" ".join(p) in joined for p in _ASK_MY_NAME)


def learn(ctx: "Context") -> None:
    name = extract_name(ctx.raw)
    if name:
        ctx.memory.user_name = name


def propose(ctx: "Context") -> Optional[Proposal]:
    if _asks_my_name(ctx.tokens):
        if ctx.memory.user_name:
            return Proposal("Your name is %s." % ctx.memory.user_name, 0.9)
        return Proposal("I don't know your name yet. What should I call you?", 0.85)
    name = extract_name(ctx.raw)
    if name:
        return Proposal("Nice to meet you, %s." % name, 0.8)
    return None
