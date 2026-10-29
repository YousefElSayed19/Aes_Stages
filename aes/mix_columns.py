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
    return _mix(state, MIX_MATRIX)


def inv_mix_columns(state):
    return _mix(state, INV_MIX_MATRIX)
