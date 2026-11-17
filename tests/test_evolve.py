"""Gate, workspace, ledger and loop. Everything runs on a temp copy of the project."""

import hashlib
import os
import re
import shutil
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from ifbot.evals.dataset import load_rows
from ifbot.evolve import gate, loop
from ifbot.evolve.ledger import Ledger, format_table
from ifbot.evolve.workspace import new_workspace
from ifbot.paths import DEFAULT_ROOT, bot_dir, data_path, ledger_path

IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "runs")

# The improving candidate answers a made-up held-out question that setUp adds to the
# temp project, so these tests do not depend on what the live bot already knows.
FIXTURE_ROW = (
    '{"id": "held-fixture", "category": "science", '
    '"instruction": "What colour is a ripe zorblat fruit?", '
    '"output": "A ripe zorblat fruit is bright teal in colour."}'
)

IMPROVER = '''
from ..arbiter import Proposal


def propose(ctx):
    if "zorblat" in set(ctx.tokens):
        return Proposal("A zorblat fruit is teal in colour when it is ripe.", 0.95)
    return None
'''


def norm(s):
    return " ".join(re.findall(r"[a-z0-9]+", s.lower()))


def tree_hash(path):
    h = hashlib.sha1()
    for p in sorted(Path(path).rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            h.update(str(p.relative_to(path)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


class EvolveCase(unittest.TestCase):
    TIMEOUT = 20.0

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.root = self.tmp / "proj"
        for name in ("ifbot", "data", "tests"):
            shutil.copytree(str(DEFAULT_ROOT / name), str(self.root / name), ignore=IGNORE)
        with open(str(data_path(self.root, "heldout")), "a", encoding="utf-8") as f:
            f.write(FIXTURE_ROW + "\n")
        self._n = 0

    def workspace(self):
        self._n += 1
        return new_workspace(self.root, dest=self.tmp / ("ws%d" % self._n))

    def write(self, ws, rel, text):
        p = ws / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(textwrap.dedent(text), encoding="utf-8")

    def submit(self, ws, timeout=None):
        return gate.submit(ws, root=self.root, timeout=timeout or self.TIMEOUT)

    def ledger(self):
        return Ledger(ledger_path(self.root)).rows()


class WorkspaceTests(EvolveCase):
    def test_contains_no_heldout_content(self):
        ws = self.workspace()
        held = load_rows(data_path(self.root, "heldout"))
        files = [p for p in ws.rglob("*") if p.is_file()]
        self.assertTrue(files)
        for p in files:
            self.assertNotIn("heldout", p.name)
            text = norm(p.read_bytes().decode("utf-8", "ignore"))
            for row in held:
                # Generic pleasantries ("nice to meet you") legitimately exist in the seed bot.
                if row.category != "smalltalk" or len(norm(row.instruction).split()) >= 5:
                    self.assertNotIn(norm(row.instruction), text, p)
                self.assertNotIn(norm(row.output), text, p)
                self.assertNotIn(row.id, p.read_bytes().decode("utf-8", "ignore"))

    def test_has_what_a_proposer_needs(self):
        ws = self.workspace()
        for rel in ("bot/__init__.py", "tests/botload.py", "tests/test_bot_basic.py", "data/dev.jsonl", "BRIEF.md"):
            self.assertTrue((ws / rel).is_file(), rel)
        self.assertIn("won", (ws / "BRIEF.md").read_text())
        self.assertFalse((ws / "tests" / "test_evolve.py").exists())

    def test_workspace_tests_pass_out_of_the_box(self):
        ws = self.workspace()
        import subprocess

        proc = subprocess.run(
            [sys.executable, "-I", "-m", "unittest", "discover", "-s", "tests", "-p", "test_bot_*.py"],
            cwd=str(ws), capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)


class GateTests(EvolveCase):
    def test_seed_bot_passes_validation(self):
        self.assertIsNone(gate.validate(self.workspace(), self.root))

    def test_first_submit_records_baseline(self):
        res = self.submit(self.workspace())
        rows = self.ledger()
        self.assertEqual(rows[0]["candidate"], "baseline")
        self.assertTrue(rows[0]["accepted"])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["candidate"], res.candidate)

    def test_improving_candidate_is_accepted_and_installed(self):
        ws = self.workspace()
        self.write(ws, "bot/modules/science_extra.py", IMPROVER)
        res = self.submit(ws)
        self.assertTrue(res.accepted, res.reason)
        self.assertTrue(res.tests_passed)
        self.assertGreater(res.heldout_win_rate, self.ledger()[0]["heldout_win_rate"])
        self.assertTrue((bot_dir(self.root) / "modules" / "science_extra.py").is_file())
        self.assertEqual(tree_hash(bot_dir(self.root)), tree_hash(ws / "bot"))
        # a second identical submit is no longer an improvement
        again = self.submit(self.workspace())
        self.assertFalse(again.accepted)

    def test_equal_candidate_is_rejected(self):
        ws = self.workspace()
        before = tree_hash(bot_dir(self.root))
        self.write(ws, "bot/modules/noop.py", "def propose(ctx):\n    return None\n")
        res = self.submit(ws)
        self.assertFalse(res.accepted)
        self.assertIn("does not beat", res.reason)
        self.assertEqual(tree_hash(bot_dir(self.root)), before)
        self.assertFalse((bot_dir(self.root) / "modules" / "noop.py").exists())

    def test_regressing_candidate_is_rejected(self):
        ws = self.workspace()
        before = tree_hash(bot_dir(self.root))
        self.write(
            ws, "bot/modules/hijack.py",
            'from ..arbiter import Proposal\n\n\ndef propose(ctx):\n'
            '    return Proposal("Okay.", 1.0) if "morning" in ctx.tokens else None\n',
        )
        res = self.submit(ws)
        self.assertFalse(res.accepted)
        self.assertTrue(res.tests_passed)
        self.assertLess(res.heldout_win_rate, self.ledger()[0]["heldout_win_rate"])
        self.assertEqual(tree_hash(bot_dir(self.root)), before)

    def test_failing_tests_are_rejected_even_if_score_improves(self):
        ws = self.workspace()
        self.write(ws, "bot/modules/science_extra.py", IMPROVER)
        arith = ws / "bot" / "modules" / "arithmetic.py"
        arith.write_text(arith.read_text().replace("ast.Mult: operator.mul", "ast.Mult: operator.add"))
        before = tree_hash(bot_dir(self.root))
        res = self.submit(ws)
        self.assertFalse(res.accepted)
        self.assertFalse(res.tests_passed)
        self.assertTrue(res.reason.startswith("tests failed"))
        self.assertEqual(tree_hash(bot_dir(self.root)), before)

    def test_forbidden_code_is_rejected(self):
        cases = {
            "import subprocess": "subprocess",
            "import socket": "socket",
            "import urllib.request": "urllib",
            "from http import client": "http",
            "import requests": "outside the standard library",
            "import os\nos.system('echo hi')": "os.system",
            "from os import system": "os.system",
            "x = eval('1+1')": "eval",
            "exec('pass')": "exec",
            "import importlib": "engine.py",
            "from ... import x": "escapes",
        }
        for code, expected in cases.items():
            with self.subTest(code=code):
                ws = self.workspace()
                self.write(ws, "bot/modules/bad.py", code + "\n\ndef propose(ctx):\n    return None\n")
                res = self.submit(ws)
                self.assertFalse(res.accepted)
                self.assertIn(expected, res.reason)
                self.assertTrue(res.reason.startswith("invalid"))

    def test_heldout_text_in_source_is_rejected(self):
        held = load_rows(data_path(self.root, "heldout"))
        question = next(r for r in held if r.id == "held-021")
        variants = {
            "string": 'Q = %r\n' % question.instruction,
            "comment": "# %s\n" % question.instruction.lower(),
            "split literal": 'Q = "Why is the " "sky blue?"\n',
            "reference": 'A = %r\n' % question.output,
        }
        for label, code in variants.items():
            with self.subTest(label=label):
                ws = self.workspace()
                self.write(ws, "bot/modules/leak.py", code + "\ndef propose(ctx):\n    return None\n")
                res = self.submit(ws)
                self.assertFalse(res.accepted)
                self.assertIn("held-out", res.reason)

    def test_files_outside_bot_are_rejected(self):
        ws = self.workspace()
        self.write(ws, "extra.py", "x = 1\n")
        res = self.submit(ws)
        self.assertFalse(res.accepted)
        self.assertIn("outside bot/", res.reason)

        ws = self.workspace()
        t = ws / "tests" / "test_bot_basic.py"
        t.write_text("import unittest\n")
        res = self.submit(ws)
        self.assertFalse(res.accepted)
        self.assertIn("outside bot/", res.reason)

        ws = self.workspace()
        self.write(ws, "tests/test_new.py", "x = 1\n")
        self.assertIn("outside bot/", self.submit(ws).reason)

    def test_symlink_is_rejected(self):
        ws = self.workspace()
        os.symlink(str(data_path(self.root, "heldout")), str(ws / "bot" / "peek.txt"))
        res = self.submit(ws)
        self.assertFalse(res.accepted)
        self.assertIn("symlink", res.reason)

    def test_hanging_at_import_is_rejected_by_timeout(self):
        ws = self.workspace()
        self.write(ws, "bot/modules/hang.py", "while True:\n    pass\n")
        before = tree_hash(bot_dir(self.root))
        res = self.submit(ws, timeout=4)
        self.assertFalse(res.accepted)
        self.assertIn("timed out", res.reason)
        self.assertEqual(tree_hash(bot_dir(self.root)), before)

    def test_hanging_on_a_question_is_rejected_by_timeout(self):
        ws = self.workspace()
        self.write(
            ws, "bot/modules/hang.py",
            'def propose(ctx):\n    while "sky" in ctx.tokens:\n        pass\n    return None\n',
        )
        res = self.submit(ws, timeout=4)
        self.assertFalse(res.accepted)
        self.assertTrue(res.tests_passed)
        self.assertIn("timed out", res.reason)

    def test_crashing_bot_is_rejected(self):
        ws = self.workspace()
        self.write(ws, "bot/modules/boom.py", "raise RuntimeError('no')\n")
        res = self.submit(ws)
        self.assertFalse(res.accepted)  # import failure is logged by the engine, score cannot improve

    def test_missing_bot_dir_is_rejected(self):
        ws = self.workspace()
        shutil.rmtree(str(ws / "bot"))
        res = self.submit(ws)
        self.assertFalse(res.accepted)
        self.assertIn("no bot/", res.reason)

    def test_every_submission_is_in_the_ledger(self):
        for _ in range(2):
            self.submit(self.workspace())
        self.assertEqual(len(self.ledger()), 3)
        for row in self.ledger():
            self.assertEqual(
                set(row), {"ts", "candidate", "tests_passed", "dev_win_rate", "heldout_win_rate", "accepted", "reason", "bot_lines"}
            )


class LedgerTests(EvolveCase):
    def test_best_and_table(self):
        led = Ledger(ledger_path(self.root))
        self.assertIsNone(led.best())
        led.append({"candidate": "a", "accepted": True, "heldout_win_rate": 0.2, "tests_passed": True, "reason": "x"})
        led.append({"candidate": "b", "accepted": False, "heldout_win_rate": 0.9, "tests_passed": True, "reason": "y"})
        led.append({"candidate": "c", "accepted": True, "heldout_win_rate": 0.3, "tests_passed": False, "reason": "z"})
        self.assertEqual(led.best(), 0.3)
        table = format_table(led.rows())
        self.assertIn("candidate", table)
        self.assertEqual(len(table.splitlines()), 4)

    def test_unreadable_line_is_skipped(self):
        led = Ledger(ledger_path(self.root))
        led.append({"candidate": "a", "accepted": True, "heldout_win_rate": 0.1})
        with open(str(led.path), "a") as fh:
            fh.write("{broken\n")
        self.assertEqual(len(led.rows()), 1)


class LoopTests(EvolveCase):
    def proposer(self, body):
        script = self.tmp / "proposer.py"
        script.write_text(textwrap.dedent(body), encoding="utf-8")
        return "%s %s" % (sys.executable, script)

    def test_round_with_improving_proposer(self):
        cmd = self.proposer(
            '''
            import os, pathlib
            ws = pathlib.Path(os.environ["IFBOT_WORKSPACE"])
            assert pathlib.Path.cwd().resolve() == ws.resolve()
            (ws / "bot" / "modules" / "science_extra.py").write_text(%r)
            '''
            % IMPROVER
        )
        results = loop.run(1, cmd, root=self.root, timeout=self.TIMEOUT)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].accepted, results[0].reason)
        self.assertTrue((bot_dir(self.root) / "modules" / "science_extra.py").is_file())

    def test_failing_proposer_is_recorded_and_bot_untouched(self):
        before = tree_hash(bot_dir(self.root))
        results = loop.run(2, self.proposer("raise SystemExit(3)\n"), root=self.root, timeout=self.TIMEOUT)
        self.assertEqual([r.accepted for r in results], [False, False])
        self.assertIn("exited 3", results[0].reason)
        self.assertEqual(tree_hash(bot_dir(self.root)), before)
        self.assertEqual(len(self.ledger()), 2)


if __name__ == "__main__":
    unittest.main()
