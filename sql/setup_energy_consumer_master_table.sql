-- ============================================================================
-- SRTPL POWER INTELLIGENCE — ENERGY CONSUMER & ASSET MAPPING MASTER TABLE
-- Target Project: Supabase (energy_master.consumer_account & public.energy_consumer_master)
--
-- Master table mapping DISCOM Consumer Accounts to Toll Plazas, Asset Codes,
-- Meter Readings, Bill Types, Divisions, and Highway Locations.
-- Provides automated correlation across:
-- 1. DISCOM Energy Bills (public.energy_bills)
-- 2. JUNO Physical Meter Telemetry (energy_readings.eb / public.reading_eb)
-- 3. Payment Receipts (public.payment_receipts)
-- 4. Toll Plazas & Equipment Assets (energy_master.plaza, energy_master.asset)
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE SCHEMA IF NOT EXISTS energy_master;

-- ----------------------------------------------------------------------------
-- STEP 1: CREATE MASTER TABLE IN energy_master
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS energy_master.consumer_account (
    consumer_account_no VARCHAR(64) PRIMARY KEY,
    toll_plaza_id VARCHAR(16) REFERENCES energy_master.plaza(plaza_id) ON DELETE SET NULL,
    bill_type VARCHAR(32) NOT NULL DEFAULT 'HT',
    asset_code VARCHAR(64) NOT NULL,
    consumer_scope VARCHAR(64) NOT NULL DEFAULT 'HIGHWAY',
    division_name VARCHAR(128) NOT NULL,
    usage_type VARCHAR(128) NOT NULL DEFAULT 'Street Light',
    sanctioned_load_kw NUMERIC(10, 2) NOT NULL DEFAULT 0.0,
    location VARCHAR(256) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    remarks TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Ensure all columns exist if table was already created
ALTER TABLE energy_master.consumer_account ADD COLUMN IF NOT EXISTS toll_plaza_id VARCHAR(16);
ALTER TABLE energy_master.consumer_account ADD COLUMN IF NOT EXISTS bill_type VARCHAR(32) DEFAULT 'HT';
ALTER TABLE energy_master.consumer_account ADD COLUMN IF NOT EXISTS asset_code VARCHAR(64);
ALTER TABLE energy_master.consumer_account ADD COLUMN IF NOT EXISTS consumer_scope VARCHAR(64) DEFAULT 'HIGHWAY';
ALTER TABLE energy_master.consumer_account ADD COLUMN IF NOT EXISTS division_name VARCHAR(128);
ALTER TABLE energy_master.consumer_account ADD COLUMN IF NOT EXISTS usage_type VARCHAR(128) DEFAULT 'Street Light';
ALTER TABLE energy_master.consumer_account ADD COLUMN IF NOT EXISTS sanctioned_load_kw NUMERIC(10, 2) DEFAULT 0.0;
ALTER TABLE energy_master.consumer_account ADD COLUMN IF NOT EXISTS location VARCHAR(256);
ALTER TABLE energy_master.consumer_account ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
ALTER TABLE energy_master.consumer_account ADD COLUMN IF NOT EXISTS remarks TEXT;
ALTER TABLE energy_master.consumer_account ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE energy_master.consumer_account ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Create Indexes for lightning fast lookups & joins
CREATE INDEX IF NOT EXISTS idx_consumer_account_asset ON energy_master.consumer_account(asset_code);
CREATE INDEX IF NOT EXISTS idx_consumer_account_plaza ON energy_master.consumer_account(toll_plaza_id);
CREATE INDEX IF NOT EXISTS idx_consumer_account_division ON energy_master.consumer_account(division_name);

-- ----------------------------------------------------------------------------
-- STEP 2: ENSURE MATCHING ASSETS EXIST IN energy_master.asset
-- ----------------------------------------------------------------------------
INSERT INTO energy_master.asset (asset_id, asset_code, asset_name, plaza_id, source_type, capacity_kva, is_active)
VALUES
    ('AST-EB-04', 'SR-E-EM-EB-5-200', 'Corridor Lighting Meter 05.200 (Ainthapalli)', 'TP01', 'EB', 50.0, true),
    ('AST-EB-05', 'SR-E-EM-EB-62-600', 'Corridor Lighting Meter 62.600 (Tangarpali)', 'TP02', 'EB', 50.0, true)
ON CONFLICT (asset_id) DO UPDATE 
SET asset_code = EXCLUDED.asset_code,
    asset_name = EXCLUDED.asset_name,
    plaza_id = EXCLUDED.plaza_id;

-- ----------------------------------------------------------------------------
-- STEP 3: SEED MASTER CONSUMER DATA (INCLUDING USER PROVIDED ROWS)
-- ----------------------------------------------------------------------------
INSERT INTO energy_master.consumer_account (
    consumer_account_no, toll_plaza_id, bill_type, asset_code, consumer_scope, division_name, usage_type, sanctioned_load_kw, location, is_active
) VALUES
    -- User Specified Master Rows
    ('411001070208', 'TP01', 'HT', 'SR-E-EM-EB-5-200', 'HIGHWAY', 'SED', 'Street Light', 10.0, 'Ainthapalli', true),
    ('413001070099', 'TP02', 'HT', 'SR-E-EM-EB-62-600', 'HIGHWAY', 'JED', 'Street Light', 18.0, 'TANGARPALI', true),
    
    -- Additional Corridor & Plaza Connections
    ('416000000110', 'TP01', 'HT', 'SR-E-EM-EB-000TP01', 'TOLL_PLAZA', 'SEED SAMBALPUR', 'General Purpose', 120.0, 'TP-01 EB Meter', true),
    ('813001070057', 'TP02', 'LT', 'SR-E-EM-EB-130-000', 'HIGHWAY', 'KUTRA', 'Public Light', 15.0, 'Kutra EB METER', true),
    ('413001070102', 'TP02', 'HT', 'SR-E-EM-EB-112-800', 'HIGHWAY', 'JED JHARSUGUDA', 'Street Light', 14.0, 'Jharsuguda Bypass', true),
    ('413001070344', 'TP02', 'HT', 'SR-E-EM-EB-95-400', 'HIGHWAY', 'JED JHARSUGUDA', 'Street Light', 12.0, 'Badmal', true),
    ('416001070082', 'TP01', 'HT', 'SR-E-EM-EB-12-300', 'HIGHWAY', 'SEED SAMBALPUR', 'Public Light', 10.0, 'Rengali', true),
    ('416001070084', 'TP01', 'HT', 'SR-E-EM-EB-24-500', 'HIGHWAY', 'SEED SAMBALPUR', 'Public Light', 10.0, 'Lapanga', true),
    ('416001070086', 'TP01', 'HT', 'SR-E-EM-EB-36-800', 'HIGHWAY', 'SEED SAMBALPUR', 'Public Light', 10.0, 'Bhojpur', true),
    ('416001070090', 'TP01', 'HT', 'SR-E-EM-EB-48-200', 'HIGHWAY', 'SEED SAMBALPUR', 'Public Light', 10.0, 'Kuchinda Road', true)
ON CONFLICT (consumer_account_no) DO UPDATE 
SET toll_plaza_id = EXCLUDED.toll_plaza_id,
    bill_type = EXCLUDED.bill_type,
    asset_code = EXCLUDED.asset_code,
    consumer_scope = EXCLUDED.consumer_scope,
    division_name = EXCLUDED.division_name,
    usage_type = EXCLUDED.usage_type,
    sanctioned_load_kw = EXCLUDED.sanctioned_load_kw,
    location = EXCLUDED.location,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

-- ----------------------------------------------------------------------------
-- STEP 4: EXPOSE PUBLIC CONVENIENCE VIEWS & SYNONYMS
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW public.energy_consumer_master AS 
SELECT 
    consumer_account_no,
    toll_plaza_id,
    bill_type,
    asset_code,
    consumer_scope,
    division_name,
    usage_type,
    sanctioned_load_kw,
    location,
    is_active,
    remarks,
    created_at,
    updated_at
FROM energy_master.consumer_account;

CREATE OR REPLACE VIEW public.consumer_account AS 
SELECT * FROM energy_master.consumer_account;

-- ----------------------------------------------------------------------------
-- STEP 5: CORRELATED RECONCILIATION VIEW ACROSS ALL TABLES
-- ----------------------------------------------------------------------------
-- Joins Master Data with:
-- 1. DISCOM Energy Bills (total billed amount, total units, latest bill month)
-- 2. JUNO Physical Meter Telemetry (total metered kWh, latest reading, pf)
-- 3. Payment Receipts (total amount paid, last payment date)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW public.v_energy_consumer_reconciliation AS
WITH bills_agg AS (
    SELECT 
        consumer_account_no,
        COUNT(bill_number) AS total_bills_count,
        MAX(bill_month) AS latest_bill_month,
        SUM(COALESCE(slab_normal_kwh, 0) + COALESCE(slab_peak_kwh, 0) + COALESCE(slab_solar_kwh, 0)) AS total_billed_kwh,
        SUM(COALESCE(current_total, 0)) AS total_billed_amount,
        SUM(COALESCE(total_amount_payable, 0)) AS total_amount_payable,
        MAX(created_at) AS latest_bill_uploaded_at
    FROM public.energy_bills
    GROUP BY consumer_account_no
),
readings_agg AS (
    SELECT 
        COALESCE(consumer_number, asset_code) AS account_or_asset,
        asset_code,
        COUNT(reading_id) AS total_meter_readings,
        MAX(reading_datetime) AS latest_reading_datetime,
        MAX(COALESCE(cumulative_kwh, 0)) AS latest_cumulative_kwh,
        SUM(COALESCE(interval_kwh, 0)) AS total_meter_interval_kwh,
        MAX(COALESCE(maximum_demand, 0)) AS max_recorded_demand_kw,
        AVG(COALESCE(pf, 1.0)) AS avg_recorded_pf
    FROM energy_readings.eb
    GROUP BY COALESCE(consumer_number, asset_code), asset_code
),
receipts_agg AS (
    SELECT 
        COALESCE(account_no, consumer_no) AS account_key,
        COUNT(receipt_no) AS total_receipts_count,
        SUM(COALESCE(amount_paid, 0)) AS total_amount_paid,
        MAX(collections_date) AS latest_payment_date
    FROM public.payment_receipts
    GROUP BY COALESCE(account_no, consumer_no)
)
SELECT 
    m.consumer_account_no,
    m.toll_plaza_id,
    p.plaza_name,
    m.bill_type,
    m.asset_code,
    a.asset_name,
    m.consumer_scope,
    m.division_name,
    m.usage_type,
    m.sanctioned_load_kw,
    m.location,
    m.is_active,

    -- DISCOM Bill Correlation
    COALESCE(b.total_bills_count, 0) AS total_bills_count,
    COALESCE(b.latest_bill_month, '—') AS latest_bill_month,
    COALESCE(b.total_billed_kwh, 0.0) AS discom_billed_kwh,
    COALESCE(b.total_billed_amount, 0.0) AS discom_billed_amount,
    COALESCE(b.total_amount_payable, 0.0) AS discom_amount_payable,

    -- Payment Receipts Correlation
    COALESCE(r.total_receipts_count, 0) AS total_receipts_count,
    COALESCE(r.total_amount_paid, 0.0) AS total_amount_paid,
    COALESCE(r.latest_payment_date, '—') AS latest_payment_date,
    (COALESCE(b.total_billed_amount, 0.0) - COALESCE(r.total_amount_paid, 0.0)) AS outstanding_balance,

    -- JUNO Physical Meter Correlation
    COALESCE(rd.total_meter_readings, 0) AS total_meter_readings,
    COALESCE(rd.total_meter_interval_kwh, 0.0) AS juno_meter_kwh,
    COALESCE(rd.latest_cumulative_kwh, 0.0) AS latest_cumulative_kwh,
    COALESCE(rd.max_recorded_demand_kw, 0.0) AS max_recorded_demand_kw,
    COALESCE(rd.avg_recorded_pf, 1.0) AS avg_recorded_pf,
    rd.latest_reading_datetime,

    -- Automated Reconciliation Variance (Metered kWh vs DISCOM Billed kWh)
    (COALESCE(b.total_billed_kwh, 0.0) - COALESCE(rd.total_meter_interval_kwh, 0.0)) AS kwh_variance,
    CASE 
        WHEN COALESCE(b.total_billed_kwh, 0.0) > 0 AND COALESCE(rd.total_meter_interval_kwh, 0.0) > 0 THEN
            ROUND(
                ABS(COALESCE(b.total_billed_kwh, 0.0) - COALESCE(rd.total_meter_interval_kwh, 0.0)) 
                / COALESCE(b.total_billed_kwh, 1.0) * 100.0, 
                2
            )
        ELSE 0.0
    END AS variance_percentage,

    m.created_at,
    m.updated_at
FROM energy_master.consumer_account m
LEFT JOIN energy_master.plaza p ON m.toll_plaza_id = p.plaza_id
LEFT JOIN energy_master.asset a ON m.asset_code = a.asset_code
LEFT JOIN bills_agg b ON m.consumer_account_no = b.consumer_account_no
LEFT JOIN receipts_agg r ON m.consumer_account_no = r.account_key
LEFT JOIN readings_agg rd ON (m.asset_code = rd.asset_code OR m.consumer_account_no = rd.account_or_asset);

-- ----------------------------------------------------------------------------
-- STEP 6: ROW LEVEL SECURITY & PERMISSIONS
-- ----------------------------------------------------------------------------
ALTER TABLE energy_master.consumer_account ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "allow_all_consumer_account" ON energy_master.consumer_account;
CREATE POLICY "allow_all_consumer_account" ON energy_master.consumer_account 
FOR ALL TO anon, authenticated, service_role, postgres 
USING (true) WITH CHECK (true);

GRANT USAGE ON SCHEMA energy_master, public TO anon, authenticated, service_role, postgres, authenticator;
GRANT ALL ON TABLE energy_master.consumer_account TO anon, authenticated, service_role, postgres, authenticator;
GRANT ALL ON VIEW public.energy_consumer_master TO anon, authenticated, service_role, postgres, authenticator;
GRANT ALL ON VIEW public.consumer_account TO anon, authenticated, service_role, postgres, authenticator;
GRANT ALL ON VIEW public.v_energy_consumer_reconciliation TO anon, authenticated, service_role, postgres, authenticator;

-- ----------------------------------------------------------------------------
-- STEP 7: POSTGREST SCHEMA CACHE RELOAD
-- ----------------------------------------------------------------------------
NOTIFY pgrst, 'reload schema';
NOTIFY pgrst, 'reload config';
