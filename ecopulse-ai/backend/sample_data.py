"""Generate simulated campus usage data (stdlib only).

    python sample_data.py        # writes ../data/sample_readings.csv (30 days, ending yesterday)

Some waste events are injected on purpose so the demo always has alerts.
"""
import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path

import config

CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_readings.csv"

BUILDINGS = [
    ("Central Library", "library"),
    ("Science Block", "academic"),
    ("Hostel A", "hostel"),
    ("Hostel B", "hostel"),
    ("Admin Block", "office"),
    ("Canteen", "canteen"),
]

# Typical daily usage per building type: electricity kWh, water litres, waste kg.
BASE = {
    "library": {"electricity": 420, "water": 2500, "waste": 35},
    "academic": {"electricity": 780, "water": 4200, "waste": 55},
    "hostel": {"electricity": 650, "water": 9000, "waste": 80},
    "office": {"electricity": 360, "water": 1800, "waste": 25},
    "canteen": {"electricity": 520, "water": 7000, "waste": 120},
}
# Saturday/Sunday multiplier (campus buildings quieter, hostel/canteen slightly busier).
WEEKEND = {"library": 0.75, "academic": 0.7, "hostel": 1.05, "office": 0.6, "canteen": 1.05}

# Injected waste events: (building, resource, days_ago) -> multiplier.
ANOMALIES = {
    ("Science Block", "electricity", 1): 1.62,
    ("Central Library", "electricity", 1): 1.32,
    ("Hostel B", "water", 1): 1.38,
    ("Hostel A", "electricity", 2): 1.45,
    ("Canteen", "waste", 2): 1.35,
    ("Canteen", "water", 3): 1.70,
    ("Admin Block", "electricity", 5): 1.28,
}


def generate_csv(days: int = 30, end: date | None = None) -> Path:
    end = end or (date.today() - timedelta(days=1))
    rng = random.Random(42)
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["building", "building_type", "resource_type", "value", "unit", "timestamp"])
        for name, btype in BUILDINGS:
            for resource in config.RESOURCE_TYPES:
                for offset in range(days - 1, -1, -1):
                    day = end - timedelta(days=offset)
                    days_ago = offset + 1
                    mult = ANOMALIES.get((name, resource, days_ago))
                    # Injected events skip the weekend discount so they stay clearly anomalous.
                    weekend = 1.0 if (mult or day.weekday() < 5) else WEEKEND[btype]
                    value = BASE[btype][resource] * weekend * rng.uniform(0.95, 1.05) * (mult or 1.0)
                    writer.writerow([
                        name, btype, resource, round(value, 1), config.UNITS[resource],
                        datetime.combine(day, datetime.min.time()).isoformat(),
                    ])
    return CSV_PATH


if __name__ == "__main__":
    print(f"Wrote {generate_csv()}")
