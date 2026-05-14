import sqlite3
import os
import cv2
import json
import numpy as np
import onnxruntime as ort
from datetime import datetime
from fastapi import FastAPI, Query, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import threading
import time

DB_PATH = "outputs/attendance.db"
MODEL_PATH = "models/facenet.onnx"
EMBEDDINGS_PATH = "data/embeddings.json"
KNOWN_FACES_DIR = "known_faces"
import json as _json_cfg
try:
    with open("config.json") as _f:
        _cfg_data = _json_cfg.load(_f)
    SIMILARITY_THRESHOLD = _cfg_data["recognition"]["similarity_threshold"]
except:
    SIMILARITY_THRESHOLD = 0.72

app = FastAPI(title="Face Recognition Attendance System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Shared state ----------
_session = None
_known_embeddings = {}
_cap = None
_latest_frame = None
_frame_lock = threading.Lock()
_detections = []
stop_event = threading.Event()
camera_thread = None

def get_session():
    global _session
    if _session is None and os.path.exists(MODEL_PATH):
        _session = ort.InferenceSession(MODEL_PATH)
    return _session


def load_embeddings():
    global _known_embeddings
    if os.path.exists(EMBEDDINGS_PATH):
        with open(EMBEDDINGS_PATH) as f:
            _known_embeddings = json.load(f)


FACE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def preprocess_face(face_bgr):
    face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
    face_resized = cv2.resize(face_rgb, (160, 160))
    face_norm = (face_resized.astype(np.float32) / 127.5) - 1.0
    return np.transpose(face_norm, (2, 0, 1))[np.newaxis, :]


def get_embedding(face_tensor):
    session = get_session()
    if session is None:
        return None
    output = session.run(["embeddings"], {"input": face_tensor})[0]
    emb = output[0]
    return emb / np.linalg.norm(emb)


def cosine_similarity(a, b):
    return float(np.dot(a, b))


def identify(embedding):
    best_name = "Unknown"
    best_score = -1.0
    for name, known_emb in _known_embeddings.items():
        score = cosine_similarity(embedding, np.array(known_emb))
        if score > best_score:
            best_score = score
            best_name = name
    if best_score < SIMILARITY_THRESHOLD:
        return "Unknown", best_score
    return best_name, best_score


def already_logged_today(name):
    if not os.path.exists(DB_PATH):
        return False
    conn = sqlite3.connect(DB_PATH)
    today = datetime.now().strftime("%Y-%m-%d")
    row = conn.execute(
        "SELECT id FROM attendance WHERE name = ? AND timestamp LIKE ?",
        (name, f"{today}%")
    ).fetchone()
    conn.close()
    return row is not None


def log_attendance(name, confidence):
    os.makedirs("outputs", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, timestamp TEXT, confidence REAL)"
    )
    conn.execute(
        "INSERT INTO attendance (name, timestamp, confidence) VALUES (?, ?, ?)",
        (name, datetime.now().isoformat(), round(float(confidence), 4))
    )
    conn.commit()
    conn.close()


