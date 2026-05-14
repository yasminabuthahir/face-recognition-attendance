import { useEffect, useState, useRef } from "react";
import api, { getStreamUrl, getDetections, getSummary, getToday } from "../api";
import { Users, UserCheck, Activity, Clock } from "lucide-react";

function StatCard({ icon: Icon, label, value, color, glow }) {
  return (
    <div className={`glass ${glow}`} style={{ padding: "1.4rem", display: "flex", alignItems: "center", gap: 16 }}>
      <div style={{
        width: 48, height: 48, borderRadius: 12,
        background: `${color}18`,
        display: "flex", alignItems: "center", justifyContent: "center",
        border: `1px solid ${color}30`
      }}>
        <Icon size={22} color={color} />
      </div>
      <div>
        <div style={{ fontSize: "0.75rem", color: "#64748b", marginBottom: 2, textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</div>
        <div style={{ fontSize: "1.8rem", fontWeight: 700, letterSpacing: "-0.02em" }}>{value}</div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [summary, setSummary] = useState({ total_records: 0, unique_people: 0 });
  const [today, setToday] = useState({ count: 0, records: [] });
  const [detections, setDetections] = useState([]);
  const [camInfo, setCamInfo] = useState(null);
  const streamUrl = getStreamUrl();

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [s, t, d, ci] = await Promise.all([
          getSummary(), getToday(), getDetections(), api.get("/camera/info")
        ]);
        setSummary(s.data);
        setToday(t.data);
        setDetections(d.data.detections || []);
        setCamInfo(ci.data);
      } catch {}
    };
    fetchAll();
    const interval = setInterval(fetchAll, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <div style={{ marginBottom: "1.5rem" }}>
        <h1>Dashboard</h1>
        <p className="text-muted" style={{ marginTop: 4 }}>Live face recognition attendance</p>
      </div>

      {/* Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "1rem", marginBottom: "1.5rem" }}>
        <StatCard icon={UserCheck} label="Today" value={today.count} color="#34d399" glow="glow-green" />
        <StatCard icon={Users} label="Total Records" value={summary.total_records} color="#6366f1" glow="glow-blue" />
        <StatCard icon={Activity} label="Registered" value={summary.unique_people} color="#a78bfa" glow="" />
        <StatCard icon={Clock} label="Faces in Frame" value={detections.length} color="#f59e0b" glow="" />
      </div>

      {/* Live feed + today's log */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 380px", gap: "1.5rem" }}>

        {/* Live feed */}
        <div className="glass" style={{ padding: "1.2rem" }}>
        <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#34d399", boxShadow: "0 0 8px #34d399" }} />
              <h2 style={{ marginBottom: 0 }}>Live Feed</h2>
            </div>
            <span className="badge badge-blue">{camInfo?.type || "camera"}</span>
          </div>
          <img
            src={streamUrl}
            alt="Live feed"
            style={{ width: "100%", borderRadius: 10, border: "1px solid rgba(255,255,255,0.08)", display: "block" }}
            onError={e => { e.target.style.display = "none"; }}
          />
          {detections.length > 0 && (
            <div style={{ marginTop: "1rem", display: "flex", flexWrap: "wrap", gap: 8 }}>
              {detections.map((d, i) => (
                <span key={i} className={`badge ${d.name !== "Unknown" ? "badge-green" : "badge-gray"}`}>
                  {d.name} {(d.score * 100).toFixed(0)}%
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Today's log */}
        <div className="glass" style={{ padding: "1.2rem", overflowY: "auto", maxHeight: 520 }}>
          <h2>Today's Attendance</h2>
          {today.records.length === 0 ? (
            <p className="text-muted">No attendance logged today.</p>
          ) : (
            today.records.map(r => (
              <div key={r.id} style={{
                display: "flex", justifyContent: "space-between", alignItems: "center",
                padding: "0.65rem 0", borderBottom: "1px solid rgba(255,255,255,0.05)"
              }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>{r.name}</div>
                  <div style={{ fontSize: "0.75rem", color: "#475569" }}>
                    {new Date(r.timestamp).toLocaleTimeString()}
                  </div>
                </div>
                <span className="badge badge-blue">{(r.confidence * 100).toFixed(0)}%</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}