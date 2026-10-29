# AES Stages in Python

مشروع بايثون بيطبّق **مراحل خوارزمية AES** كل مرحلة في ملف لوحدها، وكل مرحلة شغالة بشكل مستقل (تاخد Input وتطلّع Output)، وبعد كده بنقدر نعمل **Reverse** لكل مرحلة لحد ما نرجع للـ Plain Text.

> الكود مكتوب بـ Python العادي **بدون أي مكتبات خارجية**، علشان الخوارزمية تكون واضحة من جوّه.

---

## المراحل

**Forward**

```
Text → Hex → State → SubBytes → ShiftRows → MixColumns
```

**Reverse**

```
InvMixColumns → InvShiftRows → InvSubBytes → State → Hex → Text
```

| # | المرحلة | الملف | الوصف |
|---|---------|-------|-------|
| 1 | Text ↔ Hex | `aes/text_hex.py` | تحويل النص (UTF-8) لـ Hex والعكس + PKCS#7 padding |
| 2 | Hex ↔ State | `aes/state.py` | تحويل 16 بايت لمصفوفة 4×4 بترتيب الأعمدة |
| 3 | SubBytes / InvSubBytes | `aes/sub_bytes.py` | استبدال كل بايت من الـ S-Box (بتتولّد بالكود من تعريفها) |
| 4 | ShiftRows / InvShiftRows | `aes/shift_rows.py` | إزاحة الصف رقم `i` لليسار بمقدار `i` |
| 5 | MixColumns / InvMixColumns | `aes/mix_columns.py` | ضرب كل عمود في مصفوفة ثابتة داخل GF(2⁸) |
| - | GF(2⁸) | `aes/gf256.py` | عمليات الضرب والمعكوس في الحقل |
| - | Pipeline | `aes/pipeline.py` | ربط كل المراحل ببعض (forward و reverse) |
| - | Utils | `aes/utils.py` | دوال مساعدة (تنضيف الـ Hex، طباعة الـ State) |

---

## هيكل المشروع

```
aes-stages/
├── main.py                 # قايمة تفاعلية لتشغيل كل مرحلة
├── aes/
│   ├── __init__.py
│   ├── gf256.py            # حسابات GF(2^8)
│   ├── utils.py            # دوال مساعدة
│   ├── text_hex.py         # Text <-> Hex + padding
│   ├── state.py            # Hex <-> State
│   ├── sub_bytes.py        # SubBytes / InvSubBytes
│   ├── shift_rows.py       # ShiftRows / InvShiftRows
│   ├── mix_columns.py      # MixColumns / InvMixColumns
│   └── pipeline.py         # السلسلة الكاملة forward / reverse
├── tests/
│   └── test_aes_stages.py  # اختبارات بقيم رسمية من FIPS-197
├── requirements.txt
├── .gitignore
└── README.md
```

---

## التشغيل

المطلوب Python 3.8 أو أحدث، ومفيش أي حاجة تتثبّت.

```bash
python main.py
```

هتظهرلك قايمة:

```
 1) Text   -> Hex                 7) InvMixColumns
 2) Hex    -> State               8) InvShiftRows
 3) SubBytes                      9) InvSubBytes
 4) ShiftRows                    10) State -> Hex
 5) MixColumns                   11) Hex   -> Text
 6) Full forward chain           12) Full reverse chain
 13) Full round trip demo (Text -> ... -> Text)
  0) Exit
```

- المراحل من 1 لـ 5 ومن 7 لـ 11 بتشتغل **لوحدها**: بتدخّل الـ Input وتاخد الـ Output (كـ State وكـ Hex) وتقدر تنسخه وتحطه في المرحلة اللي بعدها.
- الخيار 6 بيشغّل السلسلة الكاملة وبيعرض ناتج كل مرحلة.
- الخيار 12 بيعمل Reverse كامل من الـ Hex الناتج بعد MixColumns.
- الخيار 13 بيعمل Round trip ويتأكد إن النص الراجع هو نفس الأصلي.

الـ Hex بيقبل صيغ كتير: `32 43 f6 a8` أو `0x32,0x43` أو `3243f6a8`.

### مثال

الـ Input: `Hello AES`

```
[Text -> Hex]    48656c6c6f20414553
[After padding]  48656c6c6f2041455307070707070707

[Hex -> State]        [SubBytes]            [ShiftRows]           [MixColumns]
48  6f  53  07        52  a8  ed  c5        52  a8  ed  c5        66  8a  ab  00
65  20  07  07        4d  b7  c5  c5        b7  c5  c5  4d        b6  3d  e2  04
6c  41  07  07        50  83  c5  c5        c5  c5  50  83        20  0c  3a  c1
6c  45  07  07        50  6e  c5  c5        c5  50  6e  c5        15  43  65  0b

Final hex: 66b620158a3d0c43abe23a650004c10b
```

لو حطيت الـ Final hex في الخيار 12 هترجعلك `Hello AES`.

### الاستخدام كمكتبة

```python
from aes import pipeline

result = pipeline.forward("Hello AES")
mixed = pipeline.ciphertext_hex(result)   # 66b620158a3d0c43abe23a650004c10b

back = pipeline.reverse(mixed)
print(back["text"])                       # Hello AES
```

أو كل مرحلة لوحدها:

```python
from aes import hex_to_state, state_to_hex, sub_bytes, inv_sub_bytes

state = hex_to_state("193de3bea0f4e22b9ac68d2ae9f84808")
out = sub_bytes(state)
print(state_to_hex(out))                  # d42711aee0bf98f1b8b45de51e415230
print(state_to_hex(inv_sub_bytes(out)))   # 193de3bea0f4e22b9ac68d2ae9f84808
```

---

## الاختبارات

```bash
python -m unittest discover -s tests -v
```

الاختبارات بتتأكد من:

- قيم S-Box المعروفة.
- ناتج كل مرحلة مقارنةً بالقيم الرسمية في **FIPS-197 (Appendix B, Round 1)**.
- إن كل Inverse بيلغي الـ Forward بتاعه (على قيم عشوائية).
- Round trip كامل للنصوص (إنجليزي وعربي وفاضي ونص أطول من Block).

---

## ملاحظات مهمة

- **ترتيب الـ State بالأعمدة**: البايتات `b0..b15` بتتحط عمود ورا عمود، يعني `state[row][col] = bytes[row + 4*col]`.
- **Padding**: AES بيشتغل على Blocks حجمها 16 بايت، فالنص بيتعمله PKCS#7 padding وبيتقسم لـ Blocks، وبيتشال الـ padding في الـ Reverse.
- المشروع بيغطي **المراحل المطلوبة فقط** (من Hex لحد MixColumns). مفيهوش `AddRoundKey` ولا `Key Expansion` ولا الجولات الكاملة، فمش تشفير حقيقي ومينفعش يتستخدم لحماية بيانات.

---

## Author

اعمل التعديل ده بإسمك قبل ما ترفع المشروع على GitHub ✌️
