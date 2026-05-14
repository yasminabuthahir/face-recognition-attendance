import { useEffect, useState } from "react";
import { getAttendance } from "../api";
import { Search, Filter } from "lucide-react";

export default function AttendanceLog() {
  const [records, setRecords] = useState([]);
  const [nameFilter, setNameFilter] = useState("");
  const [dateFilter, setDateFilter] = useState("");

  const fetchRecords = async () => {
    try {
      const params = {};
      if (nameFilter) params.name = nameFilter;
      if (dateFilter) params.date = dateFilter;
      const res = await getAttendance(params);
      setRecords(res.data.records);
    } catch {}
  };

  useEffect(() => { fetchRecords(); }, []);

  return (
    <div>
      <div style={{ marginBottom: "1.5rem" }}>
        <h1>Attendance Log</h1>
        <p className="text-muted" style={{ marginTop: 4 }}>Full history of all attendance records</p>
      </div>

      {/* Filters */}
      <div className="glass" style={{ padding: "1rem 1.2rem", marginBottom: "1rem", display: "flex", gap: "1rem", alignItems: "flex-end" }}>
        <div style={{ flex: 1 }}>
          <label>Search by name</label>
          <input value={nameFilter} onChange={e => setNameFilter(e.target.value)} placeholder="e.g. yasmin" />
        </div>
        <div style={{ flex: 1 }}>
          <label>Filter by date</label>
          <input type="date" value={dateFilter} onChange={e => setDateFilter(e.target.value)} />
        </div>
        <button className="btn btn-primary" onClick={fetchRecords}>
          <Search size={14} /> Search
        </button>
        <button className="btn btn-ghost" onClick={() => { setNameFilter(""); setDateFilter(""); setTimeout(fetchRecords, 0); }}>
          Clear
        </button>
      </div>

      {/* Table */}
      <div className="glass" style={{ padding: 0, overflow: "hidden" }}>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Timestamp</th>
              <th>Confidence</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {records.map(r => (
              <tr key={r.id}>
                <td style={{ color: "#475569" }}>#{r.id}</td>
                <td style={{ fontWeight: 600 }}>{r.name}</td>
                <td>{new Date(r.timestamp).toLocaleString()}</td>
                <td>{(r.confidence * 100).toFixed(1)}%</td>
                <td>
                  <span className={`badge ${r.name !== "Unknown" ? "badge-green" : "badge-gray"}`}>
                    {r.name !== "Unknown" ? "Recognised" : "Unknown"}
                  </span>
                </td>
              </tr>
            ))}
            {records.length === 0 && (
              <tr><td colSpan={5} style={{ textAlign: "center", padding: "2rem", color: "#475569" }}>No records found</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}