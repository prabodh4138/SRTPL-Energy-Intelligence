RULES = {
    "SOLAR": [
        ("SOL-VAL-001", "Missing plant ID", "ERROR"),
        ("SOL-VAL-002", "Invalid timestamp", "ERROR"),
        ("SOL-VAL-003", "Negative cumulative generation", "CRITICAL"),
        ("SOL-VAL-004", "Cumulative generation decreased", "ERROR"),
        ("SOL-VAL-005", "Duplicate plant/date-time", "ERROR"),
        ("SOL-VAL-006", "Missing expected reading", "WARNING"),
    ],
    "DG": [
        ("DG-VAL-001", "Unknown generator", "ERROR"),
        ("DG-VAL-002", "Invalid status", "ERROR"),
        ("DG-VAL-003", "Cumulative kWh decreased", "ERROR"),
        ("DG-VAL-004", "Running hours decreased", "ERROR"),
        ("DG-VAL-005", "PF outside valid range", "ERROR"),
        ("DG-VAL-006", "KW/KVA/PF consistency issue", "WARNING"),
        ("DG-VAL-007", "Phase voltage/current imbalance", "WARNING"),
        ("DG-VAL-008", "Duplicate reading", "ERROR"),
    ],
    "EB": [
        ("EB-VAL-001", "Invalid date/time", "ERROR"),
        ("EB-VAL-002", "Negative meter value", "ERROR"),
        ("EB-VAL-003", "PF outside valid range", "ERROR"),
        ("EB-VAL-004", "Duplicate meter/date", "ERROR"),
        ("EB-VAL-005", "Missing required reading", "WARNING"),
        ("EB-VAL-006", "MD interpretation requires confirmation", "WARNING"),
    ],
    "TRANSFORMER": [
        ("TRF-VAL-001", "Invalid date/time", "ERROR"),
        ("TRF-VAL-002", "Invalid voltage/current value", "WARNING"),
        ("TRF-VAL-003", "PF outside valid range", "ERROR"),
        ("TRF-VAL-004", "Frequency outside expected range", "WARNING"),
        ("TRF-VAL-005", "Temperature threshold exceeded", "WARNING"),
        ("TRF-VAL-006", "Duplicate reading", "ERROR"),
    ],
    "UPS": [
        ("UPS-VAL-001", "Invalid date/time", "ERROR"),
        ("UPS-VAL-002", "Input/output voltage anomaly", "WARNING"),
        ("UPS-VAL-003", "Frequency anomaly", "WARNING"),
        ("UPS-VAL-004", "Battery voltage anomaly", "WARNING"),
        ("UPS-VAL-005", "Battery temperature anomaly", "WARNING"),
        ("UPS-VAL-006", "Duplicate reading", "ERROR"),
    ],
}

def get_rules(source_type):
    return RULES.get(source_type.upper(), [])
