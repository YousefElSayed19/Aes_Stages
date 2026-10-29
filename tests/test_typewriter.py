import contextlib
import io
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from aes.cli import main
from aes.typewriter import LEVELS, ORDER, Typewriter


class FakeTty(io.StringIO):
    def isatty(self):
        return True


def write_with(typer, text, tty=True):
    stream = FakeTty() if tty else io.StringIO()
    with mock.patch("aes.typewriter.time.sleep") as sleep:
        with contextlib.redirect_stdout(stream):
            typer.write(text)
    return stream.getvalue(), sleep


def run_cli(inputs):
    out = io.StringIO()
    with mock.patch("builtins.input", side_effect=list(inputs) + ["0"]):
        with contextlib.redirect_stdout(out):
            main()
    return out.getvalue()


class TestTypewriter(unittest.TestCase):
    def test_types_every_visible_character_with_a_delay(self):
        text = "ab cd\nef"
        written, sleep = write_with(Typewriter("normal"), text)
        self.assertEqual(written, text)
        self.assertEqual(sleep.call_count, 6)
        sleep.assert_called_with(LEVELS["normal"])

    def test_no_delay_when_output_is_not_a_terminal(self):
        written, sleep = write_with(Typewriter("slow"), "hello", tty=False)
        self.assertEqual(written, "hello")
        sleep.assert_not_called()

    def test_off_level_has_no_delay(self):
        written, sleep = write_with(Typewriter("off"), "hello")
        self.assertEqual(written, "hello")
        sleep.assert_not_called()

    def test_ctrl_c_shows_the_rest_instantly(self):
        typer = Typewriter("normal")
        stream = FakeTty()
        with mock.patch("aes.typewriter.time.sleep", side_effect=[None, KeyboardInterrupt]) as sleep:
            with contextlib.redirect_stdout(stream):
                typer.write("abcdef")
                typer.write("ghi")
        self.assertEqual(stream.getvalue(), "abcdefghi")
        self.assertTrue(typer.skip)
        self.assertEqual(sleep.call_count, 2)

    def test_cycle_goes_through_every_level(self):
        typer = Typewriter("slow")
        seen = [typer.cycle() for _ in ORDER]
        self.assertEqual(seen, ["normal", "fast", "off", "slow"])

    def test_reset_restores_defaults(self):
        typer = Typewriter("off")
        typer.skip = True
        typer.reset()
        self.assertEqual(typer.level, "normal")
        self.assertFalse(typer.skip)


class TestSpeedMenu(unittest.TestCase):
    def test_s_cycles_the_speed(self):
        out = run_cli(["s", "s"])
        self.assertIn("Typing speed is now: fast.", out)
        self.assertIn("Typing speed is now: off.", out)

    def test_speed_is_reset_for_a_new_session(self):
        run_cli(["s"])
        out = run_cli([])
        self.assertIn("Typing speed: normal", out)

    def test_results_are_still_correct_with_typing_enabled(self):
        stream = FakeTty()
        with mock.patch("aes.typewriter.time.sleep"):
            with mock.patch("builtins.input", side_effect=["13", "Hello AES", "0"]):
                with contextlib.redirect_stdout(stream):
                    main()
        self.assertIn("Round trip OK", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
