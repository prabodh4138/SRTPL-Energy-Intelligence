from .common import check_non_decreasing
from .cumulative import cumulative_delta

def validate_solar(current, previous=None):
    issues = []

    issue = check_non_decreasing(
        current.get("cumulative_kwh"),
        previous.get("cumulative_kwh") if previous else None,
        "VAL-SOL-001",
        "Solar cumulative kWh"
    )
    if issue:
        issues.append(issue)

    delta, state = cumulative_delta(
        current.get("cumulative_kwh"),
        previous.get("cumulative_kwh") if previous else None
    )

    return issues, delta, state
