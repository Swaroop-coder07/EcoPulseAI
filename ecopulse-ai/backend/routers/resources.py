"""Resource APIs: dashboard, buildings, readings."""
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

import config
from database import get_db
from models import Action, Alert, Building, Reading
from schemas import BuildingOut, ReadingCreate, ReadingCreateResult, ReadingOut
from services import anomaly, impact
from routers.serializers import alert_to_out

router = APIRouter(prefix="/api", tags=["resources"])


def reading_to_out(r: Reading) -> ReadingOut:
    return ReadingOut(
        id=r.id,
        building_id=r.building_id,
        building_name=r.building.name,
        resource_type=r.resource_type,
        value=r.value,
        unit=r.unit,
        timestamp=r.timestamp,
    )


@router.get("/buildings", response_model=list[BuildingOut])
def list_buildings(db: Session = Depends(get_db)):
    return db.query(Building).order_by(Building.name).all()


@router.get("/readings", response_model=list[ReadingOut])
def list_readings(
    building_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    latest = db.query(func.max(Reading.timestamp)).scalar()
    if latest is None:
        return []
    q = db.query(Reading).filter(Reading.timestamp > latest - timedelta(days=days))
    if building_id is not None:
        q = q.filter(Reading.building_id == building_id)
    if resource_type is not None:
        q = q.filter(Reading.resource_type == resource_type)
    rows = q.order_by(Reading.timestamp.desc()).limit(limit).all()
    return [reading_to_out(r) for r in rows]


@router.post("/readings", response_model=ReadingCreateResult, status_code=201)
def add_reading(payload: ReadingCreate, db: Session = Depends(get_db)):
    building = db.get(Building, payload.building_id)
    if building is None:
        raise HTTPException(404, "Building not found")

    ts = payload.timestamp or datetime.now()
    duplicate = (
        db.query(Reading)
        .filter(
            Reading.building_id == payload.building_id,
            Reading.resource_type == payload.resource_type,
            Reading.timestamp == ts,
        )
        .first()
    )
    if duplicate:
        raise HTTPException(409, "A reading for this building/resource/timestamp already exists")

    reading = Reading(
        building_id=payload.building_id,
        resource_type=payload.resource_type,
        value=payload.value,
        unit=config.UNITS[payload.resource_type],
        timestamp=ts,
    )
    db.add(reading)
    db.flush()
    alert = anomaly.evaluate_reading(db, reading)  # instant anomaly check
    db.commit()
    db.refresh(reading)
    return ReadingCreateResult(
        reading=reading_to_out(reading),
        alert=alert_to_out(alert) if alert else None,
    )


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    latest = db.query(func.max(Reading.timestamp)).scalar()
    empty_block = impact.make_block({})
    if latest is None:
        return {
            "period": None,
            "totals": {"electricity_kwh": 0, "water_litres": 0, "waste_kg": 0},
            "carbon_emissions_kg_co2e": 0,
            "potential_savings": empty_block,
            "open_alerts": 0,
            "completed_actions": 0,
            "eco_points": 0,
            "weekly_usage": [],
        }

    start = latest - timedelta(days=7)
    rows = db.query(Reading).filter(Reading.timestamp > start).order_by(Reading.timestamp).all()

    totals = defaultdict(float)
    daily = defaultdict(lambda: {r: 0.0 for r in config.RESOURCE_TYPES})
    for r in rows:
        totals[r.resource_type] += r.value
        daily[r.timestamp.date().isoformat()][r.resource_type] += r.value

    emissions = sum(impact.co2e_kg(res, qty) for res, qty in totals.items())

    summary = impact.impact_summary(db)
    return {
        "period": {"start": (start + timedelta(seconds=1)).date().isoformat(), "end": latest.date().isoformat()},
        "totals": {
            "electricity_kwh": round(totals["electricity"], 1),
            "water_litres": round(totals["water"], 1),
            "waste_kg": round(totals["waste"], 1),
        },
        "carbon_emissions_kg_co2e": round(emissions, 1),
        "potential_savings": summary["potential_open"],
        "open_alerts": db.query(Alert).join(Action).filter(Action.status == "pending").count(),
        "completed_actions": summary["actions_completed"],
        "eco_points": summary["eco_points_total"],
        "weekly_usage": [
            {"date": d, **{k: round(v, 1) for k, v in vals.items()}} for d, vals in sorted(daily.items())
        ],
    }
