"""Monthly analytics: trend, month-vs-month comparison, CO2e and baseline savings.

Pure functions over plain tuples (no DB access) so the logic is easy to test:

    rows   = [(timestamp, resource_type, value, baseline_or_None), ...]   one per reading
    alerts = [(timestamp, resource_type, potential_saving, action_status), ...]

Important definitions
---------------------
* Month totals are campus totals (all buildings added together).
* Months can be partial (data starts mid-month, or the current month is not over).
  Totals of a partial month are NOT comparable with a full month, so every
  comparison also reports the daily average, which is the like-for-like number.
* Baseline savings = baseline - actual, summed over the days that have a baseline
  (the baseline is the median of the previous 14 days, see services/anomaly.py).
  Positive = below the recent normal (estimated saving, not verified);
  negative = above it (overuse).
"""
import calendar
from collections import defaultdict
from datetime import date

import config
from services import impact

RESOURCES = config.RESOURCE_TYPES


def pct_change(current, previous):
    if previous is None or previous == 0 or current is None:
        return None
    return round((current - previous) / previous * 100, 1)


def direction(change):
    if change is None:
        return "n/a"
    if abs(change) < 0.5:
        return "flat"
    return "increase" if change > 0 else "decrease"


def previous_month(year: int, month: int):
    return (year - 1, 12) if month == 1 else (year, month - 1)


def _aggregate(rows):
    agg = defaultdict(lambda: {
        "dates": set(),
        "total": defaultdict(float),
        "baseline": defaultdict(float),
        "actual_on_baseline_days": defaultdict(float),
    })
    for ts, resource, value, baseline in rows:
        m = agg[(ts.year, ts.month)]
        m["dates"].add(ts.date())
        m["total"][resource] += value
        if baseline is not None:
            m["baseline"][resource] += baseline
            m["actual_on_baseline_days"][resource] += value
    return agg


def _info(agg, year, month):
    days_in_month = calendar.monthrange(year, month)[1]
    m = agg.get((year, month))
    days = len(m["dates"]) if m else 0
    return {
        "year": year,
        "month": month,
        "label": f"{calendar.month_name[month]} {year}",
        "days_with_data": days,
        "days_in_month": days_in_month,
        "has_data": days > 0,
        "partial": 0 < days < days_in_month,
    }


def _total(agg, year, month, resource):
    m = agg.get((year, month))
    return m["total"][resource] if m else 0.0


def _co2e_total(agg, year, month):
    return sum(impact.co2e_kg(r, _total(agg, year, month, r)) for r in RESOURCES)


def _filters(agg):
    months_by_year = defaultdict(list)
    for (y, mth) in sorted(agg):
        months_by_year[y].append(mth)
    years = sorted(months_by_year)
    latest = None
    if years:
        latest = {"year": years[-1], "month": months_by_year[years[-1]][-1]}
    return {
        "years": years,
        "months_by_year": {str(y): ms for y, ms in months_by_year.items()},
        "latest": latest,
    }


def _resolve_selection(filters, year, month):
    latest = filters["latest"]
    if latest is None:
        today = date.today()
        return year or today.year, month or today.month
    if year is None and month is None:
        return latest["year"], latest["month"]
    if year is None:
        return latest["year"], month
    if month is None:
        months = filters["months_by_year"].get(str(year))
        return year, (months[-1] if months else 1)
    return year, month


def _trend(agg, year):
    out = []
    for mth in range(1, 13):
        info = _info(agg, year, mth)
        entry = {
            "month": mth,
            "label": calendar.month_abbr[mth],
            "has_data": info["has_data"],
            "partial": info["partial"],
            "days_with_data": info["days_with_data"],
        }
        for r in RESOURCES:
            entry[r] = round(_total(agg, year, mth, r), 1) if info["has_data"] else None
        entry["co2e_kg"] = round(_co2e_total(agg, year, mth), 1) if info["has_data"] else None
        out.append(entry)
    return out


