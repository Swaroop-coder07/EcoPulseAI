"""Baseline-based waste / anomaly detection.

    Excess % = (Actual - Baseline) / Baseline * 100

An alert is raised when Excess % is greater than config.ALERT_THRESHOLD_PCT.
Baseline = median of the previous BASELINE_WINDOW_DAYS readings of the same
building and resource (median is robust to earlier spikes).
"""
from collections import defaultdict
from statistics import median
from typing import Optional

from sqlalchemy.orm import Session

import config
from models import Action, Alert, Reading
from services import impact, recommendations

_UNSET = object()


def excess_pct(actual: float, baseline: float) -> float:
    if baseline is None or baseline <= 0:
        return 0.0
    return (actual - baseline) / baseline * 100.0


def severity_for(excess: float) -> str:
    if excess >= 60:
        return "critical"
    if excess >= 40:
        return "high"
    if excess >= 30:
        return "medium"
    return "low"


def series_with_baseline(readings: list) -> list:
    """Given readings sorted by timestamp (one building + resource), return
    [(reading, baseline_or_None)] using a rolling median of previous readings."""
    out = []
    window = config.BASELINE_WINDOW_DAYS
    for i, r in enumerate(readings):
        prev = [x.value for x in readings[max(0, i - window):i]]
        baseline = median(prev) if len(prev) >= config.MIN_BASELINE_POINTS else None
        out.append((r, baseline))
    return out


def compute_baseline(db: Session, building_id: int, resource_type: str, before) -> Optional[float]:
    rows = (
        db.query(Reading.value)
        .filter(
            Reading.building_id == building_id,
            Reading.resource_type == resource_type,
            Reading.timestamp < before,
        )
        .order_by(Reading.timestamp.desc())
        .limit(config.BASELINE_WINDOW_DAYS)
        .all()
    )
    values = [r[0] for r in rows]
    if len(values) < config.MIN_BASELINE_POINTS:
        return None
    return median(values)


def evaluate_reading(db: Session, reading: Reading, baseline=_UNSET) -> Optional[Alert]:
    """Check one reading; create an Alert + pending Action if it is anomalous."""
    if reading.alert is not None:
        return reading.alert

    if baseline is _UNSET:
        baseline = compute_baseline(db, reading.building_id, reading.resource_type, reading.timestamp)
    if baseline is None:
        return None

    excess = excess_pct(reading.value, baseline)
    if excess <= config.ALERT_THRESHOLD_PCT:
        return None

    building = reading.building
    rec = recommendations.build(reading.resource_type, building.type, building.name, excess)
    alert = Alert(
        building_id=reading.building_id,
        reading_id=reading.id,
        resource_type=reading.resource_type,
        actual_value=reading.value,
        baseline=baseline,
        excess_pct=round(excess, 1),
        severity=severity_for(excess),
        hypothesis=rec["hypothesis"],
        timestamp=reading.timestamp,
    )
    db.add(alert)
    db.flush()
    db.add(
        Action(
            alert_id=alert.id,
            description=rec["action"],
            status="pending",
            # Potential saving = max(0, actual - target); target = baseline.
            estimated_savings=round(impact.potential_saving(reading.value, baseline), 2),
        )
    )
    db.flush()
    return alert


def scan_all(db: Session) -> int:
    """Run detection over every stored reading. Returns number of new alerts."""
    grouped = defaultdict(list)
    for r in db.query(Reading).order_by(Reading.timestamp).all():
        grouped[(r.building_id, r.resource_type)].append(r)

    created = 0
    for readings in grouped.values():
        for reading, baseline in series_with_baseline(readings):
            if reading.alert is None and evaluate_reading(db, reading, baseline) is not None:
                created += 1
    db.commit()
    return created
