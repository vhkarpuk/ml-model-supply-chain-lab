import struct, json
 
TARGET = "safe_model.safetensors"
 
with open(TARGET, "rb") as f:
    # first 8 bytes = header length (little-endian unsigned 64-bit)
    header_len = struct.unpack("<Q", f.read(8))[0]
    # next header_len bytes = the JSON header
    header = json.loads(f.read(header_len))
 
print(f"--- header of {TARGET} ---\n")
print(json.dumps(header, indent=2))
 
print(f"\n--- what this means ---")
print("The header is plain JSON: only names, dtypes, shapes, byte offsets.")
print("There is no opcode, no GLOBAL, no REDUCE -- nothing to execute.")
print("Everything after the header is raw numbers at fixed positions.")