def _comparison(agg, sel, prev):
    def block(resource, unit, cur_total, prev_total):
        cur_avg = cur_total / sel["days_with_data"] if sel["has_data"] else None
        prev_avg = prev_total / prev["days_with_data"] if prev["has_data"] else None
        change = pct_change(cur_total, prev_total) if (sel["has_data"] and prev["has_data"]) else None
        avg_change = pct_change(cur_avg, prev_avg)
        return {
            "resource": resource,
            "unit": unit,
            "selected": round(cur_total, 1) if sel["has_data"] else None,
            "previous": round(prev_total, 1) if prev["has_data"] else None,
            "change_pct": change,
            "direction": direction(change),
            "selected_daily_avg": round(cur_avg, 1) if cur_avg is not None else None,
            "previous_daily_avg": round(prev_avg, 1) if prev_avg is not None else None,
            "daily_avg_change_pct": avg_change,
            "daily_avg_direction": direction(avg_change),
        }

    rows = [
        block(
            r,
            config.UNITS[r],
            _total(agg, sel["year"], sel["month"], r),
            _total(agg, prev["year"], prev["month"], r),
        )
        for r in RESOURCES
    ]
    rows.append(
        block(
            "co2e",
            "kg CO₂e",
            _co2e_total(agg, sel["year"], sel["month"]),
            _co2e_total(agg, prev["year"], prev["month"]),
        )
    )
    return rows


def _carbon(agg, sel, prev, alerts):
    y, mth = sel["year"], sel["month"]
    m = agg.get((y, mth))

    emissions = {r: round(impact.co2e_kg(r, _total(agg, y, mth, r)), 1) for r in RESOURCES}
    total = sum(impact.co2e_kg(r, _total(agg, y, mth, r)) for r in RESOURCES)
    prev_total = _co2e_total(agg, prev["year"], prev["month"])

    baseline_rows = []
    net_co2e = 0.0
    net_cost = 0.0
    for r in RESOURCES:
        baseline = m["baseline"][r] if m else 0.0
        actual = m["actual_on_baseline_days"][r] if m else 0.0
        if baseline <= 0:
            baseline_rows.append({
                "resource": r, "unit": config.UNITS[r], "actual": None, "baseline": None,
                "difference": None, "difference_pct": None,
                "co2e_difference_kg": None, "cost_difference_inr": None,
            })
            continue
        diff = baseline - actual  # positive = below baseline = estimated saving
        co2_diff = impact.co2e_kg(r, diff)
        cost_diff = impact.cost_inr(r, diff)
        net_co2e += co2_diff
        net_cost += cost_diff
        baseline_rows.append({
            "resource": r,
            "unit": config.UNITS[r],
            "actual": round(actual, 1),
            "baseline": round(baseline, 1),
            "difference": round(diff, 1),
            "difference_pct": round(diff / baseline * 100, 1),
            "co2e_difference_kg": round(co2_diff, 2),
            "cost_difference_inr": round(cost_diff, 0),
        })

    # Waste found by the anomaly detector in this month (opportunity, not verified).
    excess = {r: 0.0 for r in RESOURCES}
    completed = {r: 0.0 for r in RESOURCES}
    n_alerts = n_completed = 0
    for ts, resource, saving, status in alerts:
        if (ts.year, ts.month) != (y, mth):
            continue
        n_alerts += 1
        excess[resource] += saving or 0.0
        if status == "completed":
            n_completed += 1
            completed[resource] += saving or 0.0

    has_baseline = any(row["baseline"] is not None for row in baseline_rows)
    return {
        "emissions_kg_co2e": {**emissions, "total": round(total, 1)},
        "previous_total_kg_co2e": round(prev_total, 1) if prev["has_data"] else None,
        "change_pct": pct_change(total, prev_total) if (sel["has_data"] and prev["has_data"]) else None,
        "baseline_comparison": baseline_rows,
        "net_vs_baseline_co2e_kg": round(net_co2e, 1) if has_baseline else None,
        "net_vs_baseline_cost_inr": round(net_cost, 0) if has_baseline else None,
        "status": (
            None if not has_baseline else ("below_baseline" if net_co2e >= 0 else "above_baseline")
        ),
        "detected_waste": {
            "alerts": n_alerts,
            "actions_completed": n_completed,
            "potential": impact.make_block(excess),
            "estimated_from_completed": impact.make_block(completed),
        },
        "note": (
            "Baseline = median of the previous "
            f"{config.BASELINE_WINDOW_DAYS} daily readings. Positive difference = usage below the recent normal "
            "(estimated saving, not verified); negative = overuse. Detected waste is an opportunity, not a verified saving."
        ),
    }


def build_report(rows, alerts, year=None, month=None) -> dict:
    agg = _aggregate(rows)
    filters = _filters(agg)
    year, month = _resolve_selection(filters, year, month)

    sel = _info(agg, year, month)
    py, pm = previous_month(year, month)
    prev = _info(agg, py, pm)

    return {
        "filters": filters,
        "selected": sel,
        "previous": prev,
        "trend": _trend(agg, year),
        "comparison": _comparison(agg, sel, prev),
        "carbon": _carbon(agg, sel, prev, alerts),
    }
