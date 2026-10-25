import pytest
from exception_center.status import can_transition
from exception_center.rules import get_rules
from exception_center.service import ExceptionService

def test_open_can_be_resolved():
    assert can_transition("OPEN", "RESOLVED")

def test_resolved_is_terminal():
    assert not can_transition("RESOLVED", "OPEN")

def test_resolution_note_required():
    service = ExceptionService()
    with pytest.raises(ValueError):
        service.resolve(None, "x", "OPEN", "", "user")

def test_known_solar_rules():
    rules = get_rules("SOLAR")
    assert any(code == "SOL-VAL-003" for code, _, _ in rules)
