import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv
ROOT=Path(__file__).resolve().parents[1]
load_dotenv(ROOT/'.env')
sys.path.insert(0,str(ROOT/'active_app'))
from supabase import create_client
from supabase_import.config import load_settings
from energy_validation.persistence import NormalizationPersistence
from analytics.dg_phase5_3 import calculate_dg_kpis

ap=argparse.ArgumentParser(); ap.add_argument('batch_id'); args=ap.parse_args()
settings=load_settings(); db=create_client(settings.supabase_url,settings.supabase_key)
summary=NormalizationPersistence(db,calculation_version='5.3').process_batch(args.batch_id,'DG')
kpis=calculate_dg_kpis(db,args.batch_id,'5.3')
print('PHASE 5.3 DG CALCULATION: SUCCESS')
print(f'batch_id: {args.batch_id}')
print(f'normalized_rows: {summary["normalized_rows"]}')
print(f'valid_source_rows: {summary["valid_rows"]}')
print(f'exception_rows_excluded: {summary["exception_rows"]}')
for x in kpis['results']:
    print(f'{x["kpi_code"]}: result_id={x["result_id"]}, action={x["action"]}, value={x["value"]}, unit={x["unit"]}')
print(f'calculation_version: {kpis["calculation_version"]}')
print(f'source_reading_ids: {",".join(kpis["source_reading_ids"])}')
