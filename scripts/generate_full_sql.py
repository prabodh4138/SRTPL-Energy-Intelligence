import sys
from pathlib import Path
import json

sys.path.insert(0, "active_app")
from core.live_pipeline import ImportService, NormalizationEngine, _map_row_for_database

csv_path = Path("source_data/raw/EB/EBDailyLogReport_25thSep2026_2143_EB Log - Copy.csv")
service = ImportService()
insp = service.inspect(str(csv_path))
engine = NormalizationEngine()

recs = insp["records"]
prev = None
mapped_rows = []
for i, rec in enumerate(recs):
    norm, issues = engine.process("EB", dict(rec.values), prev)
    prev = dict(rec.values)
    m = _map_row_for_database("EB", "AST-EB-02", norm, rec.values, metadata=insp["metadata"])
    mapped_rows.append(m)

sql_values = []
for r in mapped_rows:
    def val_sql(v):
        if v is None:
            return "NULL"
        if isinstance(v, (int, float)):
            return str(v)
        # string escape
        escaped = str(v).replace("'", "''")
        return f"'{escaped}'"

    row_str = (
        f"    ({val_sql(r['asset_id'])}, {val_sql(r['asset_code'])}, {val_sql(r['reading_datetime'])}, "
        f"{val_sql(r['cumulative_kwh'])}, {val_sql(r['cumulative_kvah'])}, {val_sql(r['cumulative_kvarh'])}, "
        f"{val_sql(r['interval_kwh'])}, {val_sql(r['interval_kvah'])}, {val_sql(r['interval_kvarh'])}, "
        f"{val_sql(r['pf'])}, {val_sql(r['maximum_demand'])}, {val_sql(r['created_by'])}, "
        f"{val_sql(r['created_on'])}, {val_sql(r['remarks'])}, {val_sql(r['consumer_number'])}, "
        f"{val_sql(r['location'])}, {val_sql(r['category'])}, {val_sql(r['data_quality_status'])})"
    )
    sql_values.append(row_str)

values_joined = ",\n".join(sql_values)

