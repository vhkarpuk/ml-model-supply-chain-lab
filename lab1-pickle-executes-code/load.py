import pickle, os

print("PWNED.txt exists before?", os.path.exists("PWNED.txt"))

with open("suspicious_model.bin", "rb") as f:
    data = pickle.load(f)      # <- the payload runs here

print("PWNED.txt exists after?", os.path.exists("PWNED.txt"))
print("loaded keys:", list(data.keys()))