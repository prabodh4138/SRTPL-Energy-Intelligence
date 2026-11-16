from .common import check_non_decreasing
from .cumulative import cumulative_delta
from .models import ValidationIssue

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

    # Physical generation sanity check: 40.46 kWp plant cannot generate > 400 kWh in a single 24h interval
    if delta is not None and delta > 400.0:
        issues.append(
            ValidationIssue(
                rule_code="VAL-SOL-002",
                severity="ERROR",
                message=f"Solar daily generation of {delta:.1f} kWh exceeds physical plant capacity ceiling (max 400.0 kWh/day for 40.46 kWp plant).",
                source_value=str(delta),
                expected_value="0 <= generation <= 400.0"
            )
        )
        state = "EXCEEDS_CAPACITY"

    return issues, delta, state