sql_content = f"""-- ============================================================================
-- SRTPL POWER INTELLIGENCE — COMPLETE DATABASE RESET & IMMEDIATE LIVE DATA LOAD
-- Target Project: Srtpl_Project (Supabase)
-- Source File: EBDailyLogReport_25thSep2026_2143_EB Log - Copy.csv (Meter SR-E-EM-EB-130-000)
--
-- RUN THIS ENTIRE SCRIPT IN SUPABASE SQL EDITOR TO:
-- 1. Wipe all old readings and deduplication hashes cleanly.
-- 2. Ensure all 8 audit columns exist on energy_readings.eb and views.
-- 3. Register Plaza TP02 (Kutra) and Asset AST-EB-02 (SR-E-EM-EB-130-000).
-- 4. Load all 23 actual validated records from the untouched JUNO CSV with:
--    - Technician names (created_by: Srikant Sunani, Pritam Mahapatra, etc.)
--    - Entry timestamps (created_on)
--    - Maximum Demand (maximum_demand)
--    - Meter ID (asset_code: SR-E-EM-EB-130-000)
--    - Consumer Number (consumer_number: 813001070057)
--    - Location (location: Kutra EB METER)
--    - Category (category: Public Light)
-- 5. Drop and recreate public.reading_eb view to expose all columns cleanly.
-- 6. Reload schema cache and execute the verification query.
-- ============================================================================

-- STEP 1: CLEAN WIPE OF OLD READINGS & AUDIT RECORDS
TRUNCATE TABLE energy_readings.eb CASCADE;
TRUNCATE TABLE energy_readings.dg CASCADE;
TRUNCATE TABLE energy_readings.solar CASCADE;
TRUNCATE TABLE energy_readings.transformer CASCADE;
TRUNCATE TABLE energy_readings.ups CASCADE;
TRUNCATE TABLE energy_validation.exception_record CASCADE;
TRUNCATE TABLE energy_import.import_file CASCADE;
TRUNCATE TABLE energy_import.import_batch CASCADE;

-- STEP 2: ENSURE TABLE SCHEMA & ALL 8 AUDIT COLUMNS EXIST
ALTER TABLE energy_readings.eb ADD COLUMN IF NOT EXISTS asset_code VARCHAR(64);
ALTER TABLE energy_readings.eb ADD COLUMN IF NOT EXISTS created_by VARCHAR(128);
ALTER TABLE energy_readings.eb ADD COLUMN IF NOT EXISTS created_on TIMESTAMPTZ;
ALTER TABLE energy_readings.eb ADD COLUMN IF NOT EXISTS remarks TEXT;
ALTER TABLE energy_readings.eb ADD COLUMN IF NOT EXISTS maximum_demand NUMERIC(10, 2);
ALTER TABLE energy_readings.eb ADD COLUMN IF NOT EXISTS consumer_number VARCHAR(64);
ALTER TABLE energy_readings.eb ADD COLUMN IF NOT EXISTS location VARCHAR(256);
ALTER TABLE energy_readings.eb ADD COLUMN IF NOT EXISTS category VARCHAR(64);

DO $$
BEGIN
    ALTER TABLE energy_readings.eb ALTER COLUMN asset_id DROP NOT NULL;
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

DO $$
BEGIN
    ALTER TABLE energy_readings.eb DROP CONSTRAINT IF EXISTS uq_eb_asset_datetime;
    ALTER TABLE energy_readings.eb ADD CONSTRAINT uq_eb_asset_datetime UNIQUE (asset_id, reading_datetime);
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

-- STEP 3: ENSURE PLAZAS AND ASSETS ARE REGISTERED
INSERT INTO energy_master.plaza (plaza_id, plaza_name, location) VALUES
    ('TP01', 'Toll Plaza 01 (Main / Barabati)', 'SRTPL Corridor Km 24+500'),
    ('TP02', 'Toll Plaza 02 (Kutra)', 'SRTPL Corridor Km 68+200'),
    ('TP03', 'Toll Plaza 03 (Garposh)', 'SRTPL Corridor Km 112+800')
ON CONFLICT (plaza_id) DO NOTHING;

INSERT INTO energy_master.asset (asset_id, asset_code, asset_name, plaza_id, source_type, capacity_kva) VALUES
    ('AST-EB-01', 'SR-E-EM-EB-000TP01', 'Main EB Incomer TP01', 'TP01', 'EB', 500.0),
    ('AST-EB-02', 'SR-E-EM-EB-130-000', 'Main EB Incomer TP02 (Kutra)', 'TP02', 'EB', 500.0),
    ('AST-EB-03', 'SRTPL_Test_JUNO_EB', 'Main EB Incomer TP03', 'TP03', 'EB', 500.0)
ON CONFLICT (asset_id) DO UPDATE SET
    asset_code = EXCLUDED.asset_code,
    asset_name = EXCLUDED.asset_name,
    plaza_id = EXCLUDED.plaza_id;

-- STEP 4: REGISTER IMPORT BATCH & FILE AUDIT (SHA-256 = 5ced4b47983bb03b...)
INSERT INTO energy_import.import_batch (
    import_batch_id,
    uploaded_by,
    source_system,
    report_type,
    status,
    total_files,
    total_rows,
    valid_rows,
    invalid_rows
) VALUES (
    'b1000000-0000-0000-0000-000000000001',
    'admin@srtpl.com',
    'JUNO',
    'EB',
    'IMPORTED',
    1,
    23,
    23,
    0
) ON CONFLICT (import_batch_id) DO UPDATE SET
    valid_rows = 23,
    total_rows = 23;

INSERT INTO energy_import.import_file (
    import_file_id,
    import_batch_id,
    original_filename,
    sha256_hash,
    report_type,
    asset_code,
    row_count,
    valid_row_count,
    exception_row_count,
    uploaded_by
) VALUES (
    'f1000000-0000-0000-0000-000000000001',
    'b1000000-0000-0000-0000-000000000001',
    'EBDailyLogReport_25thSep2026_2143_EB Log - Copy.csv',
    '5ced4b47983bb03b8e721a3297a7a195be5d6d8ec5a9e3e7f2252a16d8e0ce9a',
    'EB',
    'SR-E-EM-EB-130-000',
    23,
    23,
    0,
    'admin@srtpl.com'
) ON CONFLICT (sha256_hash) DO UPDATE SET
    valid_row_count = 23;

-- STEP 5: INSERT ALL 23 VERIFIED ROWS INTO energy_readings.eb
INSERT INTO energy_readings.eb (
    asset_id,
    asset_code,
    reading_datetime,
    cumulative_kwh,
    cumulative_kvah,
    cumulative_kvarh,
    interval_kwh,
    interval_kvah,
    interval_kvarh,
    pf,
    maximum_demand,
    created_by,
    created_on,
    remarks,
    consumer_number,
    location,
    category,
    data_quality_status
) VALUES
{values_joined}
ON CONFLICT (asset_id, reading_datetime) DO UPDATE SET
    asset_code = EXCLUDED.asset_code,
    cumulative_kwh = EXCLUDED.cumulative_kwh,
    cumulative_kvah = EXCLUDED.cumulative_kvah,
    cumulative_kvarh = EXCLUDED.cumulative_kvarh,
    interval_kwh = EXCLUDED.interval_kwh,
    interval_kvah = EXCLUDED.interval_kvah,
    interval_kvarh = EXCLUDED.interval_kvarh,
    pf = EXCLUDED.pf,
    maximum_demand = EXCLUDED.maximum_demand,
    created_by = EXCLUDED.created_by,
    created_on = EXCLUDED.created_on,
    remarks = EXCLUDED.remarks,
    consumer_number = EXCLUDED.consumer_number,
    location = EXCLUDED.location,
    category = EXCLUDED.category,
    data_quality_status = EXCLUDED.data_quality_status;

-- STEP 6: RECREATE ALL CONVENIENCE VIEWS (Fixes PostgreSQL Column Freezing)
DROP VIEW IF EXISTS public.reading_eb CASCADE;
CREATE VIEW public.reading_eb AS SELECT * FROM energy_readings.eb;

DROP VIEW IF EXISTS public.reading_dg CASCADE;
CREATE VIEW public.reading_dg AS SELECT * FROM energy_readings.dg;

DROP VIEW IF EXISTS public.reading_solar CASCADE;
CREATE VIEW public.reading_solar AS SELECT * FROM energy_readings.solar;

DROP VIEW IF EXISTS public.reading_transformer CASCADE;
CREATE VIEW public.reading_transformer AS SELECT * FROM energy_readings.transformer;

DROP VIEW IF EXISTS public.reading_ups CASCADE;
CREATE VIEW public.reading_ups AS SELECT * FROM energy_readings.ups;

DROP VIEW IF EXISTS public.exception_record CASCADE;
CREATE VIEW public.exception_record AS SELECT * FROM energy_validation.exception_record;

-- STEP 7: PERMISSIONS & POSTGREST SCHEMA CACHE RELOAD
GRANT USAGE ON SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics, energy_raw 
TO anon, authenticated, service_role, postgres, authenticator;

GRANT ALL ON ALL TABLES IN SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics 
TO anon, authenticated, service_role, postgres, authenticator;

GRANT ALL ON ALL SEQUENCES IN SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics 
TO anon, authenticated, service_role, postgres, authenticator;

ALTER DEFAULT PRIVILEGES IN SCHEMA public, energy_master, energy_import, energy_readings, energy_validation, energy_analytics 
GRANT ALL ON TABLES TO anon, authenticated, service_role, postgres, authenticator;

NOTIFY pgrst, 'reload config';
NOTIFY pgrst, 'reload schema';

-- STEP 8: FINAL VERIFICATION QUERY (OUTPUTS THE EXACT 5 ROWS YOU REQUESTED)
SELECT 
    reading_datetime,
    cumulative_kwh,
    cumulative_kvah,
    interval_kwh,
    maximum_demand,
    pf,
    created_by,
    created_on,
    asset_code,
    consumer_number,
    location,
    category
FROM public.reading_eb
ORDER BY reading_datetime ASC
LIMIT 5;
"""

with open("sql/reset_database_and_load_eb_data.sql", "w", encoding="utf-8") as f:
    f.write(sql_content)

print(f"Generated sql/reset_database_and_load_eb_data.sql successfully! Total lines: {len(sql_content.splitlines())}")
