"""Behaviour any version of the bot must keep. The evolve gate runs these against every candidate."""

import time
import unittest

from botload import new_bot


class GreetingTests(unittest.TestCase):
    def test_greets_back(self):
        reply = new_bot().respond("hello")
        self.assertTrue("hello" in reply.text.lower() or "hi" in reply.text.lower())

    def test_greeting_with_typo(self):
        reply = new_bot().respond("helo")
        self.assertTrue("hello" in reply.text.lower() or "hi" in reply.text.lower())

    def test_greeting_with_name_uses_name(self):
        reply = new_bot().respond("hi, i'm Sam")
        self.assertIn("Sam", reply.text)


class NameTests(unittest.TestCase):
    def test_remembers_name_across_turns(self):
        bot = new_bot()
        bot.respond("my name is Alex")
        self.assertIn("Alex", bot.respond("what's my name?").text)

    def test_unknown_name_is_not_invented(self):
        reply = new_bot().respond("what is my name")
        self.assertNotIn("Alex", reply.text)
        self.assertIn("don't know", reply.text.lower())

    def test_reset_forgets_name(self):
        bot = new_bot()
        bot.respond("I'm Riley")
        bot.reset()
        self.assertNotIn("Riley", bot.respond("what is my name").text)

    def test_feelings_are_not_names(self):
        bot = new_bot()
        bot.respond("I'm tired")
        self.assertNotIn("Tired", bot.respond("what is my name").text)


class ArithmeticTests(unittest.TestCase):
    def test_multiplication(self):
        self.assertIn("84", new_bot().respond("what is 12 * 7").text)

    def test_words_and_precedence(self):
        self.assertIn("14", new_bot().respond("calculate 2 + 3 * 4").text)
        self.assertIn("7", new_bot().respond("3 plus 4").text)

    def test_decimal_result(self):
        self.assertIn("2.5", new_bot().respond("10 / 4").text)

    def test_divide_by_zero(self):
        reply = new_bot().respond("what is 5 / 0")
        self.assertIn("zero", reply.text.lower())

    def test_malformed_input_does_not_crash(self):
        for message in ("what is 5 +", "( 3 + ", "* 4", "2 ** ** 3", "1 / / 2"):
            with self.subTest(message=message):
                reply = new_bot().respond(message)
                self.assertTrue(reply.text.strip())

    def test_code_is_never_executed(self):
        for message in ("__import__('os').system('echo pwned')", "9 + __import__('os').getcwd()"):
            with self.subTest(message=message):
                reply = new_bot().respond(message)
                self.assertNotIn("pwned", reply.text)

    def test_huge_power_is_refused_quickly(self):
        start = time.time()
        reply = new_bot().respond("what is 9 ** 9 ** 9")
        self.assertLess(time.time() - start, 2.0)
        self.assertTrue(reply.text.strip())


class RobustnessTests(unittest.TestCase):
    def test_empty_and_whitespace(self):
        bot = new_bot()
        for message in ("", "   ", "\n\t"):
            with self.subTest(message=message):
                self.assertTrue(bot.respond(message).text.strip())

    def test_fallback_on_gibberish(self):
        reply = new_bot().respond("qwertyuiop zxcvbnm asdfgh")
        self.assertTrue(reply.text.strip())

    def test_very_long_message(self):
        self.assertTrue(new_bot().respond("word " * 5000).text.strip())

    def test_reply_shape(self):
        reply = new_bot().respond("hello")
        self.assertIsInstance(reply.text, str)
        self.assertIsInstance(reply.module, str)
        self.assertTrue(0.0 <= reply.confidence <= 1.0)

    def test_same_seed_same_conversation(self):
        script = ["hello", "what is 2 + 2", "tell me something odd", "hi again", "bye"]
        first = [new_bot(seed=7).respond(m).text for m in script]
        second = [new_bot(seed=7).respond(m).text for m in script]
        self.assertEqual(first, second)

    def test_one_bot_is_deterministic_across_reset(self):
        bot = new_bot(seed=3)
        a = [bot.respond(m).text for m in ("hello", "zzz", "hi")]
        bot.reset()
        b = [bot.respond(m).text for m in ("hello", "zzz", "hi")]
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
