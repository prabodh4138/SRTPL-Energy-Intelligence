import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "active_app"))

from import_engine.service import ImportService
from energy_validation.normalizer import NormalizationEngine
from analytics.solar_phase5_5 import calculate_solar_kpis_from_normalized

service = ImportService()
engine = NormalizationEngine()
sample_file = ROOT / "source_data" / "raw" / "Solar" / "Solar_Plant_Log_25thSep2026_2719_Solar Log.csv"

assert sample_file.exists(), f"Sample Solar file missing: {sample_file}"

inspection = service.inspect(str(sample_file))
assert inspection["report_type"] == "SOLAR"
assert inspection["record_count"] == 177
assert inspection["metadata"].asset_code == "SR-E-AP-SPX-000002"

previous = {}
normalized_readings = []
valid = 0
exceptions = 0
total_kwh = 0.0

for r in inspection["records"]:
    norm, issues = engine.process("SOLAR", r.values, previous)
    norm["reading_datetime"] = r.values.get("date")
    norm["data_quality_status"] = "VALID" if not issues else "EXCEPTION"
    normalized_readings.append(norm)
    previous = dict(r.values)
    if issues:
        exceptions += 1
    else:
        valid += 1
        if norm.get("interval_kwh") is not None:
            total_kwh += float(norm["interval_kwh"])

assert valid == 177
assert exceptions == 0
assert total_kwh == 14904.0

kpis = calculate_solar_kpis_from_normalized(normalized_readings)
assert kpis["valid_source_rows"] == 177
gen_kpi = next(r for r in kpis["results"] if r["kpi_code"] == "SOL-GEN-D")
assert gen_kpi["value"] == 14904.0

print("PHASE 5.5 SOLAR LOCAL VERIFICATION: PASS")
print(f"parsed_rows: {inspection['record_count']}")
print(f"valid_rows: {valid}")
print(f"exception_rows: {exceptions}")
print(f"Solar generation from validated intervals: {total_kwh} kWh")
print("raw_mapping: PASS")
print("normalization: PASS")
print("KPI calculation: PASS")
