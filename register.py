"""
Step 2 — Register known faces.
Reads images from known_faces/, extracts FaceNet embeddings via ONNX,
saves to data/embeddings.json.

Naming convention: known_faces/yasmin.jpg → label "yasmin"
"""
import os
import json
import cv2
import numpy as np
import onnxruntime as ort
from PIL import Image

KNOWN_FACES_DIR = "known_faces"
EMBEDDINGS_PATH = "data/embeddings.json"
MODEL_PATH = "models/facenet.onnx"
os.makedirs("data", exist_ok=True)

FACE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def preprocess_face(img_bgr, target_size=(160, 160)):
    """Crop, resize, and normalise a face region for FaceNet input."""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    faces = FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    if len(faces) == 0:
        # No face detected — use full image
        face_img = img_bgr
    else:
        x, y, w, h = faces[0]
        # Add padding
        pad = int(0.2 * min(w, h))
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(img_bgr.shape[1], x + w + pad)
        y2 = min(img_bgr.shape[0], y + h + pad)
        face_img = img_bgr[y1:y2, x1:x2]

    face_rgb = cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB)
    face_resized = cv2.resize(face_rgb, target_size)

    # Normalise to [-1, 1] — FaceNet convention
    face_norm = (face_resized.astype(np.float32) / 127.5) - 1.0

    # (H, W, C) → (1, C, H, W)
    return np.transpose(face_norm, (2, 0, 1))[np.newaxis, :]


def get_embedding(session, face_tensor):
    output = session.run(["embeddings"], {"input": face_tensor})[0]
    emb = output[0]
    # L2 normalise
    return emb / np.linalg.norm(emb)


def register():
    if not os.path.exists(MODEL_PATH):
        print(f"[Register] ONNX model not found at {MODEL_PATH}.")
        print("[Register] Run export_onnx.py first.")
        return

    session = ort.InferenceSession(MODEL_PATH)
    embeddings = {}

    for filename in os.listdir(KNOWN_FACES_DIR):
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        name = os.path.splitext(filename)[0]
        path = os.path.join(KNOWN_FACES_DIR, filename)
        img = cv2.imread(path)
        if img is None:
            print(f"[Register] Could not read {path}, skipping.")
            continue

        face_tensor = preprocess_face(img)
        embedding = get_embedding(session, face_tensor)
        embeddings[name] = embedding.tolist()
        print(f"[Register] Registered: {name}")

    with open(EMBEDDINGS_PATH, "w") as f:
        json.dump(embeddings, f)

    print(f"[Register] Saved {len(embeddings)} embeddings to {EMBEDDINGS_PATH}")


if __name__ == "__main__":
    register()