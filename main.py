"""
main.py
-------
Interactive menu for the AES stages project.

Every stage runs on its own: you give it an Input, it prints the Output
(as a 4x4 State and as hex) so you can copy the Output into the next stage.

Run:
    python main.py
"""

from aes import pipeline
from aes.mix_columns import inv_mix_columns, mix_columns
from aes.shift_rows import inv_shift_rows, shift_rows
from aes.state import hex_to_state, state_to_hex
from aes.sub_bytes import inv_sub_bytes, sub_bytes
from aes.text_hex import hex_to_text, pad_pkcs7, split_blocks, text_to_hex
from aes.utils import bytes_to_spaced_hex, clean_hex, format_state

MENU = """
==================== AES Stages ====================
 Forward                          Reverse
 -------                          -------
 1) Text   -> Hex                 7) InvMixColumns
 2) Hex    -> State               8) InvShiftRows
 3) SubBytes                      9) InvSubBytes
 4) ShiftRows                    10) State -> Hex
 5) MixColumns                   11) Hex   -> Text
 6) Full forward chain           12) Full reverse chain
 ------------------------------------------------------
 13) Full round trip demo (Text -> ... -> Text)
  0) Exit
====================================================="""


def show_state(title, state):
    print(f"\n{title}")
    print(format_state(state))
    print(f"hex: {state_to_hex(state)}")


def read_blocks(raw):
    """
    Turn a hex string of ANY length into a list of 16-byte blocks.
    If the length is not a multiple of 16, PKCS#7 padding is added
    automatically (and a notice is printed).
    """
    data = bytes.fromhex(clean_hex(raw))
    if len(data) % 16 != 0:
        data = pad_pkcs7(data)
        print(f"(auto-padded with PKCS#7 to {len(data)} bytes: {data.hex()})")
    return split_blocks(data)


def run_state_stage(title, func, auto_pad=True):
    """
    Ask for hex, apply func to every 16-byte block, print the result.
    Forward stages auto-pad; inverse stages need exact 16-byte blocks.
    """
    raw = input("Enter hex (any length, auto-padded to 16-byte blocks): "
                if auto_pad else
                "Enter State as hex (16 bytes / 32 hex digits): ")
    if auto_pad:
        blocks = read_blocks(raw)
    else:
        blocks = [bytes.fromhex(clean_hex(raw))]
    for i, block in enumerate(blocks, 1):
        if len(blocks) > 1:
            print(f"\n---------- Block {i} ----------")
        state = hex_to_state(block.hex())
        show_state("Input State:", state)
        show_state(f"Output State ({title}):", func(state))


def stage_text_to_hex():
    text = input("Enter text: ")
    h = text_to_hex(text)
    print(f"\nHex: {h}")
    print(f"Hex (spaced): {bytes_to_spaced_hex(bytes.fromhex(h))}")


def stage_hex_to_state():
    raw = input("Enter hex (any length, auto-padded to 16-byte blocks): ")
    blocks = read_blocks(raw)
    for i, block in enumerate(blocks, 1):
        if len(blocks) > 1:
            print(f"\n---------- Block {i} ----------")
        show_state("State:", hex_to_state(block.hex()))


def stage_state_to_hex():
    raw = input("Enter State as hex (column-major, 32 hex digits): ")
    state = hex_to_state(raw)
    show_state("State:", state)
    print(f"\nHex: {state_to_hex(state)}")


def stage_hex_to_text():
    raw = input("Enter hex of the text (no padding): ")
    print(f"\nText: {hex_to_text(raw)}")


def stage_full_forward():
    text = input("Enter text: ")
    result = pipeline.forward(text)
    print(f"\n[Text -> Hex]      {result['hex']}")
    print(f"[After padding]    {result['padded']}")
    for i, b in enumerate(result["blocks"], 1):
        print(f"\n---------- Block {i} ----------")
        show_state("[Hex -> State]", b["state_in"])
        show_state("[SubBytes]", b["after_sub"])
        show_state("[ShiftRows]", b["after_shift"])
        show_state("[MixColumns]", b["after_mix"])
    print(f"\nFinal hex (after MixColumns): {pipeline.ciphertext_hex(result)}")
    print("Copy this hex into option 12 to reverse it.")


def stage_full_reverse():
    raw = input("Enter hex produced by the forward chain: ")
    result = pipeline.reverse(raw)
    for i, b in enumerate(result["blocks"], 1):
        print(f"\n---------- Block {i} ----------")
        show_state("[Input State]", b["state_in"])
        show_state("[InvMixColumns]", b["after_inv_mix"])
        show_state("[InvShiftRows]", b["after_inv_shift"])
        show_state("[InvSubBytes]", b["after_inv_sub"])
    print(f"\n[State -> Hex]  {result['padded']}")
    print(f"[Remove padding] {result['hex']}")
    print(f"[Hex -> Text]   {result['text']}")


def stage_demo():
    text = input("Enter text: ")
    fwd = pipeline.forward(text)
    mixed = pipeline.ciphertext_hex(fwd)
    back = pipeline.reverse(mixed)
    print(f"\nOriginal text : {text}")
    print(f"After forward : {mixed}")
    print(f"Recovered text: {back['text']}")
    print("Round trip OK" if back["text"] == text else "Round trip FAILED")


ACTIONS = {
    "1": stage_text_to_hex,
    "2": stage_hex_to_state,
    "3": lambda: run_state_stage("SubBytes", sub_bytes),
    "4": lambda: run_state_stage("ShiftRows", shift_rows),
    "5": lambda: run_state_stage("MixColumns", mix_columns),
    "6": stage_full_forward,
    "7": lambda: run_state_stage("InvMixColumns", inv_mix_columns, auto_pad=False),
    "8": lambda: run_state_stage("InvShiftRows", inv_shift_rows, auto_pad=False),
    "9": lambda: run_state_stage("InvSubBytes", inv_sub_bytes, auto_pad=False),
    "10": stage_state_to_hex,
    "11": stage_hex_to_text,
    "12": stage_full_reverse,
    "13": stage_demo,
}


def main():
    while True:
        print(MENU)
        choice = input("Choose: ").strip()
        if choice == "0":
            print("Bye!")
            break
        action = ACTIONS.get(choice)
        if action is None:
            print("Invalid choice, try again.")
            continue
        try:
            action()
        except ValueError as err:
            print(f"\nError: {err}")
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")


if __name__ == "__main__":
    main()
