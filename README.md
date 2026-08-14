# ML Model Supply-Chain Security Lab

A hands-on lab demonstrating why loading a machine-learning model can execute
arbitrary code — and why the file format matters more than any scanner.

> ⚠️ **Educational security lab.** This repository intentionally builds a model
> file that runs a command when loaded. The "payload" is deliberately harmless —
> it only writes a marker file (`PWNED.txt`) via `echo`. Nothing here touches the
> network, credentials, or any file outside the lab folder. It exists to teach
> defenders how the attack works so they can block it.

## The one-sentence problem

A machine-learning model is just a large pile of numbers (tensors). But the most
common way to save PyTorch models — Python's **pickle** format — doesn't store
data, it stores *instructions to rebuild the object*. Those instructions can
include "import `os` and run this command." So loading an untrusted `.bin` is
roughly equivalent to running an untrusted executable.

## Background

| Concept | In one line |
|---|---|
| **Tensor** | An N-dimensional array of numbers. A model is millions of these. |
| **PyTorch** | The library that reads those tensors and runs the model. |
| **Serialization** | Flattening an in-memory object into bytes on disk. |
| **Pickle** | Python's native serialization. Stores *rebuild instructions*, not just data — so it can call any function on load. |
| **`__reduce__`** | The official hook where an object tells pickle how to rebuild itself. Abused here to say "rebuild me by calling `os.system`." |

The danger is **not** what the model *is* (numbers) — it's what the file *tells
the loader to do* while rebuilding it.

## Lab 1 — Prove that pickle executes code

### Setup

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Step 1 — Build the poisoned model

```powershell
python create_sample.py
```

`create_sample.py` plays the **attacker**: it defines a class whose `__reduce__`
returns `(os.system, ("echo ... > PWNED.txt",))`, hides an instance of it inside
a dictionary that mimics a real model `state_dict`, and serializes everything to
`suspicious_model.bin`. At this point nothing malicious has run — the command is
only *written* into the file, waiting.

### Step 2 — Load it (the payload fires here)

```powershell
python load.py
```

`load.py` plays the **victim**: it does nothing but `pickle.load()` the file —
the same thing `torch.load()` does under the hood. Expected output:

```
PWNED.txt exists before? False
PWNED.txt exists after? True
loaded keys: ['layers.0.attention.query.weight', 'layers.0.attention.key.weight', '__metadata__']
```

The marker file appeared, and the model loaded **completely and correctly**. No
error, no warning. That silence is the point.

## Why this matters (defender's view)

The victim never *chose* to run anything. `load.py` contains no reference to the
attack — it just wanted the model. But **"load the model" and "run the payload"
are the same operation** in pickle; you can't do one without the other. You can't
fix this by telling developers to "be careful when loading" — loading *is* the
risk.

The fix has to come earlier:

- **Prefer `safetensors`** — a format that stores only tensors, with no ability
  to execute code. There is no `REDUCE` opcode to hide a payload in.
- **When pickle is unavoidable**, load with `torch.load(..., weights_only=True)`
  or a custom unpickler allowlist, and load inside a sandbox with no network and
  no credentials.
- **Static scanners** (`picklescan`, `modelscan`) are one signal, not a
  guarantee — they're signature-based and have documented bypasses. A clean scan
  means "no known-bad pattern matched," not "safe to load."

## Files

| File | Role |
|---|---|
| `create_sample.py` | Attacker — builds the poisoned `.bin` |
| `load.py` | Victim — loads it, triggering the payload |

## Roadmap

- [x] **Lab 1** — Prove pickle executes code on load
- [ ] **Lab 2** — Read the opcodes *without* executing (static detection)
- [ ] **Lab 3** — Inspect a `safetensors` file and see why it's immune
- [ ] **Lab 4** — A tiered triage scanner for downloaded model repos

## Disclaimer

For educational and defensive security research only. Do not adapt the technique
against systems you don't own or aren't authorized to test.
