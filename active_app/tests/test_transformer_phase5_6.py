from pathlib import Path
from import_engine.service import ImportService
from import_engine.hash_utils import sha256_file
from supabase_import.raw_mapper import map_transformer
from energy_validation.transformer import validate_transformer
from analytics.transformer_phase5_6 import calculate_transformer_kpis_from_normalized

ROOT = Path(__file__).resolve().parents[2]
TRF_DIR = ROOT / "source_data" / "raw" / "Transformer"


def test_transformer_duplicate_file_detection():
    f1 = TRF_DIR / "TransformerDailyReport_25thSep2026_109_Transformer Daily Log Report.csv"
    f2 = TRF_DIR / "TransformerDailyReport_25thSep2026_109_Transformer Daily Log Report - Copy.csv"
    assert sha256_file(f1) == sha256_file(f2)


def test_transformer_detection_and_mapping():
    service = ImportService()
    res = service.inspect(str(TRF_DIR / "TransformerDailyReport_25thSep2026_2116_Transformer Daily Log Report.csv"))
    assert res["report_type"] == "TRANSFORMER"
    assert res["record_count"] == 252
    assert res["metadata"].asset_code == "SR-E-HT-TFR-000003"

    rec = res["records"][0]
    rec.import_row_id = "trf-1"
    mapped = map_transformer(rec)
    assert mapped["primary_v_ry"] is not None
    assert mapped["secondary_v_ry"] is not None
    assert mapped["wti"] is not None
    assert mapped["oti"] is not None


def test_transformer_kpis_and_audit_guard():
    service = ImportService()
    res = service.inspect(str(TRF_DIR / "TransformerDailyReport_25thSep2026_2116_Transformer Daily Log Report.csv"))
    readings = []
    for i, r in enumerate(res["records"]):
        r.import_row_id = f"trf-{i}"
        raw = map_transformer(r)
        issues = validate_transformer(raw)
        raw["data_quality_status"] = "VALID" if not issues else "EXCEPTION"
        readings.append(raw)

    kpis = calculate_transformer_kpis_from_normalized(readings)
    assert kpis["valid_source_rows"] == 252
    assert "loss/efficiency is intentionally disabled" in kpis["audit_note"]
