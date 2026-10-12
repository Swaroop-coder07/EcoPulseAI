"""Savings, CO2e and eco-point calculations.

    Potential Saving = max(0, Actual - Target)
    CO2e Reduction   = Energy Saved x Emission Factor

IMPORTANT: potential / estimated savings are opportunities, NOT verified
savings. Measured savings are computed separately from readings recorded
AFTER an action was completed.
"""
from datetime import datetime

from sqlalchemy.orm import Session

import config
from models import Action, Alert, Reading

BLOCK_KEYS = {"electricity": "electricity_kwh", "water": "water_litres", "waste": "waste_kg"}


def potential_saving(actual: float, target: float) -> float:
    return max(0.0, actual - target)


def co2e_kg(resource_type: str, quantity: float) -> float:
    return quantity * config.EMISSION_FACTORS.get(resource_type, 0.0)


def cost_inr(resource_type: str, quantity: float) -> float:
    return quantity * config.COST_PER_UNIT.get(resource_type, 0.0)


def eco_points(co2e: float) -> int:
    return config.ECO_POINTS_BASE + round(co2e * config.ECO_POINTS_PER_KG_CO2E)


def make_block(by_resource: dict) -> dict:
    """{resource: quantity} -> summary block with CO2e and cost totals."""
    block = {key: 0.0 for key in BLOCK_KEYS.values()}
    co2 = 0.0
    cost = 0.0
    for resource, qty in by_resource.items():
        block[BLOCK_KEYS[resource]] = round(qty, 2)
        co2 += co2e_kg(resource, qty)
        cost += cost_inr(resource, qty)
    block["co2e_kg"] = round(co2, 2)
    block["cost_inr"] = round(cost, 2)
    return block


def complete_action(db: Session, action: Action) -> Action:
    """Mark an action as completed, record estimated savings, award eco-points."""
    if action.status == "completed":
        raise ValueError("Action already completed")
    resource = action.alert.resource_type
    co2 = co2e_kg(resource, action.estimated_savings or 0.0)
    action.status = "completed"
    action.completed_at = datetime.now()
    action.co2e_saved_kg = round(co2, 3)
    action.eco_points = eco_points(co2)
    db.commit()
    db.refresh(action)
    return action


def measured_saving(db: Session, action: Action) -> float:
    """Verified saving: how far readings recorded AFTER completion fall below
    the alert's baseline (same building + resource)."""
    if action.status != "completed" or action.completed_at is None:
        return 0.0
    alert = action.alert
    rows = (
        db.query(Reading.value)
        .filter(
            Reading.building_id == alert.building_id,
            Reading.resource_type == alert.resource_type,
            Reading.timestamp > action.completed_at,
        )
        .all()
    )
    return sum(max(0.0, alert.baseline - v[0]) for v in rows)


def impact_summary(db: Session) -> dict:
    potential = {r: 0.0 for r in config.RESOURCE_TYPES}
    estimated = {r: 0.0 for r in config.RESOURCE_TYPES}
    measured = {r: 0.0 for r in config.RESOURCE_TYPES}
    points = 0
    completed = 0
    pending = 0

    for action in db.query(Action).join(Alert).all():
        resource = action.alert.resource_type
        if action.status == "completed":
            completed += 1
            points += action.eco_points or 0
            estimated[resource] += action.estimated_savings or 0.0
            measured[resource] += measured_saving(db, action)
        else:
            pending += 1
            potential[resource] += action.estimated_savings or 0.0

    return {
        "potential_open": make_block(potential),
        "estimated_completed": make_block(estimated),
        "measured_verified": make_block(measured),
        "eco_points_total": points,
        "actions_completed": completed,
        "actions_pending": pending,
        "assumptions": {
            "emission_factors_kg_co2e_per_unit": config.EMISSION_FACTORS,
            "cost_inr_per_unit": config.COST_PER_UNIT,
            "alert_threshold_pct": config.ALERT_THRESHOLD_PCT,
            "baseline": f"median of previous {config.BASELINE_WINDOW_DAYS} daily readings",
            "note": (
                "Potential and estimated figures are opportunities, not verified savings. "
                "Measured = readings after completion that fall below the alert baseline."
            ),
        },
    }
