"""Seed the database from data/sample_readings.csv.

Usage (from the backend/ folder):
    python seed.py            # create tables, load CSV if DB is empty, detect anomalies
    python seed.py --reset    # drop everything and reseed
    python seed.py --regen    # regenerate the CSV (ending yesterday) and reseed

The CSV is simulated usage data, so the demo needs no internet or sensors.
"""
import argparse

import pandas as pd

from database import Base, SessionLocal, engine
from models import Building, Reading
from sample_data import CSV_PATH, generate_csv
from services import anomaly

def load_csv(db) -> int:
    df = pd.read_csv(CSV_PATH, parse_dates=["timestamp"])
    buildings = {b.name: b for b in db.query(Building).all()}
    for name, btype in df[["building", "building_type"]].drop_duplicates().itertuples(index=False):
        if name not in buildings:
            b = Building(name=name, type=btype)
            db.add(b)
            buildings[name] = b
    db.flush()

    rows = [
        Reading(
            building_id=buildings[r.building].id,
            resource_type=r.resource_type,
            value=float(r.value),
            unit=r.unit,
            timestamp=r.timestamp.to_pydatetime(),
        )
        for r in df.itertuples(index=False)
    ]
    db.bulk_save_objects(rows)
    db.commit()
    return len(rows)


def run(reset: bool = False, regen: bool = False) -> None:
    if regen or not CSV_PATH.exists():
        generate_csv()
        print(f"Generated {CSV_PATH}")
    if reset or regen:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(Building).count() == 0:
            n = load_csv(db)
            alerts = anomaly.scan_all(db)
            print(f"Loaded {n} readings, detected {alerts} anomalies.")
        else:
            print("Database already seeded (use --reset to reload).")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--regen", action="store_true")
    args = parser.parse_args()
    run(reset=args.reset, regen=args.regen)
