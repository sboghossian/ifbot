"""Append-only record of every submission, accepted or not."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger("ifbot.ledger")

FIELDS = (
    "ts",
    "candidate",
    "tests_passed",
    "dev_win_rate",
    "heldout_win_rate",
    "accepted",
    "reason",
    "bot_lines",
)


class Ledger:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def append(self, row: Dict[str, Any]) -> Dict[str, Any]:
        full = {key: row.get(key) for key in FIELDS}
        if full["ts"] is None:
            full["ts"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(str(self.path), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(full) + "\n")
        return full

    def rows(self) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        out = []
        for lineno, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                log.warning("skipping unreadable ledger line %d in %s", lineno, self.path)
        return out

    def best(self) -> Optional[float]:
        """Highest held-out win rate among accepted rows, or None if nothing was accepted."""
        rates = [
            r["heldout_win_rate"]
            for r in self.rows()
            if r.get("accepted") and isinstance(r.get("heldout_win_rate"), (int, float))
        ]
        return max(rates) if rates else None


def _pct(value: Any) -> str:
    return "-" if value is None else "%.3f" % value


def format_table(rows: List[Dict[str, Any]]) -> str:
    header = ("#", "time", "candidate", "tests", "dev", "heldout", "kept", "best", "reason")
    lines = []
    best = None  # type: Optional[float]
    for i, r in enumerate(rows, start=1):
        rate = r.get("heldout_win_rate")
        if r.get("accepted") and isinstance(rate, (int, float)):
            best = rate if best is None else max(best, rate)
        lines.append(
            (
                str(i),
                str(r.get("ts", ""))[:19],
                str(r.get("candidate", "")),
                {True: "pass", False: "FAIL", None: "-"}[r.get("tests_passed")],
                _pct(r.get("dev_win_rate")),
                _pct(rate),
                "yes" if r.get("accepted") else "no",
                _pct(best),
                str(r.get("reason", ""))[:70],
            )
        )
    table = [header] + lines
    widths = [max(len(row[c]) for row in table) for c in range(len(header) - 1)]
    out = []
    for row in table:
        cells = [row[c].ljust(widths[c]) for c in range(len(header) - 1)] + [row[-1]]
        out.append("  ".join(cells).rstrip())
    return "\n".join(out)
