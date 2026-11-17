"""Judges decide whether a reply "wins" against a reference answer.

OverlapJudge is offline and deterministic but crude. CommandJudge hands the decision to any
shell command you supply, which is how an LLM (or a human) can be plugged in.
"""

from __future__ import annotations

import json
import logging
import re
import subprocess
from collections import Counter
from typing import List, Protocol

log = logging.getLogger("ifbot.judge")

_TOKEN = re.compile(r"[a-z0-9]+")
_VERDICT = re.compile(r"(WIN|LOSS)\b")


class Judge(Protocol):
    def judge(self, instruction: str, reference: str, reply: str) -> bool:
        """Return True if the reply wins."""
        ...


def tokens(text: str) -> List[str]:
    return _TOKEN.findall(text.lower())


def token_f1(reference: str, reply: str) -> float:
    ref, rep = Counter(tokens(reference)), Counter(tokens(reply))
    if not ref or not rep:
        return 0.0
    common = sum((ref & rep).values())
    if common == 0:
        return 0.0
    precision = common / sum(rep.values())
    recall = common / sum(ref.values())
    return 2 * precision * recall / (precision + recall)


class OverlapJudge:
    """Win if token-level F1 between reply and reference is at least threshold."""

    def __init__(self, threshold: float = 0.35) -> None:
        self.threshold = threshold

    @property
    def name(self) -> str:
        return "overlap(threshold=%s)" % self.threshold

    def judge(self, instruction: str, reference: str, reply: str) -> bool:
        return token_f1(reference, reply) >= self.threshold


class CommandJudge:
    """Run a shell command per row. JSON {instruction, reference, reply} goes to stdin.

    Stdout must start with WIN or LOSS. A non-zero exit, a timeout, or anything else counts as
    LOSS and is logged.
    """

    def __init__(self, command: str, timeout: float = 60.0) -> None:
        if not command or not command.strip():
            raise ValueError("judge command is empty")
        self.command = command
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "command(%s)" % self.command

    def judge(self, instruction: str, reference: str, reply: str) -> bool:
        payload = json.dumps({"instruction": instruction, "reference": reference, "reply": reply})
        try:
            proc = subprocess.run(
                self.command,
                shell=True,
                input=payload,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            log.warning("judge command timed out after %ss: %s", self.timeout, self.command)
            return False
        except OSError as exc:
            log.warning("judge command could not run: %s", exc)
            return False
        if proc.returncode != 0:
            log.warning("judge command exited %d: %s", proc.returncode, proc.stderr.strip()[:200])
            return False
        match = _VERDICT.match(proc.stdout.lstrip())
        if match is None:
            log.warning("judge command printed neither WIN nor LOSS: %r", proc.stdout[:80])
            return False
        return match.group(1) == "WIN"
