import re

from .explain import (
    explain_hex_to_state,
    explain_hex_to_text,
    explain_inv_mix_columns,
    explain_inv_shift_rows,
    explain_inv_sub_bytes,
    explain_mix_columns,
    explain_padding,
    explain_shift_rows,
    explain_state_to_hex,
    explain_sub_bytes,
    explain_text_to_hex,
    explain_unpad,
)
from .mix_columns import inv_mix_columns, mix_columns
from .shift_rows import inv_shift_rows, shift_rows
from .state import hex_to_state, state_to_hex
from .sub_bytes import inv_sub_bytes, sub_bytes
from .text_hex import pad_pkcs7, split_blocks, text_to_hex, unpad_pkcs7
from .utils import BLOCK_SIZE, bytes_to_spaced_hex, clean_hex, format_row

PREVIOUS_FLAGS = {"p", "prev", "previous", "last"}
NEW_FLAGS = {"n", "new"}
PREVIOUS_WORDS = {"p", "/p", "prev"}

FORWARD_STAGES = [
    ("SubBytes", sub_bytes, explain_sub_bytes),
    ("ShiftRows", shift_rows, explain_shift_rows),
    ("MixColumns", mix_columns, explain_mix_columns),
]

INVERSE_STAGES = [
    ("InvMixColumns", inv_mix_columns, explain_inv_mix_columns),
    ("InvShiftRows", inv_shift_rows, explain_inv_shift_rows),
    ("InvSubBytes", inv_sub_bytes, explain_inv_sub_bytes),
]


class Session:
    def __init__(self):
        self.last_hex = None
        self.last_text = None
        self.explain = True


def say(session, lines):
    if not session.explain:
        return
    print("\n  How it works:")
    for line in lines:
        print(f"    {line}")


def header(title):
    print(f"\n=== {title} ===")


def show_state(label, state):
    print(f"\n  {label}")
    for row in state:
        print(f"    {format_row(row)}")
    print(f"  hex: {state_to_hex(state)}")


def show_pair(left, right):
    width = 22
    print(f"\n  {'Input State':<{width}}Output State")
    for left_row, right_row in zip(left, right):
        print(f"  {format_row(left_row):<{width}}{format_row(right_row)}")
    print(f"  Input hex : {state_to_hex(left)}")
    print(f"  Output hex: {state_to_hex(right)}")


def get_text(session, mode):
    if mode == "prev":
        if session.last_text is None:
            raise ValueError("There is no previous text yet. Run a text stage first.")
        print(f"Using previous text: {session.last_text}")
        return session.last_text
    hint = " (type /p for the previous text)" if session.last_text is not None else ""
    raw = input(f"Enter text{hint}: ")
    if raw.strip().lower() == "/p":
        return get_text(session, "prev")
    return raw


def get_hex(session, mode):
    if mode == "prev":
        if session.last_hex is None:
            raise ValueError("There is no previous result yet. Run a stage first.")
        print(f"Using previous result: {session.last_hex}")
        return session.last_hex
    hint = " (type p for the previous result)" if session.last_hex is not None else ""
    raw = input(f"Enter hex{hint}: ")
    if raw.strip().lower() in PREVIOUS_WORDS:
        return get_hex(session, "prev")
    return raw


def to_blocks(session, raw, auto_pad):
    data = bytes.fromhex(clean_hex(raw))
    if len(data) % BLOCK_SIZE != 0:
        if not auto_pad:
            raise ValueError(
                f"Input is {len(data)} bytes; this stage needs a multiple of 16 bytes "
                "(32 hex digits per block)."
            )
        say(session, explain_padding(len(data)))
        data = pad_pkcs7(data)
        print(f"Padded input: {data.hex()}")
    return split_blocks(data)


def block_title(title, index, total):
    return f"{title} - block {index} of {total}" if total > 1 else title


def stage_text_to_hex(session, mode):
    text = get_text(session, mode)
    header("Text -> Hex")
    say(session, explain_text_to_hex(text))
    result = text_to_hex(text)
    print(f"\nHex: {result}")
    print(f"Hex (spaced): {bytes_to_spaced_hex(bytes.fromhex(result))}")
    session.last_hex = result
    session.last_text = text


