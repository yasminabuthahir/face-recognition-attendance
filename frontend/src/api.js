import axios from "axios";

const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({ baseURL: BASE });

export const getStreamUrl = () => `${BASE}/video_feed`;
export const getDetections = () => api.get("/detections");
export const getAttendance = (params) => api.get("/attendance", { params });
export const getToday = () => api.get("/attendance/today");
export const getSummary = () => api.get("/attendance/summary");
export const registerFace = (name, file) => {
  const form = new FormData();
  form.append("file", file);
  return api.post(`/register?name=${encodeURIComponent(name)}`, form);
};

export default api;