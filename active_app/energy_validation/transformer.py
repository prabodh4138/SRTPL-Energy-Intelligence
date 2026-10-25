from .common import check_pf, check_imbalance
from .numbers import number

def validate_transformer(current, thresholds=None):
    issues = []
    thresholds = thresholds or {}

    issue = check_pf(current.get("pf"), "VAL-TRF-001", "Transformer PF")
    if issue: issues.append(issue)

    issue = check_imbalance(
        [current.get("primary_v_ry"), current.get("primary_v_yb"), current.get("primary_v_br")],
        "VAL-TRF-PV-IMB",
        "Transformer primary voltage",
        thresholds.get("primary_voltage_imbalance_warning")
    )
    if issue: issues.append(issue)

    issue = check_imbalance(
        [current.get("secondary_v_ry"), current.get("secondary_v_yb"), current.get("secondary_v_br")],
        "VAL-TRF-SV-IMB",
        "Transformer secondary voltage",
        thresholds.get("secondary_voltage_imbalance_warning")
    )
    if issue: issues.append(issue)

    issue = check_imbalance(
        [current.get("primary_i_r"), current.get("primary_i_y"), current.get("primary_i_b")],
        "VAL-TRF-PI-IMB",
        "Transformer primary current",
        thresholds.get("primary_current_imbalance_warning")
    )
    if issue: issues.append(issue)

    issue = check_imbalance(
        [current.get("secondary_i_r"), current.get("secondary_i_y"), current.get("secondary_i_b")],
        "VAL-TRF-SI-IMB",
        "Transformer secondary current",
        thresholds.get("secondary_current_imbalance_warning")
    )
    if issue: issues.append(issue)

    return issues
