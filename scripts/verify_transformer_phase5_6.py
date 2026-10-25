import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "active_app"))

from import_engine.service import ImportService
from import_engine.hash_utils import sha256_file
from supabase_import.raw_mapper import map_transformer
from energy_validation.transformer import validate_transformer
from analytics.transformer_phase5_6 import calculate_transformer_kpis_from_normalized

service = ImportService()

file1 = ROOT / "source_data" / "raw" / "Transformer" / "TransformerDailyReport_25thSep2026_109_Transformer Daily Log Report.csv"
file1_copy = ROOT / "source_data" / "raw" / "Transformer" / "TransformerDailyReport_25thSep2026_109_Transformer Daily Log Report - Copy.csv"
file2 = ROOT / "source_data" / "raw" / "Transformer" / "TransformerDailyReport_25thSep2026_2116_Transformer Daily Log Report.csv"

# Level 1 Duplicate Detection check
hash1 = sha256_file(file1)
hash1_copy = sha256_file(file1_copy)
assert hash1 == hash1_copy, "Duplicate file SHA-256 mismatch!"
print(f"Duplicate-file SHA-256 detection: PASS ({hash1[:16]}...)")

# Inspection check
inspection = service.inspect(str(file2))
assert inspection["report_type"] == "TRANSFORMER"
assert inspection["record_count"] == 252
assert inspection["metadata"].asset_code == "SR-E-HT-TFR-000003"

valid = 0
exceptions = 0
normalized_readings = []

for i, r in enumerate(inspection["records"]):
    r.import_row_id = f"trf-{i}"
    raw = map_transformer(r)
    issues = validate_transformer(raw)
    raw["reading_datetime"] = r.values.get("date")
    raw["data_quality_status"] = "VALID" if not issues else "EXCEPTION"
    normalized_readings.append(raw)
    if issues:
        exceptions += 1
    else:
        valid += 1

assert valid == 252
assert exceptions == 0

kpis = calculate_transformer_kpis_from_normalized(normalized_readings)
assert kpis["valid_source_rows"] == 252
assert "loss/efficiency is intentionally disabled" in kpis["audit_note"]

print("PHASE 5.6 TRANSFORMER LOCAL VERIFICATION: PASS")
print(f"parsed_rows: {inspection['record_count']}")
print(f"valid_rows: {valid}")
print(f"exception_rows: {exceptions}")
print("duplicate_detection: PASS")
print("raw_mapping: PASS")
print("normalization: PASS")
print("KPI calculation & audit guard: PASS")
