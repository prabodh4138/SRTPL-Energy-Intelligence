from .models import ValidationIssue
from .thresholds import ThresholdProvider

def validate_ups(current, threshold_provider=None):
    issues = []
    threshold_provider = threshold_provider or ThresholdProvider()

    checks = [
        ("rectifier_voltage", "UPS-RECTIFIER-V"),
        ("bypass_voltage", "UPS-BYPASS-V"),
        ("bypass_frequency", "UPS-BYPASS-F"),
        ("output_voltage", "UPS-OUTPUT-V"),
        ("output_frequency", "UPS-OUTPUT-F"),
        ("battery_temperature", "UPS-BATT-T"),
        ("battery_vdc", "UPS-BATT-V"),
        ("battery_ib", "UPS-BATT-I"),
    ]

    for field, parameter in checks:
        value = current.get(field)
        if value is None:
            continue

        try:
            value_num = float(str(value).replace(",", ""))
        except (TypeError, ValueError):
            continue

        severity = threshold_provider.evaluate(parameter, value_num, "UPS")
        if severity:
            issues.append(ValidationIssue(
                rule_code=f"VAL-{parameter}",
                severity=severity,
                message=f"{field} is outside its configured threshold.",
                source_value=str(value)
            ))

    return issues
