import pickletools

TARGET = "suspicious_model.bin"

# opcodes that import/call a function -- the heart of a payload
INTERESTING = {"GLOBAL", "STACK_GLOBAL", "REDUCE", "INST", "OBJ", "NEWOBJ"}

print(f"--- disassembly of {TARGET} ---\n")

flagged = []
with open(TARGET, "rb") as f:
    for opcode, arg, pos in pickletools.genops(f):
        mark = "  <== SUSPICIOUS" if opcode.name in INTERESTING else ""
        print(f"[{pos:>4}] {opcode.name:<16} {arg}{mark}")
        if opcode.name in INTERESTING:
            flagged.append((opcode.name, arg))

print(f"\n--- summary ---")
if flagged:
    print(f"{len(flagged)} suspicious opcode(s) found:")
    for name, arg in flagged:
        print(f"  {name}: {arg}")
else:
    print("no import/call opcodes found.")
