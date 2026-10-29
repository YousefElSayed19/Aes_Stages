import contextlib
import io
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from aes import pipeline
from aes.cli import main, parse_choice
from aes.explain import (
    explain_hex_to_state,
    explain_inv_mix_columns,
    explain_inv_sub_bytes,
    explain_mix_columns,
    explain_padding,
    explain_shift_rows,
    explain_sub_bytes,
)
from aes.mix_columns import mix_columns
from aes.state import hex_to_state

SAMPLE = "193de3bea0f4e22b9ac68d2ae9f84808"


def run_cli(inputs):
    out = io.StringIO()
    with mock.patch("builtins.input", side_effect=list(inputs) + ["0"]):
        with contextlib.redirect_stdout(out):
            main()
    return out.getvalue()


class TestParseChoice(unittest.TestCase):
    def test_plain_number(self):
        self.assertEqual(parse_choice("3"), ("3", "new"))

    def test_previous_flags(self):
        for raw in ["3 p", "3p", "3 prev", "3 previous", "3 last", "12 P"]:
            self.assertEqual(parse_choice(raw)[1], "prev")

    def test_new_flags(self):
        for raw in ["3 n", "3n", "3 new"]:
            self.assertEqual(parse_choice(raw)[1], "new")

    def test_invalid(self):
        for raw in ["abc", "3 x", "3 p p", ""]:
            with self.assertRaises(ValueError):
                parse_choice(raw)


class TestChaining(unittest.TestCase):
    def test_full_manual_chain_matches_pipeline(self):
        expected = pipeline.ciphertext_hex(pipeline.forward("helloworld"))
        out = run_cli(["1", "helloworld", "2 p", "3 p", "4 p", "5 p"])
        self.assertIn(f"Result: {expected}", out)

    def test_manual_chain_then_reverse_gives_text(self):
        mixed = pipeline.ciphertext_hex(pipeline.forward("helloworld"))
        out = run_cli(["12", mixed])
        self.assertIn("Text: helloworld", out)

    def test_previous_result_used_by_inverse_stage(self):
        out = run_cli(["3", SAMPLE, "9 p"])
        self.assertIn(f"Output hex: {SAMPLE}", out)

    def test_new_value_can_replace_previous(self):
        out = run_cli(["3", SAMPLE, "4 n", SAMPLE])
        self.assertNotIn("Using previous", out)
        self.assertIn(f"Input hex : {SAMPLE}", out.split("=== ShiftRows ===")[1])
        self.assertIn("Using previous", run_cli(["3", SAMPLE, "4 p"]))

    def test_typing_p_at_prompt_uses_previous(self):
        out = run_cli(["3", SAMPLE, "4", "p"])
        self.assertIn("Using previous result", out)

    def test_previous_without_history_is_an_error(self):
        out = run_cli(["3 p"])
        self.assertIn("There is no previous result yet", out)

    def test_previous_text_for_direct_solve(self):
        out = run_cli(["1", "abc", "6 p"])
        self.assertIn("Using previous text: abc", out)
        self.assertIn("Final hex after MixColumns", out)

    def test_round_trip_demo(self):
        out = run_cli(["13", "Hello AES"])
        self.assertIn("Round trip OK", out)

    def test_forward_stages_auto_pad(self):
        out = run_cli(["2", "68656c6c6f776f726c64"])
        self.assertIn("68656c6c6f776f726c64060606060606", out)

    def test_inverse_stage_rejects_wrong_length(self):
        out = run_cli(["9", "0011"])
        self.assertIn("needs a multiple of 16 bytes", out)

    def test_multi_block_input(self):
        out = run_cli(["3", SAMPLE + SAMPLE])
        self.assertIn("block 1 of 2", out)
        self.assertIn("block 2 of 2", out)

    def test_explanations_toggle(self):
        with_explain = run_cli(["6", "abc"])
        self.assertIn("How it works", with_explain)
        without = run_cli(["e", "6", "abc"])
        self.assertNotIn("How it works", without)
        self.assertIn("Final hex after MixColumns", without)

    def test_invalid_choice_does_not_crash(self):
        out = run_cli(["99", "zzz"])
        self.assertIn("Error", out)


class TestExplanations(unittest.TestCase):
    def setUp(self):
        self.state = hex_to_state(SAMPLE)

    def test_sub_bytes_explanation_has_every_byte(self):
        lines = explain_sub_bytes(self.state)
        self.assertEqual(len([l for l in lines if "-> S(x)=" in l]), 16)

    def test_inv_sub_bytes_explanation_has_every_byte(self):
        lines = explain_inv_sub_bytes(self.state)
        self.assertEqual(len([l for l in lines if "-> x=" in l]), 16)

    def test_shift_rows_explanation_has_four_rows(self):
        lines = explain_shift_rows(self.state)
        self.assertEqual(len([l for l in lines if l.strip().startswith("row")]), 4)

    def test_mix_columns_explanation_matches_result(self):
        mixed = mix_columns(self.state)
        text = "\n".join(explain_mix_columns(self.state))
        for r in range(4):
            for c in range(4):
                self.assertIn(f"= {mixed[r][c]:02x}", text)

    def test_inv_mix_columns_explanation_mentions_matrix(self):
        text = "\n".join(explain_inv_mix_columns(self.state))
        self.assertIn("0e", text)

    def test_padding_explanation(self):
        text = "\n".join(explain_padding(10))
        self.assertIn("= 6", text)
        self.assertIn("06", text)

    def test_hex_to_state_explanation(self):
        lines = explain_hex_to_state(bytes.fromhex(SAMPLE))
        self.assertEqual(len([l for l in lines if "<- bytes" in l]), 4)


if __name__ == "__main__":
    unittest.main()
