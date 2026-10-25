def pct(numerator, denominator):
    if denominator in (None, 0):
        return None
    return round((numerator / denominator) * 100, 2)

def calculate_metrics(records_received, records_valid, records_invalid,
                       records_duplicate, expected_records=None,
                       exceptions=0, corrections=0, traceable=0):
    return {
        "records_received": records_received,
        "records_valid": records_valid,
        "records_invalid": records_invalid,
        "records_duplicate": records_duplicate,
        "completeness_pct": pct(records_received, expected_records),
        "validation_pass_pct": pct(records_valid, records_received),
        "duplicate_rate_pct": pct(records_duplicate, records_received),
        "exception_rate_pct": pct(exceptions, records_received),
        "manual_correction_rate_pct": pct(corrections, records_received),
        "audit_traceability_pct": pct(traceable, records_received),
    }
