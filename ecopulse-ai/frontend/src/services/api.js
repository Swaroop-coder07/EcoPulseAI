// All backend calls live here. Base URL is empty in dev (Vite proxies /api to FastAPI);
// set VITE_API_URL=http://host:8000 for a separately hosted backend.
const BASE = import.meta.env.VITE_API_URL || "";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body.detail) {
        detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      /* ignore non-JSON error bodies */
    }
    throw new Error(detail);
  }
  return res.json();
}

function qs(params = {}) {
  const clean = Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "");
  return clean.length ? "?" + new URLSearchParams(clean).toString() : "";
}

export const api = {
  dashboard: () => request("/api/dashboard"),
  buildings: () => request("/api/buildings"),
  readings: (params) => request(`/api/readings${qs(params)}`),
  addReading: (body) => request("/api/readings", { method: "POST", body: JSON.stringify(body) }),
  analytics: (params) => request(`/api/analytics${qs(params)}`),
  alerts: (params) => request(`/api/alerts${qs(params)}`),
  recommendations: (params) => request(`/api/recommendations${qs(params)}`),
  completeAction: (id) => request(`/api/actions/${id}/complete`, { method: "POST" }),
  impact: () => request("/api/impact"),
  leaderboard: () => request("/api/leaderboard"),
};
