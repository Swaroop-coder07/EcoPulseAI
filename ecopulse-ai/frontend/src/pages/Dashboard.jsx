import { useState } from "react";
import StatCard from "../components/StatCard.jsx";
import Status from "../components/Status.jsx";
import { UsageChart } from "../components/Charts.jsx";
import { api } from "../services/api.js";
import { useApi } from "../services/useApi.js";
import { RESOURCES, fmt, inr } from "../utils.js";

export default function Dashboard() {
  const { data, error, loading } = useApi(() => api.dashboard(), []);
  const [resource, setResource] = useState("electricity");

  if (!data) return <Status loading={loading} error={error} hasData={false} />;

  const p = data.potential_savings;
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Campus Dashboard</h1>
        {data.period && (
          <p className="text-sm text-slate-500">
            Last 7 days: {data.period.start} to {data.period.end}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Electricity" value={fmt(data.totals.electricity_kwh)} unit="kWh" accent="text-amber-600" />
        <StatCard label="Water" value={fmt(data.totals.water_litres)} unit="litres" accent="text-sky-600" />
        <StatCard label="Waste" value={fmt(data.totals.waste_kg)} unit="kg" accent="text-stone-600" />
        <StatCard
          label="Estimated carbon emissions"
          value={fmt(data.carbon_emissions_kg_co2e)}
          unit="kg CO₂e"
          hint="Usage x configurable emission factors"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="card lg:col-span-2">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h2 className="font-semibold">Weekly usage</h2>
            <div className="flex gap-1">
              {Object.entries(RESOURCES).map(([key, meta]) => (
                <button
                  key={key}
                  onClick={() => setResource(key)}
                  className={`rounded-lg px-3 py-1 text-sm font-medium ${
                    resource === key ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  {meta.label}
                </button>
              ))}
            </div>
          </div>
          <UsageChart data={data.weekly_usage} resource={resource} />
        </div>

        <div className="space-y-4">
          <div className="card">
            <h2 className="font-semibold">Potential savings</h2>
            <p className="text-xs text-slate-500">Estimated opportunity from open alerts, not verified savings.</p>
            <ul className="mt-3 space-y-1 text-sm">
              <li>{fmt(p.electricity_kwh)} kWh electricity</li>
              <li>{fmt(p.water_litres)} litres water</li>
              <li>{fmt(p.waste_kg)} kg waste</li>
            </ul>
            <p className="mt-3 text-sm font-semibold text-emerald-700">
              {fmt(p.co2e_kg)} kg CO₂e · {inr(p.cost_inr)}
            </p>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <StatCard label="Open alerts" value={data.open_alerts} accent="text-red-600" />
            <StatCard label="Done" value={data.completed_actions} accent="text-emerald-600" />
            <StatCard label="Eco-points" value={data.eco_points} />
          </div>
        </div>
      </div>
    </div>
  );
}
