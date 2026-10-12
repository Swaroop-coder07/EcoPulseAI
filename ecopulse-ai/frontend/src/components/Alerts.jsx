import { RESOURCES, SEVERITY_STYLES, fmt, inr } from "../utils.js";

export function SeverityBadge({ severity }) {
  return (
    <span
      className={`rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase ring-1 ring-inset ${
        SEVERITY_STYLES[severity] || SEVERITY_STYLES.low
      }`}
    >
      {severity}
    </span>
  );
}

// One detected anomaly: what happened, why (hypothesis), what to do, what it could save.
export function AlertCard({ alert }) {
  const meta = RESOURCES[alert.resource_type];
  return (
    <div className="card">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="font-semibold">
            {alert.building_name} <span className="font-normal text-slate-500">- {meta.label}</span>
          </p>
          <p className="text-xs text-slate-500">{String(alert.timestamp).slice(0, 10)}</p>
        </div>
        <div className="flex items-center gap-2">
          {alert.action_status === "completed" && (
            <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-700">
              ACTION DONE
            </span>
          )}
          <SeverityBadge severity={alert.severity} />
        </div>
      </div>

      <p className="mt-3 text-sm">
        Actual <b>{fmt(alert.actual_value, 1)}</b> {alert.unit} vs normal <b>{fmt(alert.baseline, 1)}</b> {alert.unit}{" "}
        <span className="font-semibold text-red-600">(+{alert.excess_pct}%)</span>
      </p>

      <dl className="mt-3 space-y-2 text-sm">
        <div>
          <dt className="text-xs font-semibold uppercase text-slate-500">Likely reason (hypothesis)</dt>
          <dd>{alert.hypothesis}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase text-slate-500">Recommended action</dt>
          <dd>{alert.recommended_action}</dd>
        </div>
        <div>
          <dt className="text-xs font-semibold uppercase text-slate-500">Potential saving (estimate)</dt>
          <dd>
            {fmt(alert.potential_saving, 1)} {alert.unit} · {fmt(alert.potential_co2e_kg, 1)} kg CO₂e ·{" "}
            {inr(alert.potential_cost_inr)}
          </dd>
        </div>
      </dl>
    </div>
  );
}
