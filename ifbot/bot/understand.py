"""Turn raw user text into something modules can match on."""

from __future__ import annotations

import difflib
import re
import unicodedata
from typing import Iterable, List, Optional

# Chat-speak and common typos, applied per word after lowercasing.
_SLANG = {
    "u": "you",
    "ur": "your",
    "r": "are",
    "pls": "please",
    "plz": "please",
    "thx": "thanks",
    "thanx": "thanks",
    "tnx": "thanks",
    "ty": "thanks",
    "hru": "how are you",
    "wassup": "what is up",
    "sup": "what is up",
    "gonna": "going to",
    "wanna": "want to",
    "gotta": "got to",
    "cya": "goodbye",
    "idk": "i do not know",
    "abt": "about",
    "hii": "hi",
    "hiii": "hi",
    "helo": "hello",
    "hellooo": "hello",
    "heya": "hey",
    "im": "i am",
    "dont": "do not",
    "cant": "can not",
    "whats": "what is",
    "thats": "that is",
    "wats": "what is",
    "whos": "who is",
}

_CONTRACTIONS = [
    (re.compile(r"\bcan't\b"), "can not"),
    (re.compile(r"\bwon't\b"), "will not"),
    (re.compile(r"\blet's\b"), "let us"),
    (re.compile(r"n't\b"), " not"),
    (re.compile(r"'re\b"), " are"),
    (re.compile(r"'m\b"), " am"),
    (re.compile(r"'ll\b"), " will"),
    (re.compile(r"'ve\b"), " have"),
    (re.compile(r"\b(what|who|where|how|when|that|there|here|it)'s\b"), r"\1 is"),
]

_WORD = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?")


def normalise(text: str) -> str:
    """Lowercase, fold unicode, expand contractions and chat-speak, squash whitespace.

    Punctuation that matters for arithmetic (+ - * / ^ % . ( )) is kept.
    """
    text = unicodedata.normalize("NFKC", str(text))
    text = text.replace("’", "'").replace("‘", "'").replace("−", "-")
    text = text.lower()
    for pattern, repl in _CONTRACTIONS:
        text = pattern.sub(repl, text)
    words = []
    for chunk in text.split():
        stripped = chunk.strip(".,!?;:\"'")
        words.append(_SLANG.get(stripped, chunk))
    return re.sub(r"\s+", " ", " ".join(words)).strip()


def tokenize(text: str) -> List[str]:
    """Word tokens of already-normalised text."""
    return _WORD.findall(text)


def correct(token: str, vocabulary: Iterable[str], cutoff: float = 0.8) -> str:
    """Snap a token to a close vocabulary word, if there is one. Short tokens are left alone."""
    if len(token) < 4:
        return token
    vocab = list(vocabulary)
    if token in vocab:
        return token
    close = difflib.get_close_matches(token, vocab, n=1, cutoff=cutoff)
    return close[0] if close else token


def has_any(tokens: Iterable[str], words: Iterable[str]) -> bool:
    wanted = set(words)
    return any(t in wanted for t in tokens)


def first_match(tokens: List[str], words: Iterable[str]) -> Optional[str]:
    wanted = set(words)
    for t in tokens:
        if t in wanted:
            return t
    return None
