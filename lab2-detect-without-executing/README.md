# Lab 2 — Detect the payload without executing it

Lab 1 *ran* the pickle program and got compromised. This lab **reads** the same
program instruction by instruction, without running any of it — the difference
between reading a recipe and cooking it. This is how `picklescan` and `modelscan`
work under the hood.

## Setup

This lab inspects the poisoned file from Lab 1. Generate one here first:

```powershell
# from this folder, with the venv active
python ..\lab1-pickle-executes-code\create_sample.py
```

That writes `suspicious_model.bin` into the current folder.

## Run

```powershell
python inspect_pickle.py
```

`inspect_pickle.py` uses `pickletools.genops()` to walk every opcode in the file
**without executing it**, printing a disassembly and flagging the opcodes that
import or call a function.

## What to look for

Most opcodes are harmless — `PROTO`, `EMPTY_DICT`, `MARK`, `SHORT_BINUNICODE`
(the layer-name strings), `BINFLOAT` (the tensor numbers). The attack shows up as
a specific sequence:

- `SHORT_BINUNICODE 'posix'` then `'system'`, then **`STACK_GLOBAL`** — "import
  the `system` function from `posix`" (`os.system` on disk becomes `posix.system`
  on Linux / `nt.system` on Windows).
- `SHORT_BINUNICODE 'echo ... > PWNED.txt'` — the argument, in plain text.
- **`REDUCE`** — "call the function on top of the stack with that argument." This
  is the trigger.

The pair **`STACK_GLOBAL` + `REDUCE`** is the classic signature of a pickle
payload. A legitimate model never imports and calls `os` / `posix` / `subprocess`
in the middle of its tensors.

## The limitation (why this is detection, not a guarantee)

This is a **blocklist of known-dangerous modules**. It fails the same way ClamAV
or any signature scanner fails:

- If the attacker reaches the same capability through a module not on the list,
  the scan is clean but the file is not safe.
- If the pickle is packaged so the parser can't disassemble it (e.g. a format
  mismatch like a 7z-wrapped PyTorch file), `genops` may not parse it at all — and
  "didn't parse" must be treated as **suspicious**, never as "clean".

A clean scan means "no known-bad pattern matched," not "safe to load." That's why
Lab 3 removes the whole class of attack with `safetensors`, and Lab 4 treats this
scan as one signal among several.

## Files

| File | Role |
|---|---|
| `inspect_pickle.py` | Disassembles a pickle file and flags import/call opcodes |
