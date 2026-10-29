"""
shift_rows.py
-------------
Stage 4: ShiftRows and InvShiftRows

Row i of the State is rotated LEFT by i positions:
    row 0: no shift
    row 1: shift left by 1
    row 2: shift left by 2
    row 3: shift left by 3

The inverse rotates each row RIGHT by the same amounts.
"""

from .state import copy_state


def shift_rows(state):
    """Rotate row i left by i. Returns a new State."""
    out = copy_state(state)
    for r in range(4):
        out[r] = state[r][r:] + state[r][:r]
    return out


def inv_shift_rows(state):
    """Rotate row i right by i. Returns a new State."""
    out = copy_state(state)
    for r in range(4):
        out[r] = state[r][-r:] + state[r][:-r] if r else state[r][:]
    return out
