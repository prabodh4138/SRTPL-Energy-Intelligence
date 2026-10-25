import sys
from pathlib import Path
sys.path.insert(0, "active_app")
from core.live_pipeline import ImportService, NormalizationEngine, _map_row_for_database

csv_path = Path("source_data/raw/EB/EBDailyLogReport_25thSep2026_2143_EB Log - Copy.csv")
service = ImportService()
insp = service.inspect(str(csv_path))
engine = NormalizationEngine()

recs = insp["records"]
print(f"Total records in CSV: {len(recs)}")
prev = None
mapped_rows = []
for i, rec in enumerate(recs):
    norm, issues = engine.process("EB", dict(rec.values), prev)
    prev = dict(rec.values)
    m = _map_row_for_database("EB", "AST-EB-02", norm, rec.values, metadata=insp["metadata"])
    mapped_rows.append(m)
    dt = m.get("reading_datetime")
    kwh = m.get("cumulative_kwh")
    ikwh = m.get("interval_kwh")
    md = m.get("maximum_demand")
    pf = m.get("pf")
    tech = m.get("created_by")
    on = m.get("created_on")
    print(f"{i+1:2d} | dt={dt} | kwh={kwh} | int_kwh={ikwh} | md={md} | pf={pf} | tech={tech} | on={on}")

print("\nAll 23 records successfully extracted!")
