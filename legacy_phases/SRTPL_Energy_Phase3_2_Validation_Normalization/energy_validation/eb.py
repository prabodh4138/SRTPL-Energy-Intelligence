from .common import check_non_decreasing, check_pf
from .cumulative import cumulative_delta

def validate_eb(current, previous=None):
    issues = []
    previous = previous or {}

    for field, code, label in [
        ("kwh", "VAL-EB-001", "EB cumulative kWh"),
        ("kvah", "VAL-EB-002", "EB cumulative KVAH"),
    ]:
        issue = check_non_decreasing(
            current.get(field), previous.get(field), code, label
        )
        if issue:
            issues.append(issue)

    issue = check_pf(current.get("pf"), "VAL-EB-003", "EB PF")
    if issue:
        issues.append(issue)

    kwh_delta, kwh_state = cumulative_delta(current.get("kwh"), previous.get("kwh"))
    kvah_delta, kvah_state = cumulative_delta(current.get("kvah"), previous.get("kvah"))
    kvarh_delta, kvarh_state = cumulative_delta(current.get("kvarh"), previous.get("kvarh"))

    return issues, {
        "interval_kwh": kwh_delta,
        "interval_kvah": kvah_delta,
        "interval_kvarh": kvarh_delta,
        "kwh_state": kwh_state,
        "kvah_state": kvah_state,
        "kvarh_state": kvarh_state,
    }
