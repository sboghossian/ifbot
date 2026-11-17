"""The Bot: discovers modules, asks each for a proposal, lets the arbiter pick one."""

from __future__ import annotations

import importlib
import logging
import pkgutil
import random
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

from . import modules as _modules_pkg
from .arbiter import Proposal, Reply, choose
from .memory import Memory
from .understand import normalise, tokenize

log = logging.getLogger("ifbot.bot")

MAX_MESSAGE_CHARS = 2000


@dataclass
class Context:
    raw: str
    text: str
    tokens: List[str]
    memory: Memory
    rng: random.Random


def discover_modules() -> List[Tuple[str, Any]]:
    """Import every module in bot/modules that defines propose(ctx). Sorted by name."""
    found = []
    for info in pkgutil.iter_modules(_modules_pkg.__path__):
        if info.name.startswith("_"):
            continue
        try:
            mod = importlib.import_module("." + info.name, _modules_pkg.__name__)
        except Exception:
            log.exception("could not import module %s", info.name)
            continue
        if callable(getattr(mod, "propose", None)):
            found.append((info.name, mod))
    found.sort(key=lambda item: item[0])
    return found


class Bot:
    def __init__(self, seed: int = 0, modules: Optional[List[Tuple[str, Any]]] = None) -> None:
        self._seed = seed
        self._modules = modules if modules is not None else discover_modules()
        self.memory = Memory()
        self.rng = random.Random(seed)

    @property
    def module_names(self) -> List[str]:
        return [name for name, _ in self._modules]

    def reset(self) -> None:
        """Forget the conversation and restart the random stream."""
        self.memory = Memory()
        self.rng = random.Random(self._seed)

    def respond(self, message: str) -> Reply:
        raw = message if isinstance(message, str) else str(message)
        raw = raw[:MAX_MESSAGE_CHARS]
        text = normalise(raw)
        ctx = Context(raw=raw, text=text, tokens=tokenize(text), memory=self.memory, rng=self.rng)

        for name, mod in self._modules:
            learn = getattr(mod, "learn", None)
            if callable(learn):
                try:
                    learn(ctx)
                except Exception:
                    log.exception("module %s failed in learn()", name)

        proposals = []
        for name, mod in self._modules:
            try:
                proposal = mod.propose(ctx)
            except Exception:
                log.exception("module %s failed in propose()", name)
                continue
            if proposal is not None:
                proposals.append((name, proposal))

        reply = choose(proposals)
        self.memory.add_turn(raw, reply.text)
        return reply
