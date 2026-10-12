import { useState } from "react";
import { SeverityBadge } from "../components/Alerts.jsx";
import Status from "../components/Status.jsx";
import { api } from "../services/api.js";
import { useApi } from "../services/useApi.js";
import { RESOURCES, fmt, inr } from "../utils.js";

function ImpactBlock({ title, subtitle, block, tone }) {
  return (
    <div className={`card border-l-4 ${tone}`}>
      <h3 className="font-semibold">{title}</h3>
      <p className="text-xs text-slate-500">{subtitle}</p>
      <ul className="mt-3 space-y-1 text-sm">
        <li>{fmt(block.electricity_kwh, 1)} kWh electricity</li>
        <li>{fmt(block.water_litres, 0)} litres water</li>
        <li>{fmt(block.waste_kg, 1)} kg waste</li>
      </ul>
      <p className="mt-3 text-sm font-semibold">
        {fmt(block.co2e_kg, 1)} kg CO₂e · {inr(block.cost_inr)}
      </p>
    </div>
  );
}

export default function Actions() {
  const recs = useApi(() => api.recommendations(), []);
  const impact = useApi(() => api.impact(), []);
  const board = useApi(() => api.leaderboard(), []);
  const [busyId, setBusyId] = useState(null);
  const [message, setMessage] = useState(null);

  async function complete(id) {
    setBusyId(id);
    setMessage(null);
    try {
      const r = await api.completeAction(id);
      setMessage({ tone: "ok", text: `+${r.eco_points_awarded} eco-points! ${r.message}` });
      recs.reload();
      impact.reload();
      board.reload();
    } catch (e) {
      setMessage({ tone: "error", text: e.message });
    } finally {
      setBusyId(null);
    }
  }

  if (!recs.data) return <Status loading={recs.loading} error={recs.error} hasData={false} />;

  const pending = recs.data.filter((a) => a.status === "pending");
  const done = recs.data.filter((a) => a.status === "completed");

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold">Action Tracker</h1>

      {message && (
        <p
          className={`rounded-lg p-3 text-sm ${
            message.tone === "ok" ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"
          }`}
        >
          {message.text}
        </p>
      )}

      <section>
        <h2 className="mb-3 text-lg font-semibold">Recommended actions ({pending.length})</h2>
        <div className="space-y-3">
          {pending.length === 0 && <p className="card text-sm text-slate-500">All recommended actions are complete.</p>}
          {pending.map((a) => (
            <div key={a.id} className="card flex flex-wrap items-center justify-between gap-4">
              <div className="min-w-0 flex-1">
                <div className="mb-1 flex items-center gap-2">
                  <SeverityBadge severity={a.severity} />
                  <span className="text-xs text-slate-500">
                    {RESOURCES[a.resource_type].label} · {a.building_name}
                  </span>
                </div>
                <p className="text-sm">{a.description}</p>
                <p className="mt-1 text-xs text-slate-500">
                  Estimated saving: {fmt(a.estimated_savings, 1)} {a.unit} · {fmt(a.estimated_co2e_kg, 1)} kg CO₂e ·{" "}
                  {inr(a.estimated_cost_inr)}
                </p>
              </div>
              <button className="btn" disabled={busyId === a.id} onClick={() => complete(a.id)}>
                {busyId === a.id ? "Saving..." : "Mark completed"}
              </button>
            </div>
          ))}
        </div>
      </section>

      {impact.data && (
        <section>
          <h2 className="mb-1 text-lg font-semibold">Sustainability impact</h2>
          <p className="mb-3 text-sm text-slate-500">
            Estimated and measured savings are shown separately. Measured savings come only from readings recorded after
            an action was completed.
          </p>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <ImpactBlock
              title="Potential (open alerts)"
              subtitle="Estimated opportunity, not realised"
              block={impact.data.potential_open}
              tone="border-l-amber-400"
            />
            <ImpactBlock
              title="Estimated (completed actions)"
              subtitle="Based on alert excess, not yet verified"
              block={impact.data.estimated_completed}
              tone="border-l-sky-400"
            />
            <ImpactBlock
              title="Measured (verified)"
              subtitle="New readings below the old baseline"
              block={impact.data.measured_verified}
              tone="border-l-emerald-500"
            />
          </div>
          <p className="mt-3 text-sm">
            Total eco-points: <b>{impact.data.eco_points_total}</b> · Completed: <b>{impact.data.actions_completed}</b> ·
            Pending: <b>{impact.data.actions_pending}</b>
          </p>
          <details className="mt-2 text-xs text-slate-500">
            <summary className="cursor-pointer">Assumptions</summary>
            <p className="mt-1">
              Emission factors (kg CO₂e/unit): electricity {impact.data.assumptions.emission_factors_kg_co2e_per_unit.electricity},
              water {impact.data.assumptions.emission_factors_kg_co2e_per_unit.water}, waste{" "}
              {impact.data.assumptions.emission_factors_kg_co2e_per_unit.waste}. Alert threshold:{" "}
              {impact.data.assumptions.alert_threshold_pct}%. Baseline: {impact.data.assumptions.baseline}.
            </p>
          </details>
        </section>
      )}

      <section>
        <h2 className="mb-3 text-lg font-semibold">Building efficiency ranking</h2>
        <div className="card overflow-x-auto p-0">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-2">Rank</th>
                <th className="px-4 py-2">Building</th>
                <th className="px-4 py-2 text-right">Efficiency score</th>
                <th className="px-4 py-2 text-right">Open alerts</th>
                <th className="px-4 py-2 text-right">Eco-points</th>
              </tr>
            </thead>
            <tbody>
              {(board.data || []).map((b) => (
                <tr key={b.building_id} className="border-t border-slate-100">
                  <td className="px-4 py-2 font-semibold">#{b.rank}</td>
                  <td className="px-4 py-2">{b.building_name}</td>
                  <td className="px-4 py-2 text-right">{b.efficiency_score}</td>
                  <td className="px-4 py-2 text-right">{b.open_alerts}</td>
                  <td className="px-4 py-2 text-right">{b.eco_points}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-slate-500">
          Efficiency score = 100 minus the average excess % over baseline across all resources in the last 7 days.
        </p>
      </section>

      {done.length > 0 && (
        <section>
          <h2 className="mb-3 text-lg font-semibold">Completed ({done.length})</h2>
          <div className="space-y-2">
            {done.map((a) => (
              <div key={a.id} className="card flex flex-wrap items-center justify-between gap-2 py-3">
                <div>
                  <p className="text-sm">{a.description}</p>
                  <p className="text-xs text-slate-500">
                    {a.building_name} · estimated saving {fmt(a.estimated_savings, 1)} {a.unit}
                  </p>
                </div>
                <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
                  +{a.eco_points} eco-points
                </span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