def stage_hex_to_state(session, mode):
    blocks = to_blocks(session, get_hex(session, mode), True)
    for i, block in enumerate(blocks, 1):
        header(block_title("Hex -> State", i, len(blocks)))
        say(session, explain_hex_to_state(block))
        show_state("State", hex_to_state(block.hex()))
    session.last_hex = b"".join(blocks).hex()
    print(f"\nResult: {session.last_hex}")


def state_stage(session, mode, title, func, explainer, auto_pad):
    blocks = to_blocks(session, get_hex(session, mode), auto_pad)
    out_hex = ""
    for i, block in enumerate(blocks, 1):
        state = hex_to_state(block.hex())
        header(block_title(title, i, len(blocks)))
        say(session, explainer(state))
        result = func(state)
        show_pair(state, result)
        out_hex += state_to_hex(result)
    session.last_hex = out_hex
    print(f"\nResult: {out_hex}")


def stage_state_to_hex(session, mode):
    blocks = to_blocks(session, get_hex(session, mode), False)
    out_hex = ""
    for i, block in enumerate(blocks, 1):
        state = hex_to_state(block.hex())
        header(block_title("State -> Hex", i, len(blocks)))
        show_state("State", state)
        say(session, explain_state_to_hex(state))
        out_hex += state_to_hex(state)
    session.last_hex = out_hex
    print(f"\nHex: {out_hex}")


def decode_plain(session, data, strict):
    plain = data
    if len(data) % BLOCK_SIZE == 0 and data:
        try:
            plain = unpad_pkcs7(data)
            say(session, explain_unpad(data, True))
        except ValueError:
            if strict:
                raise ValueError(
                    "Invalid padding after reversing. Was this hex produced by the forward chain?"
                )
            say(session, explain_unpad(data, False))
    elif strict:
        raise ValueError("The data must be a multiple of 16 bytes.")
    try:
        text = plain.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("The resulting bytes are not valid UTF-8 text.")
    say(session, explain_hex_to_text(plain))
    print(f"\nPlain hex: {plain.hex()}")
    print(f"Text: {text}")
    session.last_text = text
    session.last_hex = plain.hex()
    return text


def stage_hex_to_text(session, mode):
    data = bytes.fromhex(clean_hex(get_hex(session, mode)))
    header("Hex -> Text")
    decode_plain(session, data, False)


def forward_chain(session, text):
    header("Text -> Hex")
    say(session, explain_text_to_hex(text))
    data = text.encode("utf-8")
    print(f"\nHex: {data.hex()}")

    header("Padding")
    say(session, explain_padding(len(data)))
    padded = pad_pkcs7(data)
    print(f"\nPadded hex: {padded.hex()}")

    blocks = split_blocks(padded)
    out_hex = ""
    for i, block in enumerate(blocks, 1):
        header(block_title("Hex -> State", i, len(blocks)))
        say(session, explain_hex_to_state(block))
        state = hex_to_state(block.hex())
        show_state("State", state)
        for title, func, explainer in FORWARD_STAGES:
            header(block_title(title, i, len(blocks)))
            say(session, explainer(state))
            result = func(state)
            show_pair(state, result)
            state = result
        out_hex += state_to_hex(state)

    print(f"\nFinal hex after MixColumns: {out_hex}")
    session.last_hex = out_hex
    session.last_text = text
    return out_hex


def reverse_chain(session, raw):
    blocks = to_blocks(session, raw, False)
    padded = b""
    for i, block in enumerate(blocks, 1):
        state = hex_to_state(block.hex())
        header(block_title("Input State", i, len(blocks)))
        show_state("State", state)
        for title, func, explainer in INVERSE_STAGES:
            header(block_title(title, i, len(blocks)))
            say(session, explainer(state))
            result = func(state)
            show_pair(state, result)
            state = result
        padded += bytes.fromhex(state_to_hex(state))

    header("State -> Hex")
    print(f"\nPadded hex: {padded.hex()}")

    header("Remove padding and Hex -> Text")
    return decode_plain(session, padded, True)


