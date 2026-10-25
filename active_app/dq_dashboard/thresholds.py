DEFAULT_THRESHOLDS = {
    "completeness_good": 98.0,
    "validation_pass_good": 98.0,
    "duplicate_rate_good": 1.0,
    "exception_rate_good": 2.0,
    "traceability_good": 99.0,
}

def health_band(value, good_threshold, inverse=False):
    if value is None:
        return "NO DATA"
    if inverse:
        return "GOOD" if value <= good_threshold else "REVIEW"
    return "GOOD" if value >= good_threshold else "REVIEW"
