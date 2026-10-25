import pytest
from master_data.validation import (
    validate_plaza, validate_asset,
    validate_effective_dates, validate_threshold
)
from master_data.versioning import next_version

def test_plaza_validation():
    validate_plaza("TP01", "Toll Plaza 01")

def test_asset_validation():
    validate_asset("SR-E-AP-UPS-000009", "UPS")

def test_invalid_dates():
    with pytest.raises(ValueError):
        validate_effective_dates("2026-05-01", "2026-04-01")

def test_threshold_validation():
    with pytest.raises(ValueError):
        validate_threshold(100, 90)

def test_version():
    class V:
        def __init__(self, n): self.version_no = n
    assert next_version([V(1), V(3)]) == 4
