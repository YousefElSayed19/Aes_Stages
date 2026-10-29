from .utils import BLOCK_SIZE, clean_hex


def hex_to_state(hex_str):
    data = bytes.fromhex(clean_hex(hex_str))
    if len(data) != BLOCK_SIZE:
        raise ValueError(
            f"A State needs exactly 16 bytes (32 hex digits), got {len(data)} bytes."
        )
    return [[data[row + 4 * col] for col in range(4)] for row in range(4)]


def state_to_hex(state):
    return "".join(f"{state[row][col]:02x}" for col in range(4) for row in range(4))


def copy_state(state):
    return [row[:] for row in state]
