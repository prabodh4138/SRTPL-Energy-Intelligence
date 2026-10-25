from .models import ValidationIssue, ValidationResult
from .numbers import number, valid_pf, percent_imbalance

def check_pf(value, rule_code, label="PF"):
    if value is None:
        return None

    if not valid_pf(value):
        return ValidationIssue(
            rule_code=rule_code,
            severity="ERROR",
            message=f"{label} is outside the normal 0 to 1 range.",
            source_value=str(value),
            expected_value="0 <= PF <= 1"
        )
    return None

def check_non_decreasing(current, previous, rule_code, label):
    if current is None or previous is None:
        return None

    c = number(current)
    p = number(previous)

    if c is None or p is None:
        return None

    if c < p:
        return ValidationIssue(
            rule_code=rule_code,
            severity="ERROR",
            message=f"{label} decreased from {p} to {c}. Possible meter reset/replacement or invalid reading.",
            source_value=str(c),
            expected_value=f">= {p}"
        )
    return None

def check_imbalance(values, rule_code, label, threshold):
    if threshold is None:
        return None

    imbalance = percent_imbalance(values)

    if imbalance is None:
        return None

    if imbalance > threshold:
        return ValidationIssue(
            rule_code=rule_code,
            severity="WARNING",
            message=f"{label} imbalance is {imbalance:.2f}%, above configured threshold {threshold:.2f}%.",
            source_value=f"{imbalance:.2f}%",
            expected_value=f"<= {threshold:.2f}%"
        )

    return None
