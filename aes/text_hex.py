from .utils import BLOCK_SIZE, clean_hex


def text_to_hex(text):
    return text.encode("utf-8").hex()


def hex_to_text(hex_str):
    if not hex_str.strip():
        return ""
    return bytes.fromhex(clean_hex(hex_str)).decode("utf-8")


def pad_pkcs7(data, block_size=BLOCK_SIZE):
    n = block_size - (len(data) % block_size)
    return data + bytes([n]) * n


def unpad_pkcs7(data, block_size=BLOCK_SIZE):
    if not data or len(data) % block_size != 0:
        raise ValueError("Data length must be a positive multiple of 16 bytes.")
    n = data[-1]
    if n < 1 or n > block_size or data[-n:] != bytes([n]) * n:
        raise ValueError("Invalid padding.")
    return data[:-n]


def split_blocks(data, block_size=BLOCK_SIZE):
    if len(data) % block_size != 0:
        raise ValueError("Data length must be a multiple of 16 bytes.")
    return [data[i:i + block_size] for i in range(0, len(data), block_size)]
