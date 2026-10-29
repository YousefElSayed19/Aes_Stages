from .gf256 import ginv
from .state import copy_state
from .utils import rotl8


def affine(b):
    return b ^ rotl8(b, 1) ^ rotl8(b, 2) ^ rotl8(b, 3) ^ rotl8(b, 4) ^ 0x63


def inv_affine(y):
    return rotl8(y, 1) ^ rotl8(y, 3) ^ rotl8(y, 6) ^ 0x05


SBOX = [affine(ginv(x)) for x in range(256)]
INV_SBOX = [0] * 256
for _x, _y in enumerate(SBOX):
    INV_SBOX[_y] = _x


def sub_bytes(state):
    out = copy_state(state)
    for r in range(4):
        for c in range(4):
            out[r][c] = SBOX[state[r][c]]
    return out


def inv_sub_bytes(state):
    out = copy_state(state)
    for r in range(4):
        for c in range(4):
            out[r][c] = INV_SBOX[state[r][c]]
    return out
