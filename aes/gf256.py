IRREDUCIBLE_POLY = 0x11B


def xtime(a):
    a <<= 1
    if a & 0x100:
        a ^= IRREDUCIBLE_POLY
    return a & 0xFF


def gmul(a, b):
    result = 0
    for _ in range(8):
        if b & 1:
            result ^= a
        a = xtime(a)
        b >>= 1
    return result & 0xFF


def ginv(a):
    if a == 0:
        return 0
    for candidate in range(1, 256):
        if gmul(a, candidate) == 1:
            return candidate
    raise ValueError("No inverse found.")
