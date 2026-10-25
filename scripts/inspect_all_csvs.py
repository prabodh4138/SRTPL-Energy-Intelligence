from pathlib import Path
import sys

sys.path.insert(0, "active_app")
from import_engine.service import ImportService

service = ImportService()
raw_dir = Path("source_data/raw")
for csv_file in sorted(raw_dir.rglob("*.csv")):
    try:
        res = service.inspect(str(csv_file))
        rtype = res["report_type"]
        rcnt = res["record_count"]
        asset = res["metadata"].asset_code
        print(f"[{rtype}] {csv_file.parent.name}/{csv_file.name} | Records: {rcnt} | Asset: {asset}")
    except Exception as e:
        print(f"[FAILED] {csv_file.parent.name}/{csv_file.name} -> {e}")
