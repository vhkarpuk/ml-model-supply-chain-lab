#!/usr/bin/env python3
"""
Triage scanner for downloaded model repositories.

Walks a folder and classifies it into a tier:
  TIER 1 - auto-approve      (safe format, no red flags)
  TIER 2 - manual review     (pickle, unknown provenance, dependencies)
  TIER 3 - escalate/reject   (payload found, remote code, python in repo)

This mirrors a package-approval pipeline, with model-specific controls.
It is a STARTING POINT: several gaps are left in on purpose (see the README).
"""
import sys, io, json, zipfile, pickletools
from pathlib import Path

# --- format buckets --------------------------------------------------------
PICKLE_EXT = {".bin", ".pt", ".pth", ".ckpt", ".pkl", ".joblib", ".h5"}
SAFE_EXT   = {".safetensors", ".gguf", ".onnx"}
DATA_EXT   = {".parquet", ".arrow", ".jsonl", ".csv"}

# --- modules that mean "this pickle can run code" --------------------------
DANGEROUS = {
    "os", "nt", "posix", "subprocess", "sys", "socket", "shutil",
    "importlib", "runpy", "pty", "webbrowser", "builtins", "__builtin__",
    "commands", "pickle", "code", "codeop", "timeit", "pdb", "bdb",
}


def scan_pickle_opcodes(raw: bytes):
    """Read opcodes WITHOUT executing. Return list of (opcode, target)."""
    hits = []
    try:
        for op, arg, _ in pickletools.genops(io.BytesIO(raw)):
            if op.name in ("GLOBAL", "STACK_GLOBAL"):
                target = str(arg) if arg else ""
                module = target.split()[0].split(".")[0] if target else "?"
                if module in DANGEROUS:
                    hits.append((op.name, target))
            elif op.name == "REDUCE":
                hits.append(("REDUCE", "call on top of stack"))
    except Exception as e:
        # GAP: a file we cannot parse is treated as a finding, but not critical.
        hits.append(("PARSE_ERROR", str(e)))
    return hits


def analyze_pickle_file(path: Path):
    """A PyTorch .bin is often a ZIP containing data.pkl."""
    hits = []
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                if name.endswith(".pkl") or "data.pkl" in name:
                    hits += scan_pickle_opcodes(z.read(name))
    else:
        hits += scan_pickle_opcodes(path.read_bytes())
    return hits


def triage(folder: str):
    base = Path(folder)
    if not base.is_dir():
        sys.exit(f"not a folder: {folder}")

    findings = []
    has_safetensors = False
    has_pickle = False

    for f in sorted(base.rglob("*")):
        if not f.is_file():
            continue
        ext = f.suffix.lower()

        if ext in SAFE_EXT:
            has_safetensors = True
            findings.append(("INFO", f.name, "safe format (no code execution on load)"))

        elif ext in PICKLE_EXT:
            has_pickle = True
            hits = analyze_pickle_file(f)
            dangerous = [h for h in hits if h[0] != "PARSE_ERROR"]
            if dangerous:
                findings.append(("CRITICAL", f.name,
                                 f"dangerous opcodes: {dangerous[:3]}"))
            elif hits:  # only parse errors
                findings.append(("WARNING", f.name, f"could not parse: {hits}"))
            else:
                findings.append(("WARNING", f.name,
                                 "pickle format (executes on load)"))

        elif ext == ".py":
            findings.append(("CRITICAL", f.name, "python code in repository"))

        elif f.name == "config.json":
            try:
                cfg = json.loads(f.read_text(encoding="utf-8"))
                if "auto_map" in cfg:
                    findings.append(("CRITICAL", f.name,
                                     f"auto_map -> requires trust_remote_code: "
                                     f"{cfg['auto_map']}"))
            except Exception as e:
                findings.append(("WARNING", f.name, f"unreadable config: {e}"))

        elif f.name in ("requirements.txt", "setup.py", "pyproject.toml"):
            findings.append(("WARNING", f.name, "installs dependencies"))

        elif ext in DATA_EXT:
            findings.append(("INFO", f.name, "data file (no execution)"))

    if has_pickle and has_safetensors:
        findings.append(("INFO", "-", "safetensors available: force its use"))
    if has_pickle and not has_safetensors:
        findings.append(("WARNING", "-", "no safetensors alternative"))

    levels = {lvl for lvl, _, _ in findings}
    tier = ("TIER 3 - escalate/reject" if "CRITICAL" in levels else
            "TIER 2 - manual review"   if "WARNING"  in levels else
            "TIER 1 - auto-approve")

    print(f"\n=== triage: {base} ===")
    if not findings:
        print("  (no files found)")
    order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
    for lvl, name, reason in sorted(findings, key=lambda x: order[x[0]]):
        print(f"  [{lvl:<8}] {name:<28} {reason}")
    print(f"\n  >> {tier}\n")
    return tier


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python triage.py <model_folder>")
    triage(sys.argv[1])