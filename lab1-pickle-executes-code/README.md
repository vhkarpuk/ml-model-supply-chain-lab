# Lab 1 — Prove that pickle executes code

The goal: show that *loading* a model is enough to run attacker code — the victim
never has to do anything but open the file.

> ⚠️ The payload here is harmless: it only writes `PWNED.txt` via `echo`.

## Step 1 — Build the poisoned model

```powershell
python create_sample.py
```

`create_sample.py` plays the **attacker**: it defines a class whose `__reduce__`
returns `(os.system, ("echo ... > PWNED.txt",))`, hides an instance of it inside
a dictionary that mimics a real model `state_dict`, and serializes everything to
`suspicious_model.bin`. At this point nothing malicious has run — the command is
only *written* into the file, waiting.

## Step 2 — Load it (the payload fires here)

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

## Why this matters

The victim never *chose* to run anything. `load.py` contains no reference to the
attack — it just wanted the model. But **"load the model" and "run the payload"
are the same operation** in pickle; you can't do one without the other. You can't
fix this by telling developers to "be careful when loading" — loading *is* the
risk.

The fix has to come earlier:

- **Prefer `safetensors`** — a format that stores only tensors, with no ability
  to execute code (see Lab 3).
- **When pickle is unavoidable**, load with `torch.load(..., weights_only=True)`
  or a custom unpickler allowlist, and load inside a sandbox with no network and
  no credentials.
- **Static scanners** read the file without running it (see Lab 2) — one signal,
  not a guarantee.

## Files

| File | Role |
|---|---|
| `create_sample.py` | Attacker — builds the poisoned `.bin` |
| `load.py` | Victim — loads it, triggering the payload |
