import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import AttendanceLog from "./pages/AttendanceLog";
import Register from "./pages/Register";
import { LayoutDashboard, ClipboardList, UserPlus, Scan } from "lucide-react";

const NAV = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "log",       label: "Attendance", icon: ClipboardList },
  { id: "register",  label: "Register",   icon: UserPlus },
];

export default function App() {
  const [page, setPage] = useState("dashboard");

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      {/* Sidebar */}
      <aside style={{
        width: 220, padding: "1.5rem 1rem",
        background: "rgba(255,255,255,0.03)",
        backdropFilter: "blur(20px)",
        borderRight: "1px solid rgba(255,255,255,0.07)",
        display: "flex", flexDirection: "column", gap: 4,
        position: "fixed", top: 0, left: 0, bottom: 0
      }}>
        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: "2rem", padding: "0 0.5rem" }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 4px 15px rgba(99,102,241,0.4)"
          }}>
            <Scan size={18} color="white" />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: "0.9rem" }}>FaceAttend</div>
            <div style={{ fontSize: "0.68rem", color: "#64748b" }}>Recognition System</div>
          </div>
        </div>

        {NAV.map(({ id, label, icon: Icon }) => (
          <button key={id} onClick={() => setPage(id)} style={{
            display: "flex", alignItems: "center", gap: 10,
            padding: "0.65rem 0.9rem", borderRadius: 10, border: "none",
            background: page === id ? "rgba(99,102,241,0.15)" : "transparent",
            color: page === id ? "#a5b4fc" : "#64748b",
            fontWeight: 500, fontSize: "0.875rem", cursor: "pointer",
            transition: "all 0.15s", width: "100%", textAlign: "left",
            borderLeft: page === id ? "2px solid #6366f1" : "2px solid transparent"
          }}>
            <Icon size={16} />
            {label}
          </button>
        ))}
      </aside>

      {/* Main */}
      <main style={{ marginLeft: 220, flex: 1, padding: "2rem", minHeight: "100vh" }}>
        {page === "dashboard" && <Dashboard />}
        {page === "log"       && <AttendanceLog />}
        {page === "register"  && <Register />}
      </main>
    </div>
  );
}