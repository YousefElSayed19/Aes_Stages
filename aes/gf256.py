"""
gf256.py
--------
Arithmetic in the Galois Field GF(2^8) used by AES.

The field is defined by the irreducible polynomial:
    x^8 + x^4 + x^3 + x + 1   (0x11B)

Addition in GF(2^8) is simply XOR.
Multiplication is "shift and add" with reduction by 0x11B.
"""

IRREDUCIBLE_POLY = 0x11B


def xtime(a: int) -> int:
    """Multiply a byte by x (i.e. by 2) in GF(2^8)."""
    a <<= 1
    if a & 0x100:
        a ^= IRREDUCIBLE_POLY
    return a & 0xFF


def gmul(a: int, b: int) -> int:
    """Multiply two bytes in GF(2^8)."""
    result = 0
    for _ in range(8):
        if b & 1:
            result ^= a
        a = xtime(a)
        b >>= 1
    return result & 0xFF


def ginv(a: int) -> int:
    """Multiplicative inverse in GF(2^8). By AES convention, inverse of 0 is 0."""
    if a == 0:
        return 0
    for candidate in range(1, 256):
        if gmul(a, candidate) == 1:
            return candidate
    raise ValueError("no inverse found")  # unreachable for a valid field
