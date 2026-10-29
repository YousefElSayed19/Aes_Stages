"""
text_hex.py
-----------
Stage 1: Text <-> Hex

Text is encoded as UTF-8 bytes, so Arabic / symbols work too.

AES works on 16-byte blocks, so we also provide PKCS#7 padding helpers:
    pad   : adds N bytes of value N so the length becomes a multiple of 16
    unpad : removes that padding again
"""

from .utils import BLOCK_SIZE, clean_hex


def text_to_hex(text: str) -> str:
    """'Hi' -> '4869'"""
    return text.encode("utf-8").hex()


def hex_to_text(hex_str: str) -> str:
    """'4869' -> 'Hi'  (an empty hex string gives an empty text)"""
    if not hex_str.strip():
        return ""
    return bytes.fromhex(clean_hex(hex_str)).decode("utf-8")


def pad_pkcs7(data: bytes, block_size: int = BLOCK_SIZE) -> bytes:
    """Pad data to a multiple of block_size (always adds at least 1 byte)."""
    n = block_size - (len(data) % block_size)
    return data + bytes([n]) * n


def unpad_pkcs7(data: bytes, block_size: int = BLOCK_SIZE) -> bytes:
    """Remove PKCS#7 padding. Raises ValueError if padding is invalid."""
    if not data or len(data) % block_size != 0:
        raise ValueError("data length must be a positive multiple of 16 bytes")
    n = data[-1]
    if n < 1 or n > block_size or data[-n:] != bytes([n]) * n:
        raise ValueError("invalid padding")
    return data[:-n]


def split_blocks(data: bytes, block_size: int = BLOCK_SIZE):
    """Split bytes into a list of 16-byte blocks."""
    if len(data) % block_size != 0:
        raise ValueError("data length must be a multiple of 16 bytes")
    return [data[i:i + block_size] for i in range(0, len(data), block_size)]
