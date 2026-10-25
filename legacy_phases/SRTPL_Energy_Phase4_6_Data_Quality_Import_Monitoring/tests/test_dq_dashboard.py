from dq_dashboard.calculations import pct, calculate_metrics
from dq_dashboard.thresholds import health_band

def test_pct():
    assert pct(50, 100) == 50.0

def test_pct_zero_denominator():
    assert pct(1, 0) is None

def test_metrics():
    m = calculate_metrics(100, 95, 5, 2, 100, 3, 1, 100)
    assert m["completeness_pct"] == 100.0
    assert m["validation_pass_pct"] == 95.0
    assert m["duplicate_rate_pct"] == 2.0
    assert m["audit_traceability_pct"] == 100.0

def test_no_data_band():
    assert health_band(None, 98) == "NO DATA"
