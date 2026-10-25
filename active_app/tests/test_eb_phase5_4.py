from pathlib import Path

from import_engine.service import ImportService
from energy_validation.normalizer import NormalizationEngine

ROOT = Path(__file__).resolve().parents[2]
EB_DIR = ROOT / "source_data" / "raw" / "EB"


def test_all_supplied_eb_formats_are_detected():
    service = ImportService()
    expected = {
        "SRTPL_Test_JUNO_EB.csv": 7,
        "EBDailyLogReport_25thSep2026_2143_EB Log - Copy.csv": 23,
        "EB_Daily_Consumption_25thSep2026_6841_EB Daily.csv": 767,
    }
    for filename, rows in expected.items():
        result = service.inspect(str(EB_DIR / filename))
        assert result["report_type"] == "EB"
        assert result["record_count"] == rows


def test_controlled_eb_validation_and_kpis():
    service = ImportService()
    result = service.inspect(str(EB_DIR / "SRTPL_Test_JUNO_EB.csv"))
    engine = NormalizationEngine()
    previous = {}
    valid = 0
    exceptions = []
    kwh = kvah = kvarh = 0.0
    for record in result["records"]:
        normalized, issues = engine.process("EB", record.values, previous)
        previous = dict(record.values)
        if issues:
            exceptions.extend(issue.rule_code for issue in issues)
            continue
        valid += 1
        kwh += float(normalized["interval_kwh"] or 0)
        kvah += float(normalized["interval_kvah"] or 0)
        kvarh += float(normalized["interval_kvarh"] or 0)
    assert valid == 5
    assert len(exceptions) == 6
    assert kwh == 125.0
    assert kvah == 125.0
    assert kvarh == 47.0


def test_detailed_daily_eb_is_interval_not_cumulative():
    service = ImportService()
    result = service.inspect(str(EB_DIR / "EB_Daily_Consumption_25thSep2026_6841_EB Daily.csv"))
    first = result["records"][0].values
    assert first["date"] == first["period"]
    assert first["kwh"] == "640"
    assert first["kvah"] == "640"
    assert first["__source_mode"] == "INTERVAL_CONSUMPTION"
