from .mix_columns import inv_mix_columns, mix_columns
from .shift_rows import inv_shift_rows, shift_rows
from .state import hex_to_state, state_to_hex
from .sub_bytes import inv_sub_bytes, sub_bytes
from .text_hex import hex_to_text, pad_pkcs7, split_blocks, text_to_hex, unpad_pkcs7
from .utils import clean_hex


def forward(text):
    hex_text = text_to_hex(text)
    padded = pad_pkcs7(bytes.fromhex(hex_text))
    blocks = []
    for block in split_blocks(padded):
        state = hex_to_state(block.hex())
        after_sub = sub_bytes(state)
        after_shift = shift_rows(after_sub)
        after_mix = mix_columns(after_shift)
        blocks.append(
            {
                "state_in": state,
                "after_sub": after_sub,
                "after_shift": after_shift,
                "after_mix": after_mix,
            }
        )
    return {"hex": hex_text, "padded": padded.hex(), "blocks": blocks}


def ciphertext_hex(result):
    return "".join(state_to_hex(b["after_mix"]) for b in result["blocks"])


def reverse(mixed_hex):
    data = bytes.fromhex(clean_hex(mixed_hex))
    blocks = []
    padded = b""
    for block in split_blocks(data):
        state = hex_to_state(block.hex())
        after_inv_mix = inv_mix_columns(state)
        after_inv_shift = inv_shift_rows(after_inv_mix)
        after_inv_sub = inv_sub_bytes(after_inv_shift)
        blocks.append(
            {
                "state_in": state,
                "after_inv_mix": after_inv_mix,
                "after_inv_shift": after_inv_shift,
                "after_inv_sub": after_inv_sub,
            }
        )
        padded += bytes.fromhex(state_to_hex(after_inv_sub))
    plain = unpad_pkcs7(padded)
    return {
        "blocks": blocks,
        "padded": padded.hex(),
        "hex": plain.hex(),
        "text": hex_to_text(plain.hex()),
    }
