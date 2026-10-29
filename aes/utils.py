"""
utils.py
--------
Small helpers shared by all stages: hex parsing/formatting and
pretty-printing of a 4x4 State.
"""

import re

BLOCK_SIZE = 16  # AES block = 16 bytes = 128 bits


def clean_hex(hex_str: str) -> str:
    """
    Normalize a user-supplied hex string.
    Accepts spaces, commas, newlines and 0x prefixes:
        "32 43 f6 a8"  /  "0x32,0x43"  /  "3243f6a8"
    Returns lowercase hex with no separators.
    Raises ValueError if the result is not valid hex of even length.
    """
    s = hex_str.strip().lower()
    s = re.sub(r"0x", "", s)
    s = re.sub(r"[\s,:\-]", "", s)
    if not s:
        raise ValueError("empty hex input")
    if len(s) % 2 != 0:
        raise ValueError("hex input must have an even number of digits")
    if not re.fullmatch(r"[0-9a-f]+", s):
        raise ValueError("hex input contains non-hex characters")
    return s


def bytes_to_spaced_hex(data: bytes) -> str:
    """b'\\x32\\x43' -> '32 43'"""
    return " ".join(f"{b:02x}" for b in data)


def format_state(state) -> str:
    """Return a 4x4 State as a printable matrix string."""
    lines = []
    for row in state:
        lines.append("  ".join(f"{b:02x}" for b in row))
    return "\n".join(lines)
