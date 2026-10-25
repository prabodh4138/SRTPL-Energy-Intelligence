import pytest

pytest.importorskip("streamlit")

from pathlib import Path
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "source_data" / "raw" / "Solar" / "Solar_Plant_Log_25thSep2026_2719_Solar Log.csv"


def test_solar_juno_page_detects_real_csv_without_database():
    at = AppTest.from_file(str(ROOT / "active_app" / "pages" / "solar_juno_import.py"), default_timeout=20)
    at.run()
    assert not at.exception

    try:
        at.file_uploader[0].set_value((SAMPLE.name, SAMPLE.read_bytes(), "text/csv"))
    except TypeError:
        at.file_uploader[0].set_value(SAMPLE.read_bytes(), SAMPLE.name)
    at.run()

    assert not at.exception
    assert at.metric[0].value == "SOLAR"
    assert at.metric[1].value == "177"
    assert "SR-E-AP-SPX-000002" in at.metric[2].value
    assert any("Solar JUNO structure detected" in x.value for x in at.success)
