from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from database import Base


class Building(Base):
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    type = Column(String, nullable=False)  # library, academic, hostel, office, canteen

    readings = relationship("Reading", back_populates="building")
    alerts = relationship("Alert", back_populates="building")


class Reading(Base):
    __tablename__ = "readings"
    __table_args__ = (
        UniqueConstraint("building_id", "resource_type", "timestamp", name="uq_reading"),
    )

    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=False, index=True)
    resource_type = Column(String, nullable=False, index=True)  # electricity | water | waste
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)

    building = relationship("Building", back_populates="readings")
    alert = relationship("Alert", back_populates="reading", uselist=False)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=False, index=True)
    reading_id = Column(Integer, ForeignKey("readings.id"), unique=True, nullable=False)
    resource_type = Column(String, nullable=False)
    actual_value = Column(Float, nullable=False)
    baseline = Column(Float, nullable=False)
    excess_pct = Column(Float, nullable=False)
    severity = Column(String, nullable=False)  # low | medium | high | critical
    hypothesis = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)  # timestamp of the offending reading
    created_at = Column(DateTime, default=datetime.utcnow)

    building = relationship("Building", back_populates="alerts")
    reading = relationship("Reading", back_populates="alert")
    action = relationship("Action", back_populates="alert", uselist=False)


class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, default="pending", nullable=False)  # pending | completed
    estimated_savings = Column(Float, default=0.0)  # in the alert's resource unit
    # Filled in when the action is completed:
    co2e_saved_kg = Column(Float, default=0.0)
    eco_points = Column(Integer, default=0)
    completed_at = Column(DateTime, nullable=True)

    alert = relationship("Alert", back_populates="action")
