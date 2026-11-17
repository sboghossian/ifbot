"""Load benchmark rows from JSONL: {id, instruction, output, category}."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set, Union

REQUIRED = ("id", "instruction", "output", "category")


class DatasetError(ValueError):
    """The file is missing, empty, or has a malformed row."""


@dataclass(frozen=True)
class Row:
    id: str
    instruction: str
    output: str
    category: str


def load_rows(path: Union[str, Path]) -> List[Row]:
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise DatasetError("cannot read %s: %s" % (p, exc))
    rows = []  # type: List[Row]
    seen = set()  # type: Set[str]
    for lineno, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DatasetError("%s line %d: invalid JSON (%s)" % (p.name, lineno, exc.msg))
        if not isinstance(obj, dict):
            raise DatasetError("%s line %d: expected a JSON object" % (p.name, lineno))
        for key in REQUIRED:
            value = obj.get(key)
            if not isinstance(value, str) or not value.strip():
                raise DatasetError("%s line %d: missing or empty field %r" % (p.name, lineno, key))
        if obj["id"] in seen:
            raise DatasetError("%s line %d: duplicate id %r" % (p.name, lineno, obj["id"]))
        seen.add(obj["id"])
        rows.append(Row(obj["id"], obj["instruction"], obj["output"], obj["category"]))
    if not rows:
        raise DatasetError("%s has no rows" % p.name)
    return rows
