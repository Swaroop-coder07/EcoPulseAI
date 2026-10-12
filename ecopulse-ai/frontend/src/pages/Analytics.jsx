import { useState } from "react";
import { Link } from "react-router-dom";
import { AlertCard } from "../components/Alerts.jsx";
import { ComparisonChart } from "../components/Charts.jsx";
import StatCard from "../components/StatCard.jsx";
import Status from "../components/Status.jsx";
import { api } from "../services/api.js";
import { useApi } from "../services/useApi.js";
import { RESOURCES, fmt } from "../utils.js";

export default function Analytics() {
  const [resource, setResource] = useState("electricity");
  const analytics = useApi(() => api.analytics({ resource_type: resource, days: 30 }), [resource]);
  const alerts = useApi(() => api.alerts({ status: "pending" }), []);

  const meta = RESOURCES[resource];
  const trend = analytics.data?.trend;
  const change = trend?.change_pct;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Analytics & AI Insights</h1>
        <div className="flex gap-1">
          {Object.entries(RESOURCES).map(([key, m]) => (
            <button
              key={key}
              onClick={() => setResource(key)}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
                resource === key ? "bg-emerald-600 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {analytics.data ? (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard label="Last 7 days" value={fmt(trend?.current_week)} unit={meta.unit} />
            <StatCard label="Previous 7 days" value={fmt(trend?.previous_week)} unit={meta.unit} />
            <StatCard
              label="Week-on-week change"
              value={change === null || change === undefined ? "-" : `${change > 0 ? "+" : ""}${change}%`}
              accent={change > 0 ? "text-red-600" : "text-emerald-600"}
              hint={change > 0 ? "Usage is rising" : "Usage is falling"}
            />
          </div>
          <div className="card">
            <h2 className="mb-3 font-semibold">Building comparison - {meta.label}</h2>
            <ComparisonChart data={analytics.data.comparison} unit={meta.unit} />
          </div>
        </>
      ) : (
        <Status loading={analytics.loading} error={analytics.error} hasData={false} />
      )}

      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Unusual consumption detected</h2>
          <Link to="/actions" className="text-sm font-medium text-emerald-700 hover:underline">
            Go to action tracker →
          </Link>
        </div>
        {alerts.data ? (
          alerts.data.length ? (
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              {alerts.data.map((a) => (
                <AlertCard key={a.id} alert={a} />
              ))}
            </div>
          ) : (
            <p className="card text-sm text-slate-500">No open anomalies. Nice work!</p>
          )
        ) : (
          <Status loading={alerts.loading} error={alerts.error} hasData={false} />
        )}
      </div>
    </div>
  );
}
