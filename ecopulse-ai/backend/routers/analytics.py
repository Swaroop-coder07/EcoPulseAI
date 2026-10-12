"""Analytics APIs: trends, alerts, recommendations, actions, impact, leaderboard."""
from collections import defaultdict
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

import config
from database import get_db
from models import Action, Alert, Building, Reading
from routers.serializers import action_to_out, alert_to_out
from schemas import ActionOut, AlertOut, CompleteActionResult
from services import anomaly, impact

router = APIRouter(prefix="/api", tags=["analytics"])

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _pct_change(current: float, previous: float):
    if not previous:
        return None
    return round((current - previous) / previous * 100, 1)


@router.get("/analytics")
def analytics(
    resource_type: str = "electricity",
    building_id: Optional[int] = None,
    days: int = 30,
    db: Session = Depends(get_db),
):
    if resource_type not in config.RESOURCE_TYPES:
        raise HTTPException(422, f"resource_type must be one of {config.RESOURCE_TYPES}")

    readings = (
        db.query(Reading)
        .filter(Reading.resource_type == resource_type)
        .order_by(Reading.timestamp)
        .all()
    )
    unit = config.UNITS[resource_type]
    if not readings:
        return {"resource_type": resource_type, "unit": unit, "series": [], "comparison": [], "trend": None}

    latest = readings[-1].timestamp
    cutoff = latest - timedelta(days=days)

    by_building = defaultdict(list)
    for r in readings:
        by_building[r.building_id].append(r)
    names = {b.id: b.name for b in db.query(Building).all()}

    # ---- series: actual vs normal (baseline) ----
    series = []
    if building_id is not None:
        for r, baseline in anomaly.series_with_baseline(by_building.get(building_id, [])):
            if r.timestamp > cutoff:
                ex = anomaly.excess_pct(r.value, baseline) if baseline else None
                series.append({
                    "date": r.timestamp.date().isoformat(),
                    "actual": round(r.value, 1),
                    "baseline": round(baseline, 1) if baseline else None,
                    "excess_pct": round(ex, 1) if ex is not None else None,
                    "is_anomaly": bool(ex is not None and ex > config.ALERT_THRESHOLD_PCT),
                })
    else:
        daily_actual = defaultdict(float)
        daily_base = defaultdict(float)
        daily_missing = defaultdict(bool)
        for rs in by_building.values():
            for r, baseline in anomaly.series_with_baseline(rs):
                if r.timestamp > cutoff:
                    d = r.timestamp.date().isoformat()
                    daily_actual[d] += r.value
                    if baseline is None:
                        daily_missing[d] = True
                    else:
                        daily_base[d] += baseline
        for d in sorted(daily_actual):
            series.append({
                "date": d,
                "actual": round(daily_actual[d], 1),
                "baseline": None if daily_missing[d] else round(daily_base[d], 1),
                "excess_pct": None,
                "is_anomaly": False,
            })

    # ---- comparison: last 7 days vs previous 7 days per building ----
    week_start = latest - timedelta(days=7)
    prev_start = latest - timedelta(days=14)
    comparison = []
    total_cur = total_prev = 0.0
    for bid, rs in by_building.items():
        cur = sum(r.value for r in rs if r.timestamp > week_start)
        prev = sum(r.value for r in rs if prev_start < r.timestamp <= week_start)
        total_cur += cur
        total_prev += prev
        comparison.append({
            "building_id": bid,
            "building_name": names.get(bid, str(bid)),
            "last_7d": round(cur, 1),
            "previous_7d": round(prev, 1),
            "change_pct": _pct_change(cur, prev),
        })
    comparison.sort(key=lambda c: c["last_7d"], reverse=True)

    return {
        "resource_type": resource_type,
        "unit": unit,
        "series": series,
        "comparison": comparison,
        "trend": {
            "current_week": round(total_cur, 1),
            "previous_week": round(total_prev, 1),
            "change_pct": _pct_change(total_cur, total_prev),
        },
    }


@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(
    status: Optional[str] = None,  # pending | completed
    resource_type: Optional[str] = None,
    building_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Alert).outerjoin(Action)
    if status:
        q = q.filter(Action.status == status)
    if resource_type:
        q = q.filter(Alert.resource_type == resource_type)
    if building_id:
        q = q.filter(Alert.building_id == building_id)
    alerts = q.order_by(Alert.timestamp.desc()).all()
    alerts.sort(key=lambda a: SEVERITY_ORDER.get(a.severity, 9))  # stable: newest first within severity
    return [alert_to_out(a) for a in alerts]


@router.get("/recommendations", response_model=list[ActionOut])
def list_recommendations(status: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Action).join(Alert)
    if status:
        q = q.filter(Action.status == status)
    actions = q.order_by(Alert.timestamp.desc()).all()
    actions.sort(key=lambda a: (a.status != "pending", SEVERITY_ORDER.get(a.alert.severity, 9)))
    return [action_to_out(a) for a in actions]


@router.post("/actions/{action_id}/complete", response_model=CompleteActionResult)
def complete_action(action_id: int, db: Session = Depends(get_db)):
    action = db.get(Action, action_id)
    if action is None:
        raise HTTPException(404, "Action not found")
    try:
        impact.complete_action(db, action)
    except ValueError as exc:
        raise HTTPException(409, str(exc))
    return CompleteActionResult(
        action=action_to_out(action),
        eco_points_awarded=action.eco_points,
        co2e_saved_kg=action.co2e_saved_kg,
        message="Action completed. Savings are estimated until new readings verify them.",
    )


@router.get("/impact")
def get_impact(db: Session = Depends(get_db)):
    return impact.impact_summary(db)


@router.get("/leaderboard")
def leaderboard(db: Session = Depends(get_db)):
    """Building efficiency ranking.

    Efficiency score = 100 - average excess % (vs baseline) across all
    resources over the last 7 days. Higher is better.
    """
    latest = db.query(func.max(Reading.timestamp)).scalar()
    if latest is None:
        return []
    week_start = latest - timedelta(days=7)

    grouped = defaultdict(list)
    for r in db.query(Reading).order_by(Reading.timestamp).all():
        grouped[(r.building_id, r.resource_type)].append(r)

    excess_by_building = defaultdict(list)
    for (bid, _res), rs in grouped.items():
        for r, baseline in anomaly.series_with_baseline(rs):
            if baseline and r.timestamp > week_start:
                excess_by_building[bid].append(anomaly.excess_pct(r.value, baseline))

    points = defaultdict(int)
    open_alerts = defaultdict(int)
    for action in db.query(Action).join(Alert).all():
        bid = action.alert.building_id
        if action.status == "completed":
            points[bid] += action.eco_points or 0
        else:
            open_alerts[bid] += 1

    rows = []
    for b in db.query(Building).all():
        ex = excess_by_building.get(b.id, [])
        avg_excess = sum(ex) / len(ex) if ex else 0.0
        rows.append({
            "building_id": b.id,
            "building_name": b.name,
            "type": b.type,
            "avg_excess_pct": round(avg_excess, 1),
            "efficiency_score": round(100 - avg_excess, 1),
            "open_alerts": open_alerts[b.id],
            "eco_points": points[b.id],
        })
    rows.sort(key=lambda r: (-r["efficiency_score"], -r["eco_points"]))
    for i, row in enumerate(rows, start=1):
        row["rank"] = i
    return rows
