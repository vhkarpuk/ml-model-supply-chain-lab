# ML Model Supply-Chain Security Lab

A hands-on lab series on why loading a machine-learning model can execute
arbitrary code — and how to detect and defend against it.

> ⚠️ **Educational security lab.** Some labs intentionally build a model file
> that runs a command when loaded. The "payload" is deliberately harmless — it
> only writes a marker file (`PWNED.txt`) via `echo`. Nothing here touches the
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
| **`__reduce__`** | The official hook where an object tells pickle how to rebuild itself. Abused to say "rebuild me by calling `os.system`." |

## Labs

| # | Lab | What it shows |
|---|---|---|
| 1 | [Pickle executes code](lab1-pickle-executes-code/) | Loading a model runs an embedded command — silently. |
| 2 | [Detect without executing](lab2-detect-without-executing/) | Read the opcodes and find the payload *without* running it. |
| 3 | Safetensors (planned) | A format that stores only tensors, immune by design. |
| 4 | Triage scanner (planned) | A tiered scanner for downloaded model repos. |

## Setup

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Each lab folder has its own README with steps.

## Disclaimer

For educational and defensive security research only. Do not adapt the technique
against systems you don't own or aren't authorized to test.