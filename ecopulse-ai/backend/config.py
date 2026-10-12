"""Central, configurable settings for EcoPulse AI.

Every value can be overridden with an environment variable so the demo can
show how thresholds / factors are tuned for a real campus.
"""
import os

# --- Anomaly detection -------------------------------------------------------
# Raise an alert when (actual - baseline) / baseline * 100 is above this value.
ALERT_THRESHOLD_PCT = float(os.getenv("ALERT_THRESHOLD_PCT", 25))
# Baseline = median of the previous N daily readings of the same building+resource.
BASELINE_WINDOW_DAYS = int(os.getenv("BASELINE_WINDOW_DAYS", 14))
# Minimum history required before a baseline is trusted.
MIN_BASELINE_POINTS = int(os.getenv("MIN_BASELINE_POINTS", 7))

# --- Units -------------------------------------------------------------------
RESOURCE_TYPES = ("electricity", "water", "waste")
UNITS = {"electricity": "kWh", "water": "litres", "waste": "kg"}

# --- Impact factors (ESTIMATES - document source/units in the demo) ----------
# kg CO2e per unit of resource.
#  electricity: ~0.82 kg CO2e/kWh, approximate Indian grid average (verify
#               against the latest CEA CO2 Baseline Database before publishing).
#  water:       ~0.344 kg CO2e per m3 (0.000344 per litre) supply + treatment,
#               illustrative.
#  waste:       ~0.5 kg CO2e per kg of mixed waste to landfill, illustrative.
EMISSION_FACTORS = {
    "electricity": float(os.getenv("EF_ELECTRICITY", 0.82)),
    "water": float(os.getenv("EF_WATER", 0.000344)),
    "waste": float(os.getenv("EF_WASTE", 0.5)),
}

# Cost in INR per unit (illustrative campus tariffs).
COST_PER_UNIT = {
    "electricity": float(os.getenv("COST_ELECTRICITY", 8.0)),   # INR / kWh
    "water": float(os.getenv("COST_WATER", 0.05)),               # INR / litre
    "waste": float(os.getenv("COST_WASTE", 2.0)),                # INR / kg disposal
}

# Eco-points: base points per completed action + points per kg CO2e avoided.
ECO_POINTS_BASE = 10
ECO_POINTS_PER_KG_CO2E = 2
