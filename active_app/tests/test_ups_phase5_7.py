from pathlib import Path
from import_engine.service import ImportService
from supabase_import.raw_mapper import map_ups
from energy_validation.ups import validate_ups
from analytics.ups_phase5_7 import calculate_ups_kpis_from_normalized

ROOT = Path(__file__).resolve().parents[2]
UPS_DIR = ROOT / "source_data" / "raw" / "UPS"


def test_ups_detection_and_mapping():
    service = ImportService()
    res = service.inspect(str(UPS_DIR / "UPSDailyLogReport_25thSep2026_2140_UPS Daily Log Report.csv"))
    assert res["report_type"] == "UPS"
    assert res["record_count"] == 1459
    assert res["metadata"].asset_code == "SR-E-AP-UPS-000009"

    rec = res["records"][0]
    rec.import_row_id = "ups-1"
    mapped = map_ups(rec)
    assert mapped["main_input_v_r"] is not None
    assert mapped["bypass_voltage"] is not None
    assert mapped["output_voltage"] is not None
    assert mapped["battery_vdc"] is not None


def test_ups_validation_and_kpis():
    service = ImportService()
    res = service.inspect(str(UPS_DIR / "UPSDailyLogReport_25thSep2026_2140_UPS Daily Log Report.csv"))
    readings = []
    for i, r in enumerate(res["records"]):
        r.import_row_id = f"ups-{i}"
        raw = map_ups(r)
        issues = validate_ups(raw)
        raw["data_quality_status"] = "VALID" if not issues else "EXCEPTION"
        readings.append(raw)

    kpis = calculate_ups_kpis_from_normalized(readings)
    assert kpis["valid_source_rows"] == 1459
    avail = next(k for k in kpis["results"] if k["kpi_code"] == "UPS-AV-01")
    assert avail["value"] == 100.0
