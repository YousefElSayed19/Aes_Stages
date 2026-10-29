import re

BLOCK_SIZE = 16


def clean_hex(hex_str):
    s = hex_str.strip().lower()
    s = re.sub(r"0x", "", s)
    s = re.sub(r"[\s,:\-]", "", s)
    if not s:
        raise ValueError("Empty hex input.")
    if len(s) % 2 != 0:
        raise ValueError("Hex input must have an even number of digits.")
    if not re.fullmatch(r"[0-9a-f]+", s):
        raise ValueError("Hex input contains non-hex characters.")
    return s


def rotl8(x, n):
    return ((x << n) | (x >> (8 - n))) & 0xFF


def bytes_to_spaced_hex(data):
    return " ".join(f"{b:02x}" for b in data)


def format_row(values):
    return "  ".join(f"{b:02x}" for b in values)
