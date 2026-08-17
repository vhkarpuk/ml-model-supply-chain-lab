import numpy as np
from safetensors.numpy import save_file

# same idea as the Lab 1 model: named tensors with numbers
tensors = {
    "layers.0.attention.query.weight": np.array([0.12, -0.44, 0.98], dtype=np.float32),
    "layers.0.attention.key.weight":   np.array([0.31, 0.07, -0.22], dtype=np.float32),
}

save_file(tensors, "safe_model.safetensors")
print("file created: safe_model.safetensors")