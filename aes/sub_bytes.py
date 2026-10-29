"""
sub_bytes.py
------------
Stage 3: SubBytes (Substitution) and InvSubBytes

Every byte of the State is replaced using the S-Box.

The S-Box is NOT hard-coded: it is generated from its definition
    1) take the multiplicative inverse of the byte in GF(2^8)
    2) apply the AES affine transformation
which avoids typos and shows where the table comes from.
"""

from .gf256 import ginv
from .state import copy_state


def _rotl8(x: int, n: int) -> int:
    return ((x << n) | (x >> (8 - n))) & 0xFF


def _build_sbox():
    sbox = []
    for a in range(256):
        b = ginv(a)
        # Affine transformation: b ^ rotl(b,1) ^ rotl(b,2) ^ rotl(b,3) ^ rotl(b,4) ^ 0x63
        s = b ^ _rotl8(b, 1) ^ _rotl8(b, 2) ^ _rotl8(b, 3) ^ _rotl8(b, 4) ^ 0x63
        sbox.append(s)
    return sbox


SBOX = _build_sbox()
INV_SBOX = [0] * 256
for _i, _v in enumerate(SBOX):
    INV_SBOX[_v] = _i


def sub_bytes(state):
    """Replace each byte by SBOX[byte]. Returns a new State."""
    out = copy_state(state)
    for r in range(4):
        for c in range(4):
            out[r][c] = SBOX[state[r][c]]
    return out


def inv_sub_bytes(state):
    """Replace each byte by INV_SBOX[byte]. Returns a new State."""
    out = copy_state(state)
    for r in range(4):
        for c in range(4):
            out[r][c] = INV_SBOX[state[r][c]]
    return out
