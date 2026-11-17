import contextlib
import io
import json
import shlex
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ifbot import cli


def run(argv, stdin=None):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        if stdin is not None:
            with mock.patch.object(sys, "stdin", io.StringIO(stdin)):
                code = cli.main(argv)
        else:
            code = cli.main(argv)
    return code, out.getvalue(), err.getvalue()


class CliTests(unittest.TestCase):
    def test_prompt(self):
        code, out, _ = run(["-p", "hi, i'm Sam"])
        self.assertEqual(code, 0)
        self.assertIn("Sam", out)

    def test_verbose_reports_module_on_stderr(self):
        _, out, err = run(["-v", "-p", "hello"])
        self.assertIn("greeting", err)
        self.assertIn("ms", err)
        self.assertNotIn("greeting", out)

    def test_piped_stdin_one_reply_per_line(self):
        code, out, _ = run([], stdin="hello\nmy name is Kim\nwhat is my name\n")
        self.assertEqual(code, 0)
        lines = out.strip().splitlines()
        self.assertEqual(len(lines), 3)
        self.assertIn("Kim", lines[2])

    def test_eval_json(self):
        code, out, _ = run(["eval", "--split", "dev", "--json"])
        data = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(data["total"], 40)
        self.assertEqual(data["split"], "dev")
        self.assertEqual(data["wins"] + len(data["failures"]), 40)

    def test_eval_command_judge(self):
        cmd = "%s -c %s" % (shlex.quote(sys.executable), shlex.quote("print('WIN')"))
        code, out, _ = run(["eval", "--split", "heldout", "--json", "--judge", "command", "--judge-cmd", cmd])
        self.assertEqual(json.loads(out)["win_rate"], 1.0)

    def test_eval_text_output(self):
        _, out, _ = run(["eval", "--split", "heldout"])
        self.assertIn("win rate:", out)
        self.assertIn("overlap", out)

    def test_evolve_log_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, _ = run(["--root", tmp, "evolve", "log"])
        self.assertEqual(code, 0)
        self.assertIn("empty", out)

    def test_evolve_new_prints_workspace(self):
        code, out, _ = run(["evolve", "new"])
        path = Path(out.strip())
        self.assertTrue((path / "BRIEF.md").is_file())
        self.assertFalse((path / "data" / "heldout.jsonl").exists())
        import shutil

        shutil.rmtree(str(path))


if __name__ == "__main__":
    unittest.main()
