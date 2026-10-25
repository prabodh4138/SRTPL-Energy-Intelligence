from pathlib import Path
import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def test_new_modules_and_interconnected_pages():
    at = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=25)
    at.run()
    assert not at.exception, f"Initial render exception: {at.exception}"

    pages_to_test = [
        "Executive Dashboard",
        "Bills & Receipts",
        "Operator & Compliance Tracking",
        "Validation & Exceptions",
        "Data Quality",
    ]

    for p in pages_to_test:
        at.sidebar.radio[0].set_value(p)
        at.run()
        assert not at.exception, f"Error on page '{p}': {at.exception}"


def test_data_quality_programmatic_navigation_button():
    at = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=25)
    at.run()
    assert not at.exception

    # Navigate to Data Quality
    at.sidebar.radio[0].set_value("Data Quality")
    at.run()
    assert not at.exception

    # Click button to navigate to Validation & Exceptions
    btn_dq = [b for b in at.button if "Correct Offending" in b.label]
    assert len(btn_dq) == 1
    btn_dq[0].click()
    at.run()
    assert not at.exception
    assert at.sidebar.radio[0].value == "Validation & Exceptions"
