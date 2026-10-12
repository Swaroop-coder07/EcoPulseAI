"""Rule-based hypotheses and recommended actions.

Keyed by (resource, building type) with a per-resource fallback. This is the
"AI Insights" text layer for the MVP; it can later be replaced by an ML model.
"""

# (hypothesis, recommended action)
RULES = {
    # ---- electricity ----
    ("electricity", "hostel"): (
        "Lights, fans or ACs left on in empty rooms / common areas.",
        "Do a room-wise night inspection, switch off idle lights/fans/ACs and set AC to 24-26 C.",
    ),
    ("electricity", "academic"): (
        "Lab equipment, projectors or AC running outside timetable hours.",
        "Match AC/projector schedules to the timetable, add auto-off timers and shut down idle lab PCs.",
    ),
    ("electricity", "library"): (
        "HVAC or lighting running at full load while footfall is low.",
        "Zone lighting and cooling by occupancy and switch off unused reading-hall zones after closing.",
    ),
    ("electricity", "office"): (
        "Office equipment and AC left on after working hours.",
        "Enable end-of-day shutdown checklist; put PCs and printers on power-saving mode.",
    ),
    ("electricity", "canteen"): (
        "Refrigeration or cooking equipment running inefficiently or left on.",
        "Service refrigerators/exhausts, switch off idle cooking equipment between meal slots.",
    ),
    # ---- water ----
    ("water", "hostel"): (
        "Possible leakage, overflowing overhead tank or taps left running.",
        "Inspect tanks, float valves and taps; repair leaks and install tap aerators.",
    ),
    ("water", "canteen"): (
        "Continuous tap use during dishwashing or a leaking pipe.",
        "Switch to low-flow nozzles for dishwashing and inspect kitchen plumbing for leaks.",
    ),
    ("water", "academic"): (
        "Leaking washroom fittings or lab taps left open.",
        "Check washroom/lab fittings and put up 'close the tap' reminders.",
    ),
    # ---- waste ----
    ("waste", "canteen"): (
        "Over-preparation of food and poor segregation increase waste volume.",
        "Track daily prepared vs consumed meals, segregate wet/dry waste and start composting.",
    ),
}

FALLBACK = {
    "electricity": (
        "Equipment left on or inefficient operation outside normal hours.",
        "Audit the building for idle loads and add timers or occupancy sensors.",
    ),
    "water": (
        "Possible leakage or unnecessary water use.",
        "Inspect pipes, tanks and taps for leaks and fix them.",
    ),
    "waste": (
        "Higher-than-normal waste generation, possibly poor segregation.",
        "Review waste segregation and set up recycling/composting bins.",
    ),
}


def build(resource_type: str, building_type: str, building_name: str, excess_pct: float) -> dict:
    """Return the hypothesis and recommended action for a detected anomaly."""
    hypothesis, action = RULES.get(
        (resource_type, building_type), FALLBACK.get(resource_type, ("Unusual consumption.", "Investigate the cause."))
    )
    return {
        "hypothesis": hypothesis,
        "action": f"{building_name}: {action}",
    }
