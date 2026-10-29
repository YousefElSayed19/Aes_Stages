"""
mix_columns.py
--------------
Stage 5: MixColumns and InvMixColumns

Each column of the State is multiplied (in GF(2^8)) by a fixed matrix.

MixColumns matrix:            InvMixColumns matrix:
    | 02 03 01 01 |               | 0e 0b 0d 09 |
    | 01 02 03 01 |               | 09 0e 0b 0d |
    | 01 01 02 03 |               | 0d 09 0e 0b |
    | 03 01 01 02 |               | 0b 0d 09 0e |

"Addition" inside the matrix product is XOR.
"""

from .gf256 import gmul
from .state import copy_state

MIX_MATRIX = [
    [0x02, 0x03, 0x01, 0x01],
    [0x01, 0x02, 0x03, 0x01],
    [0x01, 0x01, 0x02, 0x03],
    [0x03, 0x01, 0x01, 0x02],
]

INV_MIX_MATRIX = [
    [0x0E, 0x0B, 0x0D, 0x09],
    [0x09, 0x0E, 0x0B, 0x0D],
    [0x0D, 0x09, 0x0E, 0x0B],
    [0x0B, 0x0D, 0x09, 0x0E],
]


def _mix(state, matrix):
    out = copy_state(state)
    for c in range(4):
        column = [state[r][c] for r in range(4)]
        for r in range(4):
            value = 0
            for k in range(4):
                value ^= gmul(matrix[r][k], column[k])
            out[r][c] = value
    return out


def mix_columns(state):
    """Multiply every column by MIX_MATRIX. Returns a new State."""
    return _mix(state, MIX_MATRIX)


def inv_mix_columns(state):
    """Multiply every column by INV_MIX_MATRIX. Returns a new State."""
    return _mix(state, INV_MIX_MATRIX)
