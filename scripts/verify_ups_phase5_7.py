import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "active_app"))

from import_engine.service import ImportService
from supabase_import.raw_mapper import map_ups
from energy_validation.ups import validate_ups
from analytics.ups_phase5_7 import calculate_ups_kpis_from_normalized

service = ImportService()
sample_file = ROOT / "source_data" / "raw" / "UPS" / "UPSDailyLogReport_25thSep2026_2140_UPS Daily Log Report.csv"

assert sample_file.exists(), f"Sample UPS file missing: {sample_file}"

inspection = service.inspect(str(sample_file))
assert inspection["report_type"] == "UPS"
assert inspection["record_count"] == 1459
assert inspection["metadata"].asset_code == "SR-E-AP-UPS-000009"

valid = 0
exceptions = 0
normalized_readings = []

for i, r in enumerate(inspection["records"]):
    r.import_row_id = f"ups-{i}"
    raw = map_ups(r)
    issues = validate_ups(raw)
    raw["reading_datetime"] = raw.get("reading_datetime")
    raw["data_quality_status"] = "VALID" if not issues else "EXCEPTION"
    normalized_readings.append(raw)
    if issues:
        exceptions += 1
    else:
        valid += 1

assert valid == 1459
assert exceptions == 0

kpis = calculate_ups_kpis_from_normalized(normalized_readings)
assert kpis["valid_source_rows"] == 1459
avail = next(r for r in kpis["results"] if r["kpi_code"] == "UPS-AV-01")
assert avail["value"] == 100.0

print("PHASE 5.7 UPS LOCAL VERIFICATION: PASS")
print(f"parsed_rows: {inspection['record_count']}")
print(f"valid_rows: {valid}")
print(f"exception_rows: {exceptions}")
print(f"UPS Availability: {avail['value']}%")
print("raw_mapping: PASS")
print("normalization: PASS")
print("KPI calculation: PASS")
