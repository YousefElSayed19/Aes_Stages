"""
state.py
--------
Stage 2: Hex <-> State

The AES State is a 4x4 matrix of bytes filled COLUMN by COLUMN
(not row by row). For the 16 input bytes b0 ... b15:

    | b0  b4  b8   b12 |
    | b1  b5  b9   b13 |
    | b2  b6  b10  b14 |
    | b3  b7  b11  b15 |

So state[row][col] = bytes[row + 4 * col].
"""

from .utils import BLOCK_SIZE, clean_hex


def hex_to_state(hex_str: str):
    """16 bytes (32 hex digits) -> 4x4 State (list of 4 rows)."""
    data = bytes.fromhex(clean_hex(hex_str))
    if len(data) != BLOCK_SIZE:
        raise ValueError(
            f"a State needs exactly 16 bytes (32 hex digits), got {len(data)} bytes"
        )
    return [[data[row + 4 * col] for col in range(4)] for row in range(4)]


def state_to_hex(state) -> str:
    """4x4 State -> 32 hex digits (column by column)."""
    return "".join(f"{state[row][col]:02x}" for col in range(4) for row in range(4))


def copy_state(state):
    """Deep copy of a State so stages never modify their input."""
    return [row[:] for row in state]
