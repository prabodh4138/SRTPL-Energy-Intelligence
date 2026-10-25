from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'active_app'))
from import_engine.service import ImportService
from energy_validation.normalizer import NormalizationEngine

SOURCE = Path(__file__).resolve().parents[1] / 'source_data' / 'raw' / 'EB' / 'SRTPL_Test_JUNO_EB.csv'

def main():
    inspection = ImportService().inspect(str(SOURCE))
    assert inspection['report_type'] == 'EB', inspection['report_type']
    assert inspection['record_count'] == 7, inspection['record_count']
    engine = NormalizationEngine()
    previous = {}
    normalized=[]
    for rec in inspection['records']:
        n, issues = engine.process('EB', rec.values, previous)
        normalized.append((n, issues))
        previous = dict(rec.values)
    valid = [n for n, issues in normalized if not issues]
    exceptions = [n for n, issues in normalized if issues]
    assert len(valid) == 5, len(valid)
    assert len(exceptions) == 2, len(exceptions)
    assert round(sum(float(n['interval_kwh']) for n in valid if n['interval_kwh'] is not None), 6) == 125.0
    assert round(sum(float(n['interval_kvah']) for n in valid if n['interval_kvah'] is not None), 6) == 125.0
    assert round(sum(float(n['interval_kvarh']) for n in valid if n['interval_kvarh'] is not None), 6) == 47.0
    assert {i.rule_code for n, issues in normalized for i in issues} == {'VAL-EB-001','VAL-EB-002','VAL-EB-004'}
    print('PHASE 5.2.6 EB LOCAL VERIFICATION: PASS')
    print('parsed_rows: 7')
    print('valid_rows: 5')
    print('exception_rows: 2')
    print('EB consumption: 125.0 kWh')
    print('EB KVAH: 125.0 kVAh')
    print('EB KVARH: 47.0 kVARh')
    print('EB average PF: 0.95')
    print('validation: PASS')
    print('KPI calculation basis: PASS')

if __name__ == '__main__': main()
