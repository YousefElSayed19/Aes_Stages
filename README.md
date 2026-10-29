# AES Stages in Python

A pure-Python implementation of the **individual stages of AES**, built for learning. Every stage lives in its own file, runs on its own (input in, output out), and has an inverse, so you can walk forward from plain text and then back again.

An optional **step-by-step explanation mode** shows what happens behind the scenes (equations, lookups, GF(2^8) products) for every stage and for the direct-solve options.

> No external libraries. Only the Python standard library is used, so the algorithm stays visible.
>
> This project covers the stages from `Text` to `MixColumns` only. It has no `AddRoundKey` and no key expansion, so it is **not real encryption** and must not be used to protect data.

---

## Stages

**Forward**

```
Text -> Hex -> State -> SubBytes -> ShiftRows -> MixColumns
```

**Reverse**

```
InvMixColumns -> InvShiftRows -> InvSubBytes -> State -> Hex -> Text
```

| Stage | File | What it does |
|-------|------|--------------|
| Text <-> Hex | `aes/text_hex.py` | UTF-8 encoding to hex and back, plus PKCS#7 padding |
| Hex <-> State | `aes/state.py` | 16 bytes to a 4x4 matrix, filled column by column |
| SubBytes / InvSubBytes | `aes/sub_bytes.py` | Byte substitution; the S-Box is generated from its definition |
| ShiftRows / InvShiftRows | `aes/shift_rows.py` | Row `i` is rotated by `i` positions |
| MixColumns / InvMixColumns | `aes/mix_columns.py` | Each column is multiplied by a fixed matrix in GF(2^8) |
| GF(2^8) arithmetic | `aes/gf256.py` | `xtime`, multiplication and inverse in the AES field |
| Pipeline | `aes/pipeline.py` | The full forward and reverse chains as a library |
| Explanations | `aes/explain.py` | Text explanations (equations and per-byte steps) for every stage |
| Menu | `aes/cli.py` | The interactive terminal menu |

## Project layout

```
.
├── main.py
├── aes/
│   ├── __init__.py
│   ├── cli.py
│   ├── explain.py
│   ├── gf256.py
│   ├── mix_columns.py
│   ├── pipeline.py
│   ├── shift_rows.py
│   ├── state.py
│   ├── sub_bytes.py
│   ├── text_hex.py
│   └── utils.py
├── tests/
│   ├── test_aes_stages.py
│   ├── test_cli.py
│   └── test_no_comments.py
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Run

Requires Python 3.8 or newer. Nothing to install.

```bash
python main.py
```

```
 Forward                            Reverse
  1) Text   -> Hex                   7) InvMixColumns
  2) Hex    -> State                 8) InvShiftRows
  3) SubBytes                        9) InvSubBytes
  4) ShiftRows                      10) State -> Hex
  5) MixColumns                     11) Hex   -> Text
  6) Direct solve (forward chain)   12) Direct solve (reverse chain)
 13) Round trip (Text -> ... -> Text)
  E) Step-by-step explanations: ON (type E to toggle)
  0) Exit
```

### Individual stages

Options 1-5 and 7-11 each run alone: enter an input, get an output. Hex input is flexible (`3243f6a8`, `32 43 f6 a8` and `0x32,0x43` all work).

- Forward stages (2-5) **pad automatically** with PKCS#7 when the input is not a multiple of 16 bytes, and process longer input block by block.
- Reverse stages (7-10) need a multiple of 16 bytes (32 hex digits per block), because their input is the output of an earlier stage.

### Reusing the previous result

After every stage, the result is remembered. Add a letter after the option number to choose where the input comes from:

| Input | Meaning |
|-------|---------|
| `3` | Ask for a new value (you can still type `p` at the prompt to use the previous result) |
| `3 p` | Use the previous result directly (also `3p`, `3 prev`, `3 last`) |
| `3 n` | Ask for a new value |

Example: build the whole chain one stage at a time.

```
Choose: 1        -> enter text: helloworld
Choose: 2 p      -> padded and turned into a State
Choose: 3 p      -> SubBytes on that State
Choose: 4 p      -> ShiftRows
Choose: 5 p      -> MixColumns
Choose: 12 p     -> reverse everything back to: helloworld
```

You can also jump in with a fresh value at any point, for example `4 n` and then type your own hex. The text options (1, 6 and 13) use the previously entered or recovered text with `p`. The menu always shows the current previous result.

### Direct solve and explanations

- **6** runs the full forward chain from text and prints every stage.
- **12** runs the full reverse chain from the hex produced by option 6.
- **13** does both and checks that the text comes back.

With explanations ON (the default), every stage prints a "How it works" section before its result. Type `E` in the menu to turn it off. For example, MixColumns shows each byte as a GF(2^8) sum:

```
MixColumns multiplies every column by a fixed matrix in GF(2^8) (addition is XOR):
  | 02  03  01  01 |
  | 01  02  03  01 |
  | 01  01  02  03 |
  | 03  01  01  02 |
  column 0 = [d4  bf  5d  30]
    s'[0] = 02*d4 ^ 03*bf ^ 01*5d ^ 01*30 = b3 ^ da ^ 5d ^ 30 = 04
    s'[1] = 01*d4 ^ 02*bf ^ 03*5d ^ 01*30 = d4 ^ 65 ^ e7 ^ 30 = 66
    ...
```

SubBytes shows the inverse in GF(2^8) and the affine transformation for each byte, ShiftRows shows each row before and after the rotation, and the padding, Hex/State and text steps are explained too.

### Using it as a library

```python
from aes import pipeline

result = pipeline.forward("Hello AES")
mixed = pipeline.ciphertext_hex(result)

back = pipeline.reverse(mixed)
print(back["text"])
```

```python
from aes import hex_to_state, state_to_hex, sub_bytes, inv_sub_bytes

state = hex_to_state("193de3bea0f4e22b9ac68d2ae9f84808")
out = sub_bytes(state)
print(state_to_hex(out))
print(state_to_hex(inv_sub_bytes(out)))
```

---

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests check:

- known S-Box values and the inverse tables
- every stage against the official FIPS-197 values (Appendix B, round 1)
- that every inverse stage undoes its forward stage on random data
- full round trips for short, long, empty and non-ASCII text
- the menu: chaining with `p` and `n`, auto-padding, multi-block input and the explanation toggle
- that the explanation text matches the real results
- that the source files contain no comments or docstrings

## Notes

- The State is filled **column by column**: `state[row][col] = bytes[row + 4 * col]`.
- Padding is PKCS#7: `n = 16 - (length mod 16)` bytes of value `n` are appended and removed again in the reverse chain.
