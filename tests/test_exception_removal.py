import pytest

pytest.importorskip("streamlit")
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def test_exception_immediately_removed_when_resolved():
    at = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=25)
    at.run()
    assert not at.exception

    # Navigate to Validation & Exceptions
    at.sidebar.radio[0].set_value("Validation & Exceptions")
    at.run()
    assert not at.exception

    # Initial state should have open errors
    initial_open_errors = int(at.metric[0].value)
    initial_resolved = int(at.metric[2].value)
    assert initial_open_errors > 0

    # Click Apply Correction on the first available open exception
    save_btns = [b for b in at.button if "Apply Correction" in b.label]
    assert len(save_btns) >= 1
    save_btns[0].click()
    at.run()
    assert not at.exception

    # Verify exception is removed immediately from open list:
    # Open count decreased by 1, Resolved count increased by 1
    new_open_errors = int(at.metric[0].value)
    new_resolved = int(at.metric[2].value)
    assert new_open_errors == initial_open_errors - 1
    assert new_resolved == initial_resolved + 1

    # Verify success banner confirming immediate removal
    assert any("immediately removed from the active list" in s.value for s in at.success)
