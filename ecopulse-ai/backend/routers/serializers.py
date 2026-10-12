"""Helpers that turn ORM objects into API schemas."""
import config
from models import Action, Alert
from schemas import ActionOut, AlertOut
from services import impact


def alert_to_out(alert: Alert) -> AlertOut:
    action = alert.action
    saving = action.estimated_savings if action else impact.potential_saving(alert.actual_value, alert.baseline)
    return AlertOut(
        id=alert.id,
        building_id=alert.building_id,
        building_name=alert.building.name,
        resource_type=alert.resource_type,
        unit=config.UNITS[alert.resource_type],
        actual_value=round(alert.actual_value, 2),
        baseline=round(alert.baseline, 2),
        excess_pct=alert.excess_pct,
        severity=alert.severity,
        hypothesis=alert.hypothesis,
        timestamp=alert.timestamp,
        action_id=action.id if action else None,
        action_status=action.status if action else None,
        recommended_action=action.description if action else None,
        potential_saving=round(saving, 2),
        potential_co2e_kg=round(impact.co2e_kg(alert.resource_type, saving), 2),
        potential_cost_inr=round(impact.cost_inr(alert.resource_type, saving), 2),
    )


def action_to_out(action: Action) -> ActionOut:
    alert = action.alert
    saving = action.estimated_savings or 0.0
    return ActionOut(
        id=action.id,
        alert_id=alert.id,
        building_id=alert.building_id,
        building_name=alert.building.name,
        resource_type=alert.resource_type,
        unit=config.UNITS[alert.resource_type],
        description=action.description,
        hypothesis=alert.hypothesis,
        severity=alert.severity,
        status=action.status,
        estimated_savings=round(saving, 2),
        estimated_co2e_kg=round(impact.co2e_kg(alert.resource_type, saving), 2),
        estimated_cost_inr=round(impact.cost_inr(alert.resource_type, saving), 2),
        eco_points=action.eco_points or 0,
        completed_at=action.completed_at,
    )
