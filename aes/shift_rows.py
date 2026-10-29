from .state import copy_state


def shift_rows(state):
    out = copy_state(state)
    for r in range(4):
        out[r] = state[r][r:] + state[r][:r]
    return out


def inv_shift_rows(state):
    out = copy_state(state)
    for r in range(1, 4):
        out[r] = state[r][-r:] + state[r][:-r]
    return out
