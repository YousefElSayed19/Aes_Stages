"""
pipeline.py
-----------
Chains all stages together.

Forward  : Text -> Hex -> (pad) -> State -> SubBytes -> ShiftRows -> MixColumns
Reverse  : InvMixColumns -> InvShiftRows -> InvSubBytes -> State -> Hex -> (unpad) -> Text

Both directions return a list of "steps" so a caller (the menu, the tests,
a future GUI) can show the Input/Output of every stage separately.
"""

from .mix_columns import inv_mix_columns, mix_columns
from .shift_rows import inv_shift_rows, shift_rows
from .state import hex_to_state, state_to_hex
from .sub_bytes import inv_sub_bytes, sub_bytes
from .text_hex import (
    hex_to_text,
    pad_pkcs7,
    split_blocks,
    text_to_hex,
    unpad_pkcs7,
)
from .utils import clean_hex


def forward(text: str) -> dict:
    """
    Run the forward chain on a text.
    Returns:
        {
          "hex":     hex of the original text,
          "padded":  hex after PKCS#7 padding,
          "blocks":  [ {"state_in", "after_sub", "after_shift", "after_mix"} ... ]
        }
    Each block entry holds States (4x4 lists) so they can be printed or reused.
    """
    hex_text = text_to_hex(text)
    padded = pad_pkcs7(bytes.fromhex(hex_text))
    blocks = []
    for block in split_blocks(padded):
        state = hex_to_state(block.hex())
        s1 = sub_bytes(state)
        s2 = shift_rows(s1)
        s3 = mix_columns(s2)
        blocks.append(
            {"state_in": state, "after_sub": s1, "after_shift": s2, "after_mix": s3}
        )
    return {"hex": hex_text, "padded": padded.hex(), "blocks": blocks}


def ciphertext_hex(result: dict) -> str:
    """Concatenate the final State (after MixColumns) of every block as hex."""
    return "".join(state_to_hex(b["after_mix"]) for b in result["blocks"])


def reverse(mixed_hex: str) -> dict:
    """
    Run the reverse chain on the hex produced by the forward chain
    (one or more 16-byte blocks, concatenated).
    Returns:
        {
          "blocks": [ {"state_in", "after_inv_mix", "after_inv_shift", "after_inv_sub"} ... ],
          "padded": hex after State -> Hex (still padded),
          "hex":    hex after removing padding,
          "text":   the recovered plain text
        }
    """
    data = bytes.fromhex(clean_hex(mixed_hex))
    blocks = []
    padded = b""
    for block in split_blocks(data):
        state = hex_to_state(block.hex())
        s1 = inv_mix_columns(state)
        s2 = inv_shift_rows(s1)
        s3 = inv_sub_bytes(s2)
        blocks.append(
            {
                "state_in": state,
                "after_inv_mix": s1,
                "after_inv_shift": s2,
                "after_inv_sub": s3,
            }
        )
        padded += bytes.fromhex(state_to_hex(s3))
    plain = unpad_pkcs7(padded)
    return {
        "blocks": blocks,
        "padded": padded.hex(),
        "hex": plain.hex(),
        "text": hex_to_text(plain.hex()),
    }
