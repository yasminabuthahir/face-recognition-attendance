"""
Step 1 — Run this once to export FaceNet from PyTorch to ONNX.
After this, PyTorch is no longer needed at runtime.
"""
import os
import torch
import numpy as np
import onnx
import onnxruntime as ort
from facenet_pytorch import InceptionResnetV1

OUTPUT_PATH = "models/facenet.onnx"
os.makedirs("models", exist_ok=True)


def export():
    print("[Export] Loading FaceNet (PyTorch)...")
    model = InceptionResnetV1(pretrained="vggface2").eval()

    # FaceNet expects (batch, 3, 160, 160) normalised to [-1, 1]
    dummy_input = torch.randn(1, 3, 160, 160)

    print(f"[Export] Exporting to {OUTPUT_PATH}...")
    torch.onnx.export(
        model,
        dummy_input,
        OUTPUT_PATH,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["embeddings"],
        dynamic_axes={
            "input": {0: "batch_size"},
            "embeddings": {0: "batch_size"}
        }
    )

    # Verify ONNX model is valid
    print("[Export] Verifying ONNX model...")
    onnx_model = onnx.load(OUTPUT_PATH)
    onnx.checker.check_model(onnx_model)
    print("[Export] ONNX model valid.")

    # Cross-check PyTorch vs ONNX output
    print("[Export] Cross-checking PyTorch vs ONNX output...")
    with torch.no_grad():
        pt_output = model(dummy_input).numpy()

    session = ort.InferenceSession(OUTPUT_PATH)
    ort_output = session.run(["embeddings"], {"input": dummy_input.numpy()})[0]

    max_diff = np.max(np.abs(pt_output - ort_output))
    print(f"[Export] Max output difference PyTorch vs ONNX: {max_diff:.6f}")
    assert max_diff < 1e-4, "Outputs differ too much — check export settings"
    print(f"[Export] Done. Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    export()