import pytest
from reports.catalog import REPORT_CATALOG
from reports.models import ReportFilter
from reports.engine import ReportEngine

def test_core_reports_exist():
    assert "EXECUTIVE_MIS" in REPORT_CATALOG
    assert "DAILY_ENERGY" in REPORT_CATALOG
    assert "EXCEPTION" in REPORT_CATALOG

def test_unknown_report_rejected():
    with pytest.raises(ValueError):
        ReportEngine().validate_request("UNKNOWN", "csv")

def test_pdf_supported():
    assert "pdf" in REPORT_CATALOG["MONTHLY_ENERGY"]["formats"]

def test_filter_shape():
    f = ReportFilter("2026-09-01", "2026-09-30", plaza_id="TP01")
    assert f.plaza_id == "TP01"