def stage_forward_chain(session, mode):
    forward_chain(session, get_text(session, mode))


def stage_reverse_chain(session, mode):
    reverse_chain(session, get_hex(session, mode))


def stage_round_trip(session, mode):
    text = get_text(session, mode)
    mixed = forward_chain(session, text)
    print("\n" + "-" * 60)
    print("Now reversing the result...")
    recovered = reverse_chain(session, mixed)
    print("\n" + "-" * 60)
    print(f"Original text : {text}")
    print(f"After forward : {mixed}")
    print(f"Recovered text: {recovered}")
    print("Round trip OK" if recovered == text else "Round trip FAILED")


ACTIONS = {
    "1": stage_text_to_hex,
    "2": stage_hex_to_state,
    "3": lambda s, m: state_stage(s, m, "SubBytes", sub_bytes, explain_sub_bytes, True),
    "4": lambda s, m: state_stage(s, m, "ShiftRows", shift_rows, explain_shift_rows, True),
    "5": lambda s, m: state_stage(s, m, "MixColumns", mix_columns, explain_mix_columns, True),
    "6": stage_forward_chain,
    "7": lambda s, m: state_stage(
        s, m, "InvMixColumns", inv_mix_columns, explain_inv_mix_columns, False
    ),
    "8": lambda s, m: state_stage(
        s, m, "InvShiftRows", inv_shift_rows, explain_inv_shift_rows, False
    ),
    "9": lambda s, m: state_stage(
        s, m, "InvSubBytes", inv_sub_bytes, explain_inv_sub_bytes, False
    ),
    "10": stage_state_to_hex,
    "11": stage_hex_to_text,
    "12": stage_reverse_chain,
    "13": stage_round_trip,
}


def short(value, limit=64):
    if value is None:
        return "(none yet)"
    return value if len(value) <= limit else value[:limit] + "..."


def print_menu(session):
    print(
        f"""
==================== AES Stages ====================
 Forward                            Reverse
 -------                            -------
  1) Text   -> Hex                   7) InvMixColumns
  2) Hex    -> State                 8) InvShiftRows
  3) SubBytes                        9) InvSubBytes
  4) ShiftRows                      10) State -> Hex
  5) MixColumns                     11) Hex   -> Text
  6) Direct solve (forward chain)   12) Direct solve (reverse chain)
 ----------------------------------------------------
 13) Round trip (Text -> ... -> Text)
  E) Step-by-step explanations: {"ON" if session.explain else "OFF"} (type E to toggle)
  0) Exit
 ----------------------------------------------------
 Tip: add p after a number to reuse the previous result (example: 3 p)
      add n (or nothing) to type a new value (example: 3 n)
 Previous result: {short(session.last_hex)}
 Previous text  : {short(session.last_text)}
====================================================="""
    )


def parse_choice(raw):
    match = re.fullmatch(r"(\d+|e)\s*([a-z]*)", raw.strip().lower())
    if not match:
        raise ValueError("Invalid choice. Use a number from the menu, optionally followed by p or n.")
    key, flag = match.groups()
    if not flag or flag in NEW_FLAGS:
        return key, "new"
    if flag in PREVIOUS_FLAGS:
        return key, "prev"
    raise ValueError("Unknown option after the number. Use p (previous result) or n (new value).")


def main():
    session = Session()
    while True:
        print_menu(session)
        try:
            raw = input("Choose: ")
        except EOFError:
            print()
            break
        if raw.strip() == "0":
            print("Bye!")
            break
        try:
            key, mode = parse_choice(raw)
            if key == "e":
                session.explain = not session.explain
                print(f"\nExplanations are now {'ON' if session.explain else 'OFF'}.")
                continue
            action = ACTIONS.get(key)
            if action is None:
                raise ValueError("Invalid choice. Use a number from the menu.")
            action(session, mode)
        except ValueError as err:
            print(f"\nError: {err}")
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
