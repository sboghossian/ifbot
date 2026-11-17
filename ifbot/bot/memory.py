"""Per-conversation state. One Memory lives as long as one conversation."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

MAX_TURNS = 50


class Memory:
    def __init__(self) -> None:
        self.turns = []  # type: List[Tuple[str, str]]
        self.user_name = None  # type: Optional[str]
        self.last_bot = None  # type: Optional[str]
        self.facts = {}  # type: Dict[str, str]

    def add_turn(self, user: str, bot: str) -> None:
        self.turns.append((user, bot))
        if len(self.turns) > MAX_TURNS:
            del self.turns[0 : len(self.turns) - MAX_TURNS]
        self.last_bot = bot

    def remember(self, key: str, value: str) -> None:
        self.facts[key] = value

    def recall(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.facts.get(key, default)
