from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

ResourceType = Literal["electricity", "water", "waste"]


class BuildingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str


class ReadingCreate(BaseModel):
    building_id: int
    resource_type: ResourceType
    value: float = Field(ge=0, description="Consumption in the resource's unit")
    timestamp: Optional[datetime] = None  # defaults to "now"


class ReadingOut(BaseModel):
    id: int
    building_id: int
    building_name: str
    resource_type: str
    value: float
    unit: str
    timestamp: datetime


class AlertOut(BaseModel):
    id: int
    building_id: int
    building_name: str
    resource_type: str
    unit: str
    actual_value: float
    baseline: float
    excess_pct: float
    severity: str
    hypothesis: str
    timestamp: datetime
    action_id: Optional[int] = None
    action_status: Optional[str] = None
    recommended_action: Optional[str] = None
    potential_saving: float = 0.0
    potential_co2e_kg: float = 0.0
    potential_cost_inr: float = 0.0


class ReadingCreateResult(BaseModel):
    reading: ReadingOut
    alert: Optional[AlertOut] = None


class ActionOut(BaseModel):
    id: int
    alert_id: int
    building_id: int
    building_name: str
    resource_type: str
    unit: str
    description: str
    hypothesis: str
    severity: str
    status: str
    estimated_savings: float
    estimated_co2e_kg: float
    estimated_cost_inr: float
    eco_points: int
    completed_at: Optional[datetime] = None


class CompleteActionResult(BaseModel):
    action: ActionOut
    eco_points_awarded: int
    co2e_saved_kg: float
    message: str
