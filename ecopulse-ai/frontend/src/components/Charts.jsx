import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { RESOURCES, shortDate } from "../utils.js";

const axisProps = { tick: { fontSize: 12, fill: "#64748b" }, stroke: "#cbd5e1" };

// Daily campus usage for one resource (weekly view on the dashboard).
export function UsageChart({ data, resource }) {
  const meta = RESOURCES[resource];
  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="date" tickFormatter={shortDate} {...axisProps} />
          <YAxis {...axisProps} width={56} />
          <Tooltip formatter={(v) => [`${v} ${meta.unit}`, meta.label]} />
          <Bar dataKey={resource} name={meta.label} fill={meta.color} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// Normal (baseline) vs actual consumption. Anomalous days get a red dot.
export function BaselineChart({ series, unit }) {
  const renderDot = (props) => {
    const { cx, cy, payload, index } = props;
    if (cx == null || cy == null || !payload?.is_anomaly) return <g key={`d-${index}`} />;
    return <circle key={`d-${index}`} cx={cx} cy={cy} r={6} fill="#dc2626" stroke="#fff" strokeWidth={2} />;
  };

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={series} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="date" tickFormatter={shortDate} {...axisProps} />
          <YAxis {...axisProps} width={56} />
          <Tooltip formatter={(v, name) => [`${v} ${unit}`, name]} />
          <Legend />
          <Line
            type="monotone"
            dataKey="baseline"
            name="Normal (baseline)"
            stroke="#94a3b8"
            strokeDasharray="5 5"
            dot={false}
            connectNulls
          />
          <Line type="monotone" dataKey="actual" name="Actual" stroke="#059669" strokeWidth={2} dot={renderDot} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// Last 7 days vs previous 7 days per building.
export function ComparisonChart({ data, unit }) {
  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="building_name" {...axisProps} />
          <YAxis {...axisProps} width={56} />
          <Tooltip formatter={(v, name) => [`${v} ${unit}`, name]} />
          <Legend />
          <Bar dataKey="previous_7d" name="Previous 7 days" fill="#cbd5e1" radius={[4, 4, 0, 0]} />
          <Bar dataKey="last_7d" name="Last 7 days" fill="#059669" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
