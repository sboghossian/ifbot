import shlex
import sys
import unittest

from ifbot.evals.judge import CommandJudge, OverlapJudge, token_f1


def py(code):
    return "%s -c %s" % (shlex.quote(sys.executable), shlex.quote(code))


class OverlapJudgeTests(unittest.TestCase):
    def test_identical_text_wins(self):
        self.assertTrue(OverlapJudge().judge("q", "Water boils at 100 degrees.", "water boils at 100 degrees"))

    def test_disjoint_text_loses(self):
        self.assertFalse(OverlapJudge().judge("q", "alpha beta gamma", "delta epsilon"))

    def test_empty_reply_loses(self):
        self.assertFalse(OverlapJudge().judge("q", "alpha beta", ""))
        self.assertEqual(token_f1("alpha", ""), 0.0)

    def test_f1_value(self):
        # reference 4 tokens, reply 2 tokens, 2 shared: P=1, R=0.5, F1=2/3
        self.assertAlmostEqual(token_f1("a b c d", "a b"), 2.0 / 3.0)

    def test_threshold_is_inclusive_and_configurable(self):
        ref, rep = "a b c d", "a b"
        self.assertTrue(OverlapJudge(threshold=0.6).judge("q", ref, rep))
        self.assertFalse(OverlapJudge(threshold=0.7).judge("q", ref, rep))
        self.assertTrue(OverlapJudge(threshold=2.0 / 3.0).judge("q", ref, rep))

    def test_default_threshold(self):
        self.assertEqual(OverlapJudge().threshold, 0.35)

    def test_repeated_words_are_not_double_counted(self):
        self.assertLess(token_f1("the cat", "the the the the"), 0.5)


class CommandJudgeTests(unittest.TestCase):
    def test_win(self):
        self.assertTrue(CommandJudge(py("print('WIN')")).judge("q", "r", "a"))

    def test_loss(self):
        self.assertFalse(CommandJudge(py("print('LOSS')")).judge("q", "r", "a"))

    def test_win_followed_by_explanation(self):
        self.assertTrue(CommandJudge(py("print('WIN - it answers the question')")).judge("q", "r", "a"))

    def test_receives_json_on_stdin(self):
        code = (
            "import json,sys; d=json.load(sys.stdin); "
            "print('WIN' if d['reply']=='ok' and d['reference']=='ref' and d['instruction']=='ask' else 'LOSS')"
        )
        judge = CommandJudge(py(code))
        self.assertTrue(judge.judge("ask", "ref", "ok"))
        self.assertFalse(judge.judge("ask", "ref", "nope"))

    def test_garbage_output_is_a_loss_and_logged(self):
        with self.assertLogs("ifbot.judge", level="WARNING"):
            self.assertFalse(CommandJudge(py("print('maybe')")).judge("q", "r", "a"))

    def test_word_that_only_starts_with_win_is_garbage(self):
        with self.assertLogs("ifbot.judge", level="WARNING"):
            self.assertFalse(CommandJudge(py("print('WINDOW')")).judge("q", "r", "a"))

    def test_empty_output_is_a_loss(self):
        with self.assertLogs("ifbot.judge", level="WARNING"):
            self.assertFalse(CommandJudge(py("pass")).judge("q", "r", "a"))

    def test_non_zero_exit_is_a_loss_even_if_it_printed_win(self):
        with self.assertLogs("ifbot.judge", level="WARNING"):
            self.assertFalse(CommandJudge(py("print('WIN'); raise SystemExit(3)")).judge("q", "r", "a"))

    def test_timeout_is_a_loss_and_logged(self):
        judge = CommandJudge(py("import time; time.sleep(10); print('WIN')"), timeout=0.5)
        with self.assertLogs("ifbot.judge", level="WARNING"):
            self.assertFalse(judge.judge("q", "r", "a"))

    def test_empty_command_rejected(self):
        with self.assertRaises(ValueError):
            CommandJudge("   ")


if __name__ == "__main__":
    unittest.main()
