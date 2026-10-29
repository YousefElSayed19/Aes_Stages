import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from aes import pipeline
from aes.gf256 import ginv, gmul
from aes.mix_columns import inv_mix_columns, mix_columns
from aes.shift_rows import inv_shift_rows, shift_rows
from aes.state import hex_to_state, state_to_hex
from aes.sub_bytes import INV_SBOX, SBOX, inv_affine, inv_sub_bytes, sub_bytes
from aes.text_hex import hex_to_text, pad_pkcs7, text_to_hex, unpad_pkcs7

R1_START = "193de3bea0f4e22b9ac68d2ae9f84808"
R1_AFTER_SUB = "d42711aee0bf98f1b8b45de51e415230"
R1_AFTER_SHIFT = "d4bf5d30e0b452aeb84111f11e2798e5"
R1_AFTER_MIX = "046681e5e0cb199a48f8d37a2806264c"


class TestTextHex(unittest.TestCase):
    def test_text_to_hex(self):
        self.assertEqual(text_to_hex("Hi"), "4869")

    def test_roundtrip_unicode(self):
        for text in ["Hello AES", "café ✓", "mixed üñ 123"]:
            self.assertEqual(hex_to_text(text_to_hex(text)), text)

    def test_padding(self):
        for n in range(0, 40):
            data = bytes(range(n))
            padded = pad_pkcs7(data)
            self.assertEqual(len(padded) % 16, 0)
            self.assertEqual(unpad_pkcs7(padded), data)

    def test_bad_padding(self):
        with self.assertRaises(ValueError):
            unpad_pkcs7(b"\x00" * 16)


class TestState(unittest.TestCase):
    def test_column_major_layout(self):
        state = hex_to_state("000102030405060708090a0b0c0d0e0f")
        self.assertEqual(state[0], [0x00, 0x04, 0x08, 0x0C])
        self.assertEqual(state[1], [0x01, 0x05, 0x09, 0x0D])
        self.assertEqual(state[3], [0x03, 0x07, 0x0B, 0x0F])

    def test_roundtrip(self):
        h = "000102030405060708090a0b0c0d0e0f"
        self.assertEqual(state_to_hex(hex_to_state(h)), h)

    def test_wrong_length(self):
        with self.assertRaises(ValueError):
            hex_to_state("0011")

    def test_spaced_input(self):
        h = "19 3d e3 be a0 f4 e2 2b 9a c6 8d 2a e9 f8 48 08"
        self.assertEqual(state_to_hex(hex_to_state(h)), R1_START)


class TestSubBytes(unittest.TestCase):
    def test_known_sbox_values(self):
        self.assertEqual(SBOX[0x00], 0x63)
        self.assertEqual(SBOX[0x01], 0x7C)
        self.assertEqual(SBOX[0x53], 0xED)
        self.assertEqual(SBOX[0xFF], 0x16)

    def test_inverse_table(self):
        for i in range(256):
            self.assertEqual(INV_SBOX[SBOX[i]], i)

    def test_inverse_affine_formula(self):
        for x in range(256):
            self.assertEqual(ginv(inv_affine(SBOX[x])), x)

    def test_fips_vector(self):
        self.assertEqual(state_to_hex(sub_bytes(hex_to_state(R1_START))), R1_AFTER_SUB)

    def test_inverse(self):
        self.assertEqual(state_to_hex(inv_sub_bytes(hex_to_state(R1_AFTER_SUB))), R1_START)


class TestShiftRows(unittest.TestCase):
    def test_fips_vector(self):
        self.assertEqual(state_to_hex(shift_rows(hex_to_state(R1_AFTER_SUB))), R1_AFTER_SHIFT)

    def test_inverse(self):
        self.assertEqual(
            state_to_hex(inv_shift_rows(hex_to_state(R1_AFTER_SHIFT))), R1_AFTER_SUB
        )


class TestMixColumns(unittest.TestCase):
    def test_gmul_known(self):
        self.assertEqual(gmul(0x57, 0x83), 0xC1)
        self.assertEqual(gmul(0x57, 0x13), 0xFE)

    def test_fips_vector(self):
        self.assertEqual(state_to_hex(mix_columns(hex_to_state(R1_AFTER_SHIFT))), R1_AFTER_MIX)

    def test_known_column(self):
        out = mix_columns(hex_to_state("db135345" + "00" * 12))
        self.assertEqual([out[r][0] for r in range(4)], [0x8E, 0x4D, 0xA1, 0xBC])

    def test_inverse(self):
        self.assertEqual(
            state_to_hex(inv_mix_columns(hex_to_state(R1_AFTER_MIX))), R1_AFTER_SHIFT
        )


class TestInputsAreNotMutated(unittest.TestCase):
    def test_stages_return_new_state(self):
        original = hex_to_state(R1_START)
        snapshot = [row[:] for row in original]
        for func in (
            sub_bytes,
            shift_rows,
            mix_columns,
            inv_sub_bytes,
            inv_shift_rows,
            inv_mix_columns,
        ):
            func(original)
            self.assertEqual(original, snapshot)


class TestPipeline(unittest.TestCase):
    def test_single_block_matches_fips(self):
        state = hex_to_state(R1_START)
        state = mix_columns(shift_rows(sub_bytes(state)))
        self.assertEqual(state_to_hex(state), R1_AFTER_MIX)

    def test_round_trip_texts(self):
        texts = [
            "a",
            "Hello",
            "exactly16bytes!!",
            "A longer sentence than one block.",
            "café ✓",
            "",
            "x" * 100,
        ]
        for text in texts:
            result = pipeline.forward(text)
            back = pipeline.reverse(pipeline.ciphertext_hex(result))
            self.assertEqual(back["text"], text)

    def test_round_trip_random(self):
        rng = random.Random(1234)
        alphabet = "abcdefghijklmnopqrstuvwxyz ABCDEFG0123456789!@#"
        for _ in range(200):
            text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 60)))
            back = pipeline.reverse(pipeline.ciphertext_hex(pipeline.forward(text)))
            self.assertEqual(back["text"], text)

    def test_each_inverse_undoes_each_forward(self):
        rng = random.Random(99)
        for _ in range(200):
            h = bytes(rng.randrange(256) for _ in range(16)).hex()
            s = hex_to_state(h)
            self.assertEqual(inv_sub_bytes(sub_bytes(s)), s)
            self.assertEqual(inv_shift_rows(shift_rows(s)), s)
            self.assertEqual(inv_mix_columns(mix_columns(s)), s)


if __name__ == "__main__":
    unittest.main()