def camera_loop():
    global _cap, _latest_frame, _detections
    import json as _json
    with open("config.json") as _f:
        _cfg = _json.load(_f)
    _src = _cfg["camera"]["source"]
    src = _src if isinstance(_src, int) else str(_src)
    _cap = cv2.VideoCapture(src)
    print(f"[Camera] Opened source: {_src}")
    frame_count = 0

    while not stop_event.is_set():
        ret, frame = _cap.read()
        if not ret:
            # Loop video files back to start
            _cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            time.sleep(0.05)
            continue

        frame_count += 1
        if frame_count % 5 == 0 and _known_embeddings:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = FACE_CASCADE.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
            )
            current_detections = []
            for (x, y, w, h) in faces:
                face_crop = frame[y:y+h, x:x+w]
                if face_crop.size == 0:
                    continue
                face_tensor = preprocess_face(face_crop)
                embedding = get_embedding(face_tensor)
                if embedding is None:
                    continue
                name, score = identify(embedding)
                if name != "Unknown" and not already_logged_today(name):
                    log_attendance(name, score)
                current_detections.append({
                    "x": int(x), "y": int(y),
                    "w": int(w), "h": int(h),
                    "name": name, "score": round(score, 3)
                })

                color = (0, 255, 120) if name != "Unknown" else (120, 120, 120)
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                cv2.putText(frame, f"{name} {score:.2f}", (x, y - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1)

            _detections = current_detections

        with _frame_lock:
            _latest_frame = frame.copy()

        time.sleep(0.01)

@app.on_event("startup")
def startup():
    load_embeddings()
    global camera_thread

    camera_thread = threading.Thread(target=camera_loop)
    camera_thread.start()

@app.on_event("shutdown")
def shutdown():
    print("\n[Server] Shutting down gracefully...")

    stop_event.set()

    global camera_thread
    global _cap

    if camera_thread is not None:
        camera_thread.join(timeout=5)

    if _cap is not None:
        _cap.release()

    cv2.destroyAllWindows()

    print("[Server] Cleanup complete.")
# ---------- Video stream ----------

def generate_frames():
    while True:
        with _frame_lock:
            frame = _latest_frame.copy() if _latest_frame is not None else None
        if frame is None:
            time.sleep(0.05)
            continue
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            buffer.tobytes() +
            b"\r\n"
        )
        time.sleep(0.033)  # ~30fps


@app.get("/video_feed")
def video_feed():
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/camera/info")
def camera_info():
    try:
        with open("config.json") as f:
            cfg = json.load(f)
        src = cfg["camera"]["source"]
        if src == 0 or src == "0":
            src_type = "webcam"
        elif str(src).startswith("rtsp"):
            src_type = "rtsp"
        else:
            src_type = "video_file"
        return {"source": src, "type": src_type, "name": cfg["camera"]["name"]}
    except:
        return {"source": "unknown", "type": "unknown", "name": "Camera"}
# ---------- Detections ----------

@app.get("/detections")
def get_detections():
    return {"detections": _detections}


# ---------- Attendance ----------

def get_records(name_filter=None, date_filter=None, limit=100):
    if not os.path.exists(DB_PATH):
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, timestamp TEXT, confidence REAL)"
    )
    query = "SELECT id, name, timestamp, confidence FROM attendance"
    params = []
    conditions = []
    if name_filter:
        conditions.append("name LIKE ?")
        params.append(f"%{name_filter}%")
    if date_filter:
        conditions.append("timestamp LIKE ?")
        params.append(f"{date_filter}%")
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [
        {"id": r[0], "name": r[1], "timestamp": r[2], "confidence": r[3]}
        for r in rows
    ]


@app.get("/")
def root():
    return {"message": "Face Recognition Attendance API running"}


@app.get("/attendance")
def get_attendance(
    name: str = Query(None),
    date: str = Query(None),
    limit: int = Query(100, le=500)
):
    records = get_records(name, date, limit)
    return JSONResponse(content={"count": len(records), "records": records})


@app.get("/attendance/today")
def get_today():
    today = datetime.now().strftime("%Y-%m-%d")
    records = get_records(date_filter=today)
    return JSONResponse(content={"date": today, "count": len(records), "records": records})


@app.get("/attendance/summary")
def get_summary():
    if not os.path.exists(DB_PATH):
        return {"total_records": 0, "unique_people": 0}
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, timestamp TEXT, confidence REAL)"
    )
    total = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
    unique = conn.execute("SELECT COUNT(DISTINCT name) FROM attendance").fetchone()[0]
    conn.close()
    return {"total_records": total, "unique_people": unique}


# ---------- Register face ----------

@app.post("/register")
async def register_face(name: str, file: UploadFile = File(...)):
    os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return JSONResponse(status_code=400, content={"error": "Invalid image"})

    path = os.path.join(KNOWN_FACES_DIR, f"{name}.jpg")
    cv2.imwrite(path, img)

    # Re-run registration for this face only
    session = get_session()
    if session is None:
        return JSONResponse(status_code=503, content={"error": "Model not loaded"})

    face_tensor = preprocess_face(img)
    embedding = get_embedding(face_tensor)
    _known_embeddings[name] = embedding.tolist()

    with open(EMBEDDINGS_PATH, "w") as f:
        json.dump(_known_embeddings, f)

    return {"message": f"Registered {name} successfully"}