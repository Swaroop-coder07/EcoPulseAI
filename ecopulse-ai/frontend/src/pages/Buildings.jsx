import { useEffect, useState } from "react";
import { AlertCard } from "../components/Alerts.jsx";
import { BaselineChart } from "../components/Charts.jsx";
import Status from "../components/Status.jsx";
import { api } from "../services/api.js";
import { useApi } from "../services/useApi.js";
import { RESOURCES, fmt } from "../utils.js";

export default function Buildings() {
  const buildings = useApi(() => api.buildings(), []);
  const [buildingId, setBuildingId] = useState(null);
  const [resource, setResource] = useState("electricity");

  useEffect(() => {
    if (buildings.data?.length && buildingId === null) setBuildingId(buildings.data[0].id);
  }, [buildings.data, buildingId]);

  const analytics = useApi(
    () => (buildingId ? api.analytics({ resource_type: resource, building_id: buildingId, days: 30 }) : Promise.resolve(null)),
    [buildingId, resource]
  );
  const alerts = useApi(
    () => (buildingId ? api.alerts({ building_id: buildingId, resource_type: resource }) : Promise.resolve([])),
    [buildingId, resource]
  );
  const readings = useApi(
    () => (buildingId ? api.readings({ building_id: buildingId, resource_type: resource, days: 14, limit: 10 }) : Promise.resolve([])),
    [buildingId, resource]
  );

  // --- add-reading form ---
  const [value, setValue] = useState("");
  const [date, setDate] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState(null);

  async function submit(e) {
    e.preventDefault();
    setSubmitting(true);
    setMessage(null);
    try {
      const body = { building_id: buildingId, resource_type: resource, value: parseFloat(value) };
      if (date) body.timestamp = `${date}T00:00:00`;
      const result = await api.addReading(body);
      setMessage(
        result.alert
          ? { tone: "warn", text: `High usage detected: +${result.alert.excess_pct}% above normal.` }
          : { tone: "ok", text: "Reading saved. Usage is within the normal range." }
      );
      setValue("");
      setDate("");
      analytics.reload();
      alerts.reload();
      readings.reload();
    } catch (err) {
      setMessage({ tone: "error", text: err.message });
    } finally {
      setSubmitting(false);
    }
  }

  if (!buildings.data) return <Status loading={buildings.loading} error={buildings.error} hasData={false} />;

  const meta = RESOURCES[resource];
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Building Monitoring</h1>

      <div className="card flex flex-wrap items-end gap-4">
        <label className="text-sm">
          <span className="mb-1 block font-medium text-slate-600">Building</span>
          <select className="input" value={buildingId ?? ""} onChange={(e) => setBuildingId(Number(e.target.value))}>
            {buildings.data.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name} ({b.type})
              </option>
            ))}
          </select>
        </label>
        <div className="flex gap-1">
          {Object.entries(RESOURCES).map(([key, m]) => (
            <button
              key={key}
              onClick={() => setResource(key)}
              className={`rounded-lg px-3 py-2 text-sm font-medium ${
                resource === key ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="card lg:col-span-2">
          <h2 className="font-semibold">Normal vs actual - {meta.label}</h2>
          <p className="mb-3 text-xs text-slate-500">
            Last 30 days. Dashed line = baseline (median of previous 14 days). Red dots = anomalies.
          </p>
          {analytics.data ? (
            <BaselineChart series={analytics.data.series} unit={meta.unit} />
          ) : (
            <Status loading={analytics.loading} error={analytics.error} hasData={false} />
          )}
        </div>

        <form onSubmit={submit} className="card space-y-3">
          <h2 className="font-semibold">Add a reading</h2>
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">
              {meta.label} used ({meta.unit})
            </span>
            <input
              className="input"
              type="number"
              step="any"
              min="0"
              required
              value={value}
              onChange={(e) => setValue(e.target.value)}
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Date (optional, defaults to now)</span>
            <input className="input" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
          </label>
          <button className="btn w-full" disabled={submitting || !value}>
            {submitting ? "Saving..." : "Save reading"}
          </button>
          {message && (
            <p
              className={`rounded-lg p-2 text-sm ${
                message.tone === "ok"
                  ? "bg-emerald-50 text-emerald-700"
                  : message.tone === "warn"
                  ? "bg-amber-50 text-amber-800"
                  : "bg-red-50 text-red-700"
              }`}
            >
              {message.text}
            </p>
          )}
        </form>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div>
          <h2 className="mb-3 font-semibold">High-usage alerts</h2>
          <div className="space-y-3">
            {alerts.data?.length ? (
              alerts.data.map((a) => <AlertCard key={a.id} alert={a} />)
            ) : (
              <p className="card text-sm text-slate-500">No alerts for this building and resource.</p>
            )}
          </div>
        </div>
        <div>
          <h2 className="mb-3 font-semibold">Recent readings</h2>
          <div className="card overflow-x-auto p-0">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-2">Date</th>
                  <th className="px-4 py-2 text-right">Value</th>
                </tr>
              </thead>
              <tbody>
                {(readings.data || []).map((r) => (
                  <tr key={r.id} className="border-t border-slate-100">
                    <td className="px-4 py-2">{String(r.timestamp).slice(0, 16).replace("T", " ")}</td>
                    <td className="px-4 py-2 text-right">
                      {fmt(r.value, 1)} {r.unit}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
