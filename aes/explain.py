from .gf256 import ginv, gmul
from .mix_columns import INV_MIX_MATRIX, MIX_MATRIX
from .sub_bytes import SBOX, affine, inv_affine
from .utils import BLOCK_SIZE, bytes_to_spaced_hex, format_row

MAX_CHARS_SHOWN = 40


def explain_text_to_hex(text):
    lines = [
        "Each character is encoded as UTF-8 bytes; every byte is written as two hex digits."
    ]
    if not text:
        lines.append("  (empty text -> no bytes)")
        return lines
    for ch in text[:MAX_CHARS_SHOWN]:
        encoded = ch.encode("utf-8")
        lines.append(
            f"  {ch!r} -> code point U+{ord(ch):04X} -> byte(s) {bytes_to_spaced_hex(encoded)}"
        )
    if len(text) > MAX_CHARS_SHOWN:
        lines.append(f"  ... and {len(text) - MAX_CHARS_SHOWN} more character(s)")
    return lines


def explain_padding(length):
    n = BLOCK_SIZE - length % BLOCK_SIZE
    return [
        "AES works on 16-byte blocks, so the data is padded with PKCS#7.",
        f"  n = 16 - (length mod 16) = 16 - ({length} mod 16) = {n}",
        f"  append {n} byte(s), each with the value {n:02x}",
        f"  new length = {length + n} bytes = {(length + n) // BLOCK_SIZE} block(s)",
    ]


def explain_hex_to_state(block):
    lines = [
        "The State is a 4x4 matrix filled column by column:",
        "  state[row][col] = bytes[row + 4 * col]",
    ]
    for c in range(4):
        chunk = block[4 * c:4 * c + 4]
        lines.append(
            f"  column {c} <- bytes {4 * c}..{4 * c + 3} = {bytes_to_spaced_hex(chunk)}"
        )
    return lines


def explain_state_to_hex(state):
    lines = ["Reading the State column by column gives the bytes back:"]
    for c in range(4):
        column = [state[r][c] for r in range(4)]
        lines.append(f"  column {c} = {bytes_to_spaced_hex(column)}")
    return lines


def explain_sub_bytes(state):
    lines = [
        "SubBytes replaces every byte x with S(x) = affine(inverse(x)).",
        "  inverse(x): multiplicative inverse in GF(2^8) modulo x^8 + x^4 + x^3 + x + 1 (inverse of 00 is 00)",
        "  affine(b) = b ^ rotl(b,1) ^ rotl(b,2) ^ rotl(b,3) ^ rotl(b,4) ^ 63   (^ = XOR)",
    ]
    for r in range(4):
        for c in range(4):
            x = state[r][c]
            b = ginv(x)
            lines.append(
                f"  [{r}][{c}] x={x:02x}  inverse(x)={b:02x}  affine({b:02x})={affine(b):02x}  -> S(x)={SBOX[x]:02x}"
            )
    return lines


def explain_inv_sub_bytes(state):
    lines = [
        "InvSubBytes undoes SubBytes: x = inverse(inv_affine(y)).",
        "  inv_affine(y) = rotl(y,1) ^ rotl(y,3) ^ rotl(y,6) ^ 05   (^ = XOR)",
        "  inverse(b): multiplicative inverse in GF(2^8) (inverse of 00 is 00)",
    ]
    for r in range(4):
        for c in range(4):
            y = state[r][c]
            b = inv_affine(y)
            x = ginv(b)
            lines.append(
                f"  [{r}][{c}] y={y:02x}  inv_affine(y)={b:02x}  inverse({b:02x})={x:02x}  -> x={x:02x}"
            )
    return lines


def explain_shift_rows(state):
    lines = ["ShiftRows rotates row i to the LEFT by i positions (row 0 stays the same)."]
    for r in range(4):
        row = state[r]
        shifted = row[r:] + row[:r]
        lines.append(
            f"  row {r}: [{format_row(row)}] rotate left by {r} -> [{format_row(shifted)}]"
        )
    return lines


def explain_inv_shift_rows(state):
    lines = ["InvShiftRows rotates row i to the RIGHT by i positions (row 0 stays the same)."]
    for r in range(4):
        row = state[r]
        shifted = row[-r:] + row[:-r] if r else row[:]
        lines.append(
            f"  row {r}: [{format_row(row)}] rotate right by {r} -> [{format_row(shifted)}]"
        )
    return lines


def _explain_mix(state, matrix, name):
    lines = [
        f"{name} multiplies every column by a fixed matrix in GF(2^8) (addition is XOR):",
    ]
    for row in matrix:
        lines.append(f"  | {format_row(row)} |")
    lines.append("  s'[r] = (m[r][0]*s[0]) ^ (m[r][1]*s[1]) ^ (m[r][2]*s[2]) ^ (m[r][3]*s[3])")
    lines.append(
        "  *01 keeps the byte, *02 is xtime (shift left, XOR 1b on overflow), *03 = *02 ^ *01; other factors use repeated xtime"
    )
    for c in range(4):
        column = [state[r][c] for r in range(4)]
        lines.append(f"  column {c} = [{format_row(column)}]")
        for r in range(4):
            terms = [gmul(matrix[r][k], column[k]) for k in range(4)]
            result = terms[0] ^ terms[1] ^ terms[2] ^ terms[3]
            expression = " ^ ".join(f"{matrix[r][k]:02x}*{column[k]:02x}" for k in range(4))
            values = " ^ ".join(f"{t:02x}" for t in terms)
            lines.append(f"    s'[{r}] = {expression} = {values} = {result:02x}")
    return lines


def explain_mix_columns(state):
    return _explain_mix(state, MIX_MATRIX, "MixColumns")


def explain_inv_mix_columns(state):
    return _explain_mix(state, INV_MIX_MATRIX, "InvMixColumns")


def explain_unpad(data, found):
    if not found:
        return ["No valid PKCS#7 padding found, so the bytes are used as they are."]
    n = data[-1]
    return [
        "PKCS#7 padding is removed: the last byte tells how many bytes were added.",
        f"  last byte = {n:02x} -> remove the last {n} byte(s)",
        f"  {len(data)} bytes - {n} = {len(data) - n} bytes remain",
    ]


def explain_hex_to_text(data):
    return [
        "The bytes are decoded as UTF-8 text:",
        f"  {bytes_to_spaced_hex(data)}  ->  {data.decode('utf-8')!r}",
    ]
