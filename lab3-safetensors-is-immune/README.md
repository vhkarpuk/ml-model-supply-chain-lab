# Lab 3 — Safetensors is immune by design

Lab 1 showed a pickle model *executing* code on load. Lab 2 *detected* that code
by reading the opcodes. This lab shows the real fix: a format where the attack
has **nowhere to live** — so there's nothing to detect in the first place.

## The idea

A pickle file is a *program* — a list of rebuild instructions, and one of them
can be "call `os.system`." Safetensors stores only two things:

- a **JSON header** — a label per tensor: name, dtype, shape, byte offsets.
- the **raw numbers**, in fixed positions after the header.

No opcodes. No "call this function." The reader isn't a virtual machine following
instructions — it's a dumb reader pulling numbers from fixed byte positions.
There is no executable line to poison.

## Run

```powershell
python make_safe.py      # creates safe_model.safetensors
python inspect_safe.py   # prints the header without loading the model
```

## What you see

`inspect_safe.py` reads the first 8 bytes (the header length), then the JSON
header — without loading a single tensor into a model. Output:

```json
{
  "layers.0.attention.key.weight":   { "dtype": "F32", "shape": [3], "data_offsets": [0, 12] },
  "layers.0.attention.query.weight": { "dtype": "F32", "shape": [3], "data_offsets": [12, 24] }
}
```

Each tensor is just "type F32, shape [3], lives from byte X to byte Y." Each
float32 is 4 bytes, three per tensor = 12 bytes, packed in sequence — that's why
the offsets are `[0, 12]` and `[12, 24]`.

## The contrast (Lab 2 vs Lab 3)

| | Pickle (Lab 2) | Safetensors (Lab 3) |
|---|---|---|
| Header content | opcodes: `STACK_GLOBAL`, `REDUCE` | labels: `dtype`, `shape`, `data_offsets` |
| Reader | a virtual machine that *executes* | a reader that *looks up bytes* |
| Can hold code? | yes — that's the vulnerability | no — no field for it |
| Needs a scanner? | yes, and scanners have bypasses | no — nothing to scan |

## Where could a payload go?

- **In the header?** It only accepts `dtype`, `shape`, `data_offsets`. Anything
  else is ignored or fails as a format error — there is no "execute" field.
- **In the number section?** It's read by byte position. Putting code there just
  produces bytes that don't form valid numbers — the reader rejects them, it does
  not run them.

There is no door to walk through. That's the difference between searching luggage
for a weapon (Lab 2) and having no boarding gate at all (Lab 3).

## The takeaway for a triage policy

Rule number one is not "scan better" — it's **prefer the format that has nothing
to scan**. Pickle needs a scanner because it has something to hide; safetensors
does not, because it has nowhere to hide it. When a model ships both formats,
force the safetensors one.

## Files

| File | Role |
|---|---|
| `make_safe.py` | Creates a safetensors model with named tensors |
| `inspect_safe.py` | Reads the JSON header without loading the model |
