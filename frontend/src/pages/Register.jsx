import { useState, useRef } from "react";
import { registerFace } from "../api";
import { Upload, UserPlus, CheckCircle, XCircle } from "lucide-react";

export default function Register() {
  const [name, setName] = useState("");
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef();

  const handleFile = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setStatus(null);
  };

  const handleSubmit = async () => {
    if (!name.trim() || !file) {
      setStatus({ ok: false, msg: "Please enter a name and select a photo." });
      return;
    }
    setLoading(true);
    try {
      await registerFace(name.trim(), file);
      setStatus({ ok: true, msg: `${name} registered successfully.` });
      setName("");
      setFile(null);
      setPreview(null);
    } catch (e) {
      setStatus({ ok: false, msg: e.response?.data?.error || "Registration failed." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: "1.5rem" }}>
        <h1>Register Face</h1>
        <p className="text-muted" style={{ marginTop: 4 }}>Add a new person to the recognition system</p>
      </div>

      <div style={{ maxWidth: 480 }}>
        <div className="glass" style={{ padding: "2rem", display: "flex", flexDirection: "column", gap: "1.2rem" }}>

          <div>
            <label>Full Name</label>
            <input
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g. yasmin"
            />
          </div>

          {/* Photo upload */}
          <div>
            <label>Face Photo</label>
            <div
              onClick={() => inputRef.current.click()}
              style={{
                border: "1.5px dashed rgba(255,255,255,0.12)",
                borderRadius: 12, padding: "1.5rem",
                textAlign: "center", cursor: "pointer",
                background: "rgba(255,255,255,0.02)",
                transition: "border-color 0.2s",
              }}
            >
              {preview ? (
                <img src={preview} alt="preview" style={{ maxHeight: 180, borderRadius: 8, margin: "0 auto", display: "block" }} />
              ) : (
                <div style={{ color: "#475569" }}>
                  <Upload size={28} style={{ margin: "0 auto 8px", display: "block" }} />
                  <div style={{ fontSize: "0.85rem" }}>Click to upload a clear face photo</div>
                  <div style={{ fontSize: "0.75rem", marginTop: 4 }}>JPG, PNG — one face, good lighting</div>
                </div>
              )}
            </div>
            <input ref={inputRef} type="file" accept="image/*" onChange={handleFile} style={{ display: "none" }} />
          </div>

          {status && (
            <div style={{
              display: "flex", alignItems: "center", gap: 8,
              padding: "0.75rem 1rem", borderRadius: 10,
              background: status.ok ? "rgba(52,211,153,0.1)" : "rgba(239,68,68,0.1)",
              border: `1px solid ${status.ok ? "rgba(52,211,153,0.2)" : "rgba(239,68,68,0.2)"}`,
              fontSize: "0.875rem",
              color: status.ok ? "#34d399" : "#f87171"
            }}>
              {status.ok ? <CheckCircle size={16} /> : <XCircle size={16} />}
              {status.msg}
            </div>
          )}

          <button className="btn btn-primary" onClick={handleSubmit} disabled={loading}
            style={{ justifyContent: "center" }}>
            <UserPlus size={15} />
            {loading ? "Registering..." : "Register Face"}
          </button>
        </div>

        <div className="glass" style={{ padding: "1.2rem", marginTop: "1rem" }}>
          <h2>Tips for best results</h2>
          <ul style={{ fontSize: "0.85rem", color: "#64748b", lineHeight: 1.8, paddingLeft: "1.2rem" }}>
            <li>Use a clear, front-facing photo</li>
            <li>Good even lighting — avoid shadows on face</li>
            <li>Only one face visible in the photo</li>
            <li>Name should match how you want it displayed</li>
          </ul>
        </div>
      </div>
    </div>
  );
}