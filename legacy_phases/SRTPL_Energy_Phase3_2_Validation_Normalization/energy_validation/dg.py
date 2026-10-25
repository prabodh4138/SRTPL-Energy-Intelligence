from .common import check_non_decreasing, check_pf, check_imbalance
from .cumulative import cumulative_delta

def validate_dg(current, previous=None, thresholds=None):
    issues = []
    previous = previous or {}
    thresholds = thresholds or {}

    issue = check_non_decreasing(
        current.get("cumulative_kwh"),
        previous.get("cumulative_kwh"),
        "VAL-DG-001",
        "DG cumulative kWh"
    )
    if issue: issues.append(issue)

    issue = check_non_decreasing(
        current.get("cumulative_running_hours"),
        previous.get("cumulative_running_hours"),
        "VAL-DG-002",
        "DG running hours"
    )
    if issue: issues.append(issue)

    pf_issue = check_pf(current.get("pf"), "VAL-DG-004", "DG PF")
    if pf_issue: issues.append(pf_issue)

    kva = _num(current.get("kva"))
    kw = _num(current.get("kw"))
    if kva is not None and kw is not None and kw > kva * 1.02:
        from .models import ValidationIssue
        issues.append(ValidationIssue(
            "VAL-DG-003", "WARNING",
            "DG kW is greater than kVA beyond tolerance.",
            f"kW={kw}, kVA={kva}", "kW <= kVA"
        ))

    issue = check_imbalance(
        [current.get("voltage_ry"), current.get("voltage_yb"), current.get("voltage_br")],
        "VAL-DG-V-IMB",
        "DG voltage",
        thresholds.get("voltage_imbalance_warning")
    )
    if issue: issues.append(issue)

    issue = check_imbalance(
        [current.get("current_r"), current.get("current_y"), current.get("current_b")],
        "VAL-DG-I-IMB",
        "DG current",
        thresholds.get("current_imbalance_warning")
    )
    if issue: issues.append(issue)

    gen_delta, gen_state = cumulative_delta(
        current.get("cumulative_kwh"),
        previous.get("cumulative_kwh")
    )
    run_delta, run_state = cumulative_delta(
        current.get("cumulative_running_hours"),
        previous.get("cumulative_running_hours")
    )

    return issues, {
        "interval_kwh": gen_delta,
        "interval_running_hours": run_delta,
        "kwh_state": gen_state,
        "runtime_state": run_state,
    }

def _num(v):
    try:
        return None if v is None else float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None
