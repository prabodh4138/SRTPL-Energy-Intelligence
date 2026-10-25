from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "active_app"))

from import_engine.service import ImportService
from energy_validation.normalizer import NormalizationEngine

SOURCE = ROOT / "source_data" / "raw" / "EB" / "SRTPL_Test_JUNO_EB.csv"


def main():
    inspection = ImportService().inspect(str(SOURCE))
    assert inspection["report_type"] == "EB"
    assert inspection["record_count"] == 7

    engine = NormalizationEngine()
    previous = {}
    valid = 0
    exceptions = []
    kwh = kvah = kvarh = 0.0
    for rec in inspection["records"]:
        normalized, issues = engine.process("EB", rec.values, previous)
        previous = dict(rec.values)
        if issues:
            exceptions.extend(i.rule_code for i in issues)
            continue
        valid += 1
        kwh += float(normalized["interval_kwh"] or 0)
        kvah += float(normalized["interval_kvah"] or 0)
        kvarh += float(normalized["interval_kvarh"] or 0)

    assert valid == 5, valid
    assert len(exceptions) == 6, exceptions
    assert sorted(exceptions) == ["VAL-EB-001", "VAL-EB-001", "VAL-EB-002", "VAL-EB-002", "VAL-EB-004", "VAL-EB-004"]
    assert kwh == 125.0
    assert kvah == 125.0
    assert kvarh == 47.0

    print("PHASE 5.4 EB LOCAL VERIFICATION: PASS")
    print("parsed_rows: 7")
    print("valid_rows: 5")
    print("exception_rows: 2")
    print("EB validated consumption: 125.0 kWh")
    print("EB validated KVAH: 125.0 kVAH")
    print("EB validated KVARH: 47.0 kVARH")
    print("validation: PASS")
    print("KPI source calculation: PASS")


if __name__ == "__main__":
    main()
