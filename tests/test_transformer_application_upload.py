import pytest

pytest.importorskip("streamlit")

from pathlib import Path
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "source_data" / "raw" / "Transformer" / "TransformerDailyReport_25thSep2026_2116_Transformer Daily Log Report.csv"


def test_transformer_juno_page_detects_real_csv_without_database():
    at = AppTest.from_file(str(ROOT / "active_app" / "pages" / "transformer_juno_import.py"), default_timeout=20)
    at.run()
    assert not at.exception

    try:
        at.file_uploader[0].set_value((SAMPLE.name, SAMPLE.read_bytes(), "text/csv"))
    except TypeError:
        at.file_uploader[0].set_value(SAMPLE.read_bytes(), SAMPLE.name)
    at.run()

    assert not at.exception
    assert at.metric[0].value == "TRANSFORMER"
    assert at.metric[1].value == "252"
    assert "SR-E-HT-TFR-000003" in at.metric[2].value
    assert any("Transformer JUNO structure detected" in x.value for x in at.success)
