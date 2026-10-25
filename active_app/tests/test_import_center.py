from import_center.hash import sha256_bytes
from import_center.detector import detect_report_type
from import_center.service import JunoImportService

def test_hash_is_stable():
    assert sha256_bytes(b"abc") == sha256_bytes(b"abc")

def test_detect_transformer():
    assert detect_report_type("TransformerDailyReport.csv", "Transformer Daily Log Report") == "TRANSFORMER"

def test_detect_ups():
    assert detect_report_type("UPSDailyLogReport.csv", "UPS Daily Log Report") == "UPS"

def test_detect_eb():
    assert detect_report_type("EBDailyLogReport.csv", "EB Daily Log Report") == "EB"

def test_precheck():
    metadata, checks = JunoImportService().precheck(
        "SolarDailyReport.csv", b"Solar Plant Report,Date,kWh"
    )
    assert metadata.sha256
    assert metadata.report_type == "SOLAR"
    assert any(c.code == "REPORT_DETECTED" and c.status == "PASS" for c in checks)


def test_load_settings_graceful():
    from supabase_import.config import load_settings
    settings = load_settings()
    assert hasattr(settings, "supabase_url")
    assert hasattr(settings, "supabase_key")
    assert hasattr(settings, "storage_bucket")
