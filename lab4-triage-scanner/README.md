# Lab 4 — A tiered triage scanner

Labs 1–3 explained the problem, the detection, and the fix. This lab turns those
lessons into a tool: `triage.py` takes a downloaded model folder and returns a
decision.

| Tier | Meaning |
|---|---|
| **TIER 1** | auto-approve — safe format, no red flags |
| **TIER 2** | manual review — pickle, dependencies, unknown provenance |
| **TIER 3** | escalate/reject — payload found, remote code, or `.py` in the repo |

It mirrors a package-approval pipeline, with model-specific controls swapped in.

## Run

```powershell
python triage.py <path-to-model-folder>
```

## What it checks

- **Format** — `safetensors` is a safe finding; pickle (`.bin`, `.pt`, `.ckpt`…)
  is at least a WARNING because it executes on load (Lab 1).
- **Opcodes** — for pickle files, it reads the opcodes without executing (Lab 2)
  and flags `GLOBAL`/`STACK_GLOBAL` into dangerous modules, plus `REDUCE`.
- **Remote code** — `auto_map` in `config.json` (forces `trust_remote_code`) and
  any `.py` in the repo are CRITICAL.
- **Dependencies** — `requirements.txt` / `setup.py` are a WARNING.
- **Safetensors available** — if both formats ship, it says to force the safe one.

The worst finding sets the tier.

## Intentional gaps (the exercise)

This scanner is a **starting point**, not a finished control. The following holes
are left in on purpose — fixing each is a commit with real security reasoning:

1. **PARSE_ERROR is not CRITICAL.** A file the parser can't read is treated as a
   WARNING. But "can't parse" is exactly the nullifAI / 7z bypass — the scanner
   being blind is not the same as the file being clean. It should escalate.
2. **Blocklist, not allowlist.** `DANGEROUS` lists known-bad modules. Anything not
   on the list slips through. An allowlist of known-good modules is safer.
3. **No provenance checks.** Publisher, verified org, commit pinning, license —
   none are checked, because they live in the Hugging Face API or the request
   form, not in the files.
4. **No sandbox.** This is pure static analysis. It cannot catch a payload that
   reaches its capability through a path the opcode scan doesn't recognize. A
   one-time load in a no-network, no-credential container is the missing layer.

A clean result here means "no known-bad pattern matched," never "safe to load."

## Files

| File | Role |
|---|---|
| `triage.py` | Walks a model folder and assigns a tier |
