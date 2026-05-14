"""
Step 3 — Run live attendance recognition.
Pure ONNX inference — no PyTorch at runtime.
Press Q to quit.
"""
import cv2
import json
import sqlite3
import numpy as np
import onnxruntime as ort
from datetime import datetime
import os

MODEL_PATH = "models/facenet.onnx"
EMBEDDINGS_PATH = "data/embeddings.json"
DB_PATH = "outputs/attendance.db"
SIMILARITY_THRESHOLD = 0.72
os.makedirs("outputs", exist_ok=True)

FACE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


# ---------- DB ----------

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            confidence REAL
        )
    """)
    conn.commit()
    conn.close()


def log_attendance(name, confidence):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO attendance (name, timestamp, confidence) VALUES (?, ?, ?)",
        (name, datetime.now().isoformat(), round(float(confidence), 4))
    )
    conn.commit()
    conn.close()


def already_logged_today(name):
    """Prevent duplicate entries for the same person on the same day."""
    conn = sqlite3.connect(DB_PATH)
    today = datetime.now().strftime("%Y-%m-%d")
    row = conn.execute(
        "SELECT id FROM attendance WHERE name = ? AND timestamp LIKE ?",
        (name, f"{today}%")
    ).fetchone()
    conn.close()
    return row is not None


# ---------- Preprocessing ----------

def preprocess_face(face_bgr, target_size=(160, 160)):
    face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
    face_resized = cv2.resize(face_rgb, target_size)
    face_norm = (face_resized.astype(np.float32) / 127.5) - 1.0
    return np.transpose(face_norm, (2, 0, 1))[np.newaxis, :]


def get_embedding(session, face_tensor):
    output = session.run(["embeddings"], {"input": face_tensor})[0]
    emb = output[0]
    return emb / np.linalg.norm(emb)


def cosine_similarity(a, b):
    return float(np.dot(a, b))


# ---------- Recognition ----------

def identify(embedding, known_embeddings):
    best_name = "Unknown"
    best_score = -1.0
    for name, known_emb in known_embeddings.items():
        score = cosine_similarity(embedding, np.array(known_emb))
        if score > best_score:
            best_score = score
            best_name = name
    if best_score < SIMILARITY_THRESHOLD:
        return "Unknown", best_score
    return best_name, best_score


# ---------- Main loop ----------

def run():
    if not os.path.exists(MODEL_PATH):
        print("[Attendance] ONNX model not found. Run export_onnx.py first.")
        return
    if not os.path.exists(EMBEDDINGS_PATH):
        print("[Attendance] Embeddings not found. Run register.py first.")
        return

    session = ort.InferenceSession(MODEL_PATH)

    with open(EMBEDDINGS_PATH) as f:
        known_embeddings = json.load(f)

    print(f"[Attendance] Loaded {len(known_embeddings)} registered face(s).")
    print("[Attendance] Starting webcam. Press Q to quit.")

    init_db()
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("[Attendance] Could not open webcam.")
        return

    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        # Run recognition every 5 frames — reduces CPU load
        if frame_count % 5 == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = FACE_CASCADE.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
            )

            for (x, y, w, h) in faces:
                face_crop = frame[y:y+h, x:x+w]
                if face_crop.size == 0:
                    continue

                face_tensor = preprocess_face(face_crop)
                embedding = get_embedding(session, face_tensor)
                name, score = identify(embedding, known_embeddings)

                # Log attendance (once per person per day)
                if name != "Unknown" and not already_logged_today(name):
                    log_attendance(name, score)
                    print(f"[Attendance] Logged: {name} ({score:.3f})")

                # Draw box and label
                color = (0, 255, 0) if name != "Unknown" else (100, 100, 100)
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                label = f"{name} ({score:.2f})"
                cv2.putText(frame, label, (x, y - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1)

        cv2.imshow("Face Recognition Attendance", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[Attendance] Session ended.")


if __name__ == "__main__":
    run()