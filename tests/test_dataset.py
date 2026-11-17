import json
import tempfile
import unittest
from pathlib import Path

from ifbot.evals.dataset import DatasetError, load_rows
from ifbot.paths import DEFAULT_ROOT, data_path

GOOD = {"id": "a1", "instruction": "Q?", "output": "A.", "category": "misc"}


class DatasetTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "rows.jsonl"

    def write(self, text):
        self.path.write_text(text, encoding="utf-8")

    def test_loads_rows_and_skips_blank_lines(self):
        self.write(json.dumps(GOOD) + "\n\n" + json.dumps(dict(GOOD, id="a2")) + "\n")
        rows = load_rows(self.path)
        self.assertEqual([r.id for r in rows], ["a1", "a2"])
        self.assertEqual(rows[0].instruction, "Q?")

    def test_malformed_line_names_the_line(self):
        self.write(json.dumps(GOOD) + "\n{not json\n")
        with self.assertRaisesRegex(DatasetError, "line 2"):
            load_rows(self.path)

    def test_missing_field(self):
        for field in ("id", "instruction", "output", "category"):
            with self.subTest(field=field):
                row = dict(GOOD)
                del row[field]
                self.write(json.dumps(row) + "\n")
                with self.assertRaisesRegex(DatasetError, field):
                    load_rows(self.path)

    def test_empty_or_non_string_field(self):
        self.write(json.dumps(dict(GOOD, output="  ")) + "\n")
        with self.assertRaises(DatasetError):
            load_rows(self.path)
        self.write(json.dumps(dict(GOOD, id=5)) + "\n")
        with self.assertRaises(DatasetError):
            load_rows(self.path)

    def test_not_an_object(self):
        self.write("[1, 2]\n")
        with self.assertRaises(DatasetError):
            load_rows(self.path)

    def test_duplicate_id(self):
        self.write(json.dumps(GOOD) + "\n" + json.dumps(GOOD) + "\n")
        with self.assertRaisesRegex(DatasetError, "duplicate"):
            load_rows(self.path)

    def test_empty_file(self):
        self.write("")
        with self.assertRaisesRegex(DatasetError, "no rows"):
            load_rows(self.path)
        self.write("\n  \n")
        with self.assertRaises(DatasetError):
            load_rows(self.path)

    def test_missing_file(self):
        with self.assertRaises(DatasetError):
            load_rows(Path(self._tmp.name) / "nope.jsonl")


class ShippedDataTests(unittest.TestCase):
    def test_shipped_splits_are_valid_and_disjoint(self):
        dev = load_rows(data_path(DEFAULT_ROOT, "dev"))
        held = load_rows(data_path(DEFAULT_ROOT, "heldout"))
        self.assertGreaterEqual(len(dev), 40)
        self.assertGreaterEqual(len(held), 30)
        self.assertFalse({r.instruction.lower() for r in dev} & {r.instruction.lower() for r in held})
        self.assertFalse({r.id for r in dev} & {r.id for r in held})
        self.assertEqual({r.category for r in dev}, {r.category for r in held})


if __name__ == "__main__":
    unittest.main()
