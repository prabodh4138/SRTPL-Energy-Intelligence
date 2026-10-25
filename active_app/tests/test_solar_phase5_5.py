from pathlib import Path
from import_engine.service import ImportService
from energy_validation.normalizer import NormalizationEngine
from analytics.solar_phase5_5 import calculate_solar_kpis_from_normalized

ROOT = Path(__file__).resolve().parents[2]
SOLAR_DIR = ROOT / "source_data" / "raw" / "Solar"


def test_all_supplied_solar_formats_are_detected():
    service = ImportService()
    expected = {
        "Solar_Plant_Log_25thSep2026_2719_Solar Log.csv": (177, "SR-E-AP-SPX-000002"),
        "Solar_Plant_Log_25thSep2026_2764_Solar Log.csv": (175, "SR-E-AP-SPX-000003"),
        "Solar_Plant_Log_25thSep2026_4168_Solar Log.csv": (167, "SR-E-AP-SPX-000001"),
    }
    for filename, (rows, asset) in expected.items():
        result = service.inspect(str(SOLAR_DIR / filename))
        assert result["report_type"] == "SOLAR"
        assert result["record_count"] == rows
        assert result["metadata"].asset_code == asset


def test_solar_normalization_and_kpi():
    service = ImportService()
    result = service.inspect(str(SOLAR_DIR / "Solar_Plant_Log_25thSep2026_2719_Solar Log.csv"))
    engine = NormalizationEngine()
    previous = {}
    normalized_list = []
    for r in result["records"]:
        norm, issues = engine.process("SOLAR", r.values, previous)
        norm["reading_datetime"] = r.values.get("date")
        norm["data_quality_status"] = "VALID" if not issues else "EXCEPTION"
        normalized_list.append(norm)
        previous = dict(r.values)

    kpis = calculate_solar_kpis_from_normalized(normalized_list)
    assert kpis["valid_source_rows"] == 177
    assert kpis["exception_rows_excluded"] == 0
    gen = next(k for k in kpis["results"] if k["kpi_code"] == "SOL-GEN-D")
    assert gen["value"] == 14904.0
