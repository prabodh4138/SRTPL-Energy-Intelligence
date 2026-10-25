import pytest

pytest.importorskip("streamlit")

from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "source_data" / "raw" / "DG" / "DGDailyLogReport_25thSep2026_443_DG Log.csv"


def test_dg_juno_page_detects_real_csv_without_database():
    at = AppTest.from_file(str(ROOT / "active_app" / "pages" / "dg_juno_import.py"), default_timeout=20)
    at.run()
    assert not at.exception

    try:
        at.file_uploader[0].set_value((SAMPLE.name, SAMPLE.read_bytes(), "text/csv"))
    except TypeError:
        at.file_uploader[0].set_value(SAMPLE.read_bytes(), SAMPLE.name)
    at.run()

    assert not at.exception
    assert at.metric[0].value == "DG"
    assert at.metric[1].value == "334"
    assert "SR-E-AP-DGX-000004" in at.metric[2].value
    assert any("DG JUNO structure detected" in x.value for x in at.success)
