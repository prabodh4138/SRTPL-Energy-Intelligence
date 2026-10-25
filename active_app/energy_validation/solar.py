from .common import check_non_decreasing
from .cumulative import cumulative_delta

def validate_solar(current, previous=None):
    issues = []
    curr_kwh = current.get("cumulative_kwh") or current.get("unit_generated_in_kwh")
    prev_kwh = (previous.get("cumulative_kwh") or previous.get("unit_generated_in_kwh")) if previous else None

    issue = check_non_decreasing(
        curr_kwh,
        prev_kwh,
        "VAL-SOL-001",
        "Solar cumulative kWh"
    )
    if issue:
        issues.append(issue)

    delta, state = cumulative_delta(
        curr_kwh,
        prev_kwh
    )

    return issues, delta, state
