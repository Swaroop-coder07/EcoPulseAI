export const RESOURCES = {
  electricity: { label: "Electricity", unit: "kWh", color: "#f59e0b" },
  water: { label: "Water", unit: "litres", color: "#0ea5e9" },
  waste: { label: "Waste", unit: "kg", color: "#78716c" },
};

export function fmt(n, digits = 0) {
  if (n === null || n === undefined || Number.isNaN(n)) return "-";
  return Number(n).toLocaleString("en-IN", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function inr(n) {
  return "₹" + fmt(n, 0);
}

export function shortDate(d) {
  if (!d) return "";
  return String(d).slice(5, 10); // MM-DD
}

export const SEVERITY_STYLES = {
  critical: "bg-red-100 text-red-700 ring-red-200",
  high: "bg-orange-100 text-orange-700 ring-orange-200",
  medium: "bg-amber-100 text-amber-700 ring-amber-200",
  low: "bg-sky-100 text-sky-700 ring-sky-200",
};
