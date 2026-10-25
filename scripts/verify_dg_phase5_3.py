from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'active_app'))
from import_engine.parsers import parse_file
from supabase_import.raw_mapper import map_dg
from energy_validation.normalizer import NormalizationEngine

p=ROOT/'test_data'/'DGDailyLogReport_25thSep2026_443_DG Log.csv'
parsed=parse_file(str(p))
assert parsed.report_type=='DG'
assert len(parsed.records)==334
for i,rec in enumerate(parsed.records,1): rec.import_row_id=i
first=map_dg(parsed.records[0])
assert first['dg_id']=='SR-E-AP-DGX-000004'
assert first['reading_datetime']=='02-Apr-2026 10:25:00'
assert first['status']=='On'
assert first['voltage_ry']=='416'
assert first['current_r']=='63'
assert first['load_percent']=='80'
engine=NormalizationEngine(); previous={}; valid=[]; exceptions=[]
for rec in parsed.records:
    raw=map_dg(rec); n,issues=engine.process('DG',raw,previous)
    if issues: exceptions.append((rec.import_row_id,[i.rule_code for i in issues]))
    else: valid.append(n)
    previous=raw
assert len(valid)==329, len(valid)
assert len(exceptions)==5, exceptions
assert round(sum(float(x['interval_kwh']) for x in valid if x.get('interval_kwh') is not None),6)==9609.2
assert round(sum(float(x['interval_running_hours']) for x in valid if x.get('interval_running_hours') is not None),6)==1208.41
pf=[float(x['pf']) for x in valid if x.get('pf') is not None]
assert round(sum(pf)/len(pf),6)==0.980442
print('PHASE 5.3 DG LOCAL VERIFICATION: PASS')
print('parsed_rows: 334')
print('valid_rows: 329')
print('exception_rows: 5')
print('DG generation from validated intervals: 9609.2 kWh')
print('DG runtime from validated intervals: 1208.41 hour')
print('DG average PF: 0.980442')
print('raw_mapping: PASS')
print('normalization: PASS')
print('KPI calculation: PASS')
