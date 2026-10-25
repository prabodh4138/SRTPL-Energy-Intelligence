-- ============================================================================
-- SRTPL POWER INTELLIGENCE — REAL-TIME DATABASE VIEWS & MASTER DATA
-- Target: Supabase / PostgreSQL (Self-Contained & Self-Healing: ZERO ERRORS)
--
-- Features:
-- 1. All prerequisite schemas & tables created IF NOT EXISTS with all columns
-- 2. Master Data Seeded (3 Toll Plazas, Assets, Exactly 60 Consumer Accounts: 3 HT, 57 LT)
-- 3. Drops existing views with CASCADE to prevent schema migration locks
-- 4. Creates Real-Time Database Views:
--    * public.v_energy_consumer_realtime       -> Real-time 360-degree consumer metrics across all 60 accounts
--    * public.v_energy_billing_kpis           -> Real-time executive KPIs (Plaza, Month, HT/LT, Basis, Payment)
--    * public.v_energy_bills_master           -> Direct relation: energy_bills + consumer_account + payment receipts
--    * public.v_energy_bills_provisional_master -> Direct relation: provisional/average bills + consumer_account
--    * public.v_missing_bills_realtime        -> Real-time detection of accounts missing bills per month
--    * public.v_energy_consumer_reconciliation-> Full telemetric reconciliation with JUNO meter readings
-- 5. Full RLS & Permissions granted to anon, authenticated, service_role, postgres, authenticator
-- 6. Reloads PostgREST schema cache
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- STEP 1: CREATE ALL REQUIRED SCHEMAS
CREATE SCHEMA IF NOT EXISTS energy_master;
CREATE SCHEMA IF NOT EXISTS energy_readings;
CREATE SCHEMA IF NOT EXISTS energy_import;
CREATE SCHEMA IF NOT EXISTS energy_validation;
CREATE SCHEMA IF NOT EXISTS energy_analytics;

-- Expose schemas in PostgREST configuration to eliminate PGRST205 errors
ALTER ROLE authenticator SET pgrst.db_schemas = 'public, energy_master, energy_readings, energy_import, energy_validation, energy_analytics';

-- ----------------------------------------------------------------------------
-- STEP 2: PREREQUISITE MASTER TABLES (Plaza, Asset, Consumer Account)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS energy_master.plaza (
    plaza_id VARCHAR(16) PRIMARY KEY,
    plaza_name VARCHAR(128) NOT NULL,
    location VARCHAR(256),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO energy_master.plaza (plaza_id, plaza_name, location, is_active)
VALUES
    ('TP01', 'Toll Plaza 01 - Sambalpur', 'Sambalpur - Km 24+500', true),
    ('TP02', 'Toll Plaza 02 - Jharsuguda', 'Jharsuguda - Km 68+200', true),
    ('TP03', 'Toll Plaza 03 - Sundargarh', 'Sundargarh / Garposh - Km 112+800', true)
ON CONFLICT (plaza_id) DO UPDATE 
SET plaza_name = EXCLUDED.plaza_name, location = EXCLUDED.location;

CREATE TABLE IF NOT EXISTS energy_master.asset (
    asset_id VARCHAR(64) PRIMARY KEY,
    asset_code VARCHAR(64) NOT NULL UNIQUE,
    asset_name VARCHAR(128) NOT NULL,
    plaza_id VARCHAR(16) REFERENCES energy_master.plaza(plaza_id) ON DELETE SET NULL,
    source_type VARCHAR(32) NOT NULL,
    capacity_kva NUMERIC(10, 2),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO energy_master.asset (asset_id, asset_code, asset_name, plaza_id, source_type, capacity_kva, is_active)
VALUES
    ('AST-EB-01', 'SR-E-EM-EB-000TP01', 'Main EB Incomer TP01 (Substation)', 'TP01', 'EB', 500.0, true),
    ('AST-EB-02', 'SR-E-EM-EB-000TP02', 'Main EB Incomer TP02 (Substation)', 'TP02', 'EB', 500.0, true),
    ('AST-EB-07', 'SR-E-EM-EB-000TP03', 'Main EB Incomer TP03 (Substation)', 'TP03', 'EB', 500.0, true),
    ('AST-EB-04', 'SR-E-EM-EB-5-200', 'Corridor Lighting Meter 05.200 (Ainthapalli)', 'TP01', 'EB', 50.0, true),
    ('AST-EB-05', 'SR-E-EM-EB-62-600', 'Corridor Lighting Meter 62.600 (Tangarpali)', 'TP02', 'EB', 50.0, true),
    ('AST-EB-06', 'SR-E-EM-EB-148-500', 'Corridor Lighting Meter 148.500 (Garposh)', 'TP03', 'EB', 50.0, true),
    ('AST-EB-08', 'SR-E-EM-EB-160-200', 'Garposh Toll Approach Meter', 'TP03', 'EB', 50.0, true),
    ('AST-EB-09', 'SR-E-EM-EB-130-000', 'Kutra EB Meter (Km 108+000)', 'TP02', 'EB', 50.0, true)
ON CONFLICT (asset_id) DO UPDATE 
SET asset_code = EXCLUDED.asset_code, asset_name = EXCLUDED.asset_name, plaza_id = EXCLUDED.plaza_id;

CREATE TABLE IF NOT EXISTS energy_master.consumer_account (
    consumer_account_no VARCHAR(64) PRIMARY KEY,
    toll_plaza_id VARCHAR(16) REFERENCES energy_master.plaza(plaza_id) ON DELETE SET NULL,
    bill_type VARCHAR(32) NOT NULL DEFAULT 'LT',
    asset_code VARCHAR(64) NOT NULL,
    consumer_scope VARCHAR(64) NOT NULL DEFAULT 'HIGHWAY',
    division_name VARCHAR(128) NOT NULL,
    usage_type VARCHAR(128) NOT NULL DEFAULT 'Public Light',
    sanctioned_load_kw NUMERIC(10, 2) NOT NULL DEFAULT 10.0,
    location VARCHAR(256) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    remarks TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Ensure all columns exist on consumer_account
ALTER TABLE energy_master.consumer_account ADD COLUMN IF NOT EXISTS toll_plaza_id VARCHAR(16);
ALTER TABLE energy_master.consumer_account ADD COLUMN IF NOT EXISTS bill_type VARCHAR(32) DEFAULT 'LT';
ALTER TABLE energy_master.consumer_account ADD COLUMN IF NOT EXISTS asset_code VARCHAR(64);
ALTER TABLE energy_master.consumer_account ADD COLUMN IF NOT EXISTS consumer_scope VARCHAR(64) DEFAULT 'HIGHWAY';
ALTER TABLE energy_master.consumer_account ADD COLUMN IF NOT EXISTS division_name VARCHAR(128);
ALTER TABLE energy_master.consumer_account ADD COLUMN IF NOT EXISTS usage_type VARCHAR(128) DEFAULT 'Public Light';
ALTER TABLE energy_master.consumer_account ADD COLUMN IF NOT EXISTS sanctioned_load_kw NUMERIC(10, 2) DEFAULT 10.0;
ALTER TABLE energy_master.consumer_account ADD COLUMN IF NOT EXISTS location VARCHAR(256);
ALTER TABLE energy_master.consumer_account ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
ALTER TABLE energy_master.consumer_account ADD COLUMN IF NOT EXISTS remarks TEXT;
ALTER TABLE energy_master.consumer_account ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE energy_master.consumer_account ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_consumer_account_asset ON energy_master.consumer_account(asset_code);
CREATE INDEX IF NOT EXISTS idx_consumer_account_plaza ON energy_master.consumer_account(toll_plaza_id);
CREATE INDEX IF NOT EXISTS idx_consumer_account_division ON energy_master.consumer_account(division_name);
CREATE INDEX IF NOT EXISTS idx_consumer_account_bill_type ON energy_master.consumer_account(bill_type);

-- Seed All 60 Consumer Accounts (3 HT Toll Plazas, 57 LT Corridor Lighting)
INSERT INTO energy_master.consumer_account (
    consumer_account_no, toll_plaza_id, bill_type, asset_code, consumer_scope, division_name, usage_type, sanctioned_load_kw, location, is_active, remarks
) VALUES
    ('416000000110', 'TP01', 'HT', 'SR-E-EM-EB-000TP01', 'TOLL_PLAZA', 'SEED SAMBALPUR', 'General Purpose', 120.0, 'TP-01 Main Substation Incomer (Km 24+500)', true, 'Main HT Substation Incomer for Toll Plaza 01'),
    ('411001070208', 'TP01', 'LT', 'SR-E-EM-EB-5-200', 'HIGHWAY', 'SED SAMBALPUR', 'Street Light', 10.0, 'Ainthapalli (Km 05+200)', true, 'TP01 Corridor LT Lighting - Ainthapalli (Km 05+200)'),
    ('411001070209', 'TP01', 'LT', 'SR-E-EM-EB-5-300', 'HIGHWAY', 'SED SAMBALPUR', 'Street Light', 15.0, 'Sambalpur Bypass (Km 05+300)', true, 'TP01 Corridor LT Lighting - Sambalpur Bypass (Km 05+300)'),
    ('416001070082', 'TP01', 'LT', 'SR-E-EM-EB-12-300', 'HIGHWAY', 'SEED SAMBALPUR', 'Public Light', 20.0, 'Rengali (Km 12+300)', true, 'TP01 Corridor LT Lighting - Rengali (Km 12+300)'),
    ('416001070084', 'TP01', 'LT', 'SR-E-EM-EB-24-500', 'HIGHWAY', 'SEED SAMBALPUR', 'Public Light', 16.0, 'Lapanga (Km 24+500)', true, 'TP01 Corridor LT Lighting - Lapanga (Km 24+500)'),
    ('416001070085', 'TP01', 'LT', 'SR-E-EM-EB-24-600', 'HIGHWAY', 'SEED SAMBALPUR', 'Public Light', 10.0, 'Lapanga Section 2 (Km 24+600)', true, 'TP01 Corridor LT Lighting - Lapanga Section 2 (Km 24+600)'),
    ('416001070086', 'TP01', 'LT', 'SR-E-EM-EB-36-800', 'HIGHWAY', 'SEED SAMBALPUR', 'Public Light', 20.0, 'Bhojpur (Km 36+800)', true, 'TP01 Corridor LT Lighting - Bhojpur (Km 36+800)'),
    ('416001070090', 'TP01', 'LT', 'SR-E-EM-EB-48-200', 'HIGHWAY', 'SEED SAMBALPUR', 'Public Light', 9.0, 'Kuchinda Road (Km 48+200)', true, 'TP01 Corridor LT Lighting - Kuchinda Road (Km 48+200)'),
    ('416001111004', 'TP01', 'LT', 'SR-E-EM-EB-24-500-LT', 'HIGHWAY', 'SEED SAMBALPUR', 'General Purpose', 4.0, 'Sambalpur Toll Admin (Km 24+500)', true, 'TP01 Corridor LT Lighting - Sambalpur Toll Admin (Km 24+500)'),
    ('411001070001', 'TP01', 'LT', 'SR-E-EM-EB-0-800', 'HIGHWAY', 'SED SAMBALPUR', 'Public Light', 10.0, 'Bareipali Junction (Km 00+800)', true, 'TP01 Corridor LT Lighting - Bareipali Junction (Km 00+800)'),
    ('411001070002', 'TP01', 'LT', 'SR-E-EM-EB-2-400', 'HIGHWAY', 'SED SAMBALPUR', 'Public Light', 12.0, 'Khetrajpur Crossing (Km 02+400)', true, 'TP01 Corridor LT Lighting - Khetrajpur Crossing (Km 02+400)'),
    ('411001070003', 'TP01', 'LT', 'SR-E-EM-EB-7-600', 'HIGHWAY', 'SED SAMBALPUR', 'Public Light', 10.0, 'Dhanupali High Mast (Km 07+600)', true, 'TP01 Corridor LT Lighting - Dhanupali High Mast (Km 07+600)'),
    ('416001070004', 'TP01', 'LT', 'SR-E-EM-EB-10-100', 'HIGHWAY', 'SEED SAMBALPUR', 'Public Light', 15.0, 'Thelkoli Chowk (Km 10+100)', true, 'TP01 Corridor LT Lighting - Thelkoli Chowk (Km 10+100)'),
    ('416001070005', 'TP01', 'LT', 'SR-E-EM-EB-15-400', 'HIGHWAY', 'SEED SAMBALPUR', 'Public Light', 10.0, 'Sason Underpass (Km 15+400)', true, 'TP01 Corridor LT Lighting - Sason Underpass (Km 15+400)'),
    ('416001070006', 'TP01', 'LT', 'SR-E-EM-EB-18-800', 'HIGHWAY', 'SEED SAMBALPUR', 'Public Light', 12.0, 'Katapali Flyover (Km 18+800)', true, 'TP01 Corridor LT Lighting - Katapali Flyover (Km 18+800)'),
    ('416001070007', 'TP01', 'LT', 'SR-E-EM-EB-21-200', 'HIGHWAY', 'SEED SAMBALPUR', 'Public Light', 10.0, 'Gunderpur Section (Km 21+200)', true, 'TP01 Corridor LT Lighting - Gunderpur Section (Km 21+200)'),
    ('416001070008', 'TP01', 'LT', 'SR-E-EM-EB-28-400', 'HIGHWAY', 'SEED SAMBALPUR', 'Public Light', 14.0, 'Rengali South (Km 28+400)', true, 'TP01 Corridor LT Lighting - Rengali South (Km 28+400)'),
    ('416001070009', 'TP01', 'LT', 'SR-E-EM-EB-32-100', 'HIGHWAY', 'SEED SAMBALPUR', 'Public Light', 10.0, 'Gharghunda Corridor (Km 32+100)', true, 'TP01 Corridor LT Lighting - Gharghunda Corridor (Km 32+100)'),
    ('416001070010', 'TP01', 'LT', 'SR-E-EM-EB-40-500', 'HIGHWAY', 'SEED SAMBALPUR', 'Public Light', 15.0, 'Bhojpur North (Km 40+500)', true, 'TP01 Corridor LT Lighting - Bhojpur North (Km 40+500)'),
    ('416001070011', 'TP01', 'LT', 'SR-E-EM-EB-44-300', 'HIGHWAY', 'SEED SAMBALPUR', 'Public Light', 10.0, 'Jujumura Crossing (Km 44+300)', true, 'TP01 Corridor LT Lighting - Jujumura Crossing (Km 44+300)'),
    ('413000000002', 'TP02', 'HT', 'SR-E-EM-EB-000TP02', 'TOLL_PLAZA', 'JED JHARSUGUDA', 'General Purpose', 120.0, 'TP-02 Main Substation Incomer (Km 68+200)', true, 'Main HT Substation Incomer for Toll Plaza 02'),
    ('413001070099', 'TP02', 'LT', 'SR-E-EM-EB-62-600', 'HIGHWAY', 'JED JHARSUGUDA', 'Street Light', 18.0, 'TANGARPALI (Km 62+600)', true, 'TP02 Corridor LT Lighting - TANGARPALI (Km 62+600)'),
    ('413001070102', 'TP02', 'LT', 'SR-E-EM-EB-112-800', 'HIGHWAY', 'JED JHARSUGUDA', 'Street Light', 14.0, 'Jharsuguda Bypass (Km 112+800)', true, 'TP02 Corridor LT Lighting - Jharsuguda Bypass (Km 112+800)'),
    ('413001070344', 'TP02', 'LT', 'SR-E-EM-EB-95-400', 'HIGHWAY', 'JED JHARSUGUDA', 'Street Light', 34.0, 'Badmal (Km 95+400)', true, 'TP02 Corridor LT Lighting - Badmal (Km 95+400)'),
    ('813001070057', 'TP02', 'LT', 'SR-E-EM-EB-130-000', 'HIGHWAY', 'KUTRA', 'Public Light', 15.0, 'Kutra EB METER (Km 108+000)', true, 'TP02 Corridor LT Lighting - Kutra EB METER (Km 108+000)'),
    ('413001070001', 'TP02', 'LT', 'SR-E-EM-EB-52-100', 'HIGHWAY', 'JED JHARSUGUDA', 'Public Light', 10.0, 'Durlaga Intersection (Km 52+100)', true, 'TP02 Corridor LT Lighting - Durlaga Intersection (Km 52+100)'),
    ('413001070002', 'TP02', 'LT', 'SR-E-EM-EB-56-400', 'HIGHWAY', 'JED JHARSUGUDA', 'Public Light', 12.0, 'Ekatali High Mast (Km 56+400)', true, 'TP02 Corridor LT Lighting - Ekatali High Mast (Km 56+400)'),
    ('413001070003', 'TP02', 'LT', 'SR-E-EM-EB-60-200', 'HIGHWAY', 'JED JHARSUGUDA', 'Public Light', 10.0, 'Tangarpali South (Km 60+200)', true, 'TP02 Corridor LT Lighting - Tangarpali South (Km 60+200)'),
    ('413001070004', 'TP02', 'LT', 'SR-E-EM-EB-65-800', 'HIGHWAY', 'JED JHARSUGUDA', 'Public Light', 15.0, 'Toll Plaza 02 Approach (Km 65+800)', true, 'TP02 Corridor LT Lighting - Toll Plaza 02 Approach (Km 65+800)'),
    ('413001070005', 'TP02', 'LT', 'SR-E-EM-EB-70-300', 'HIGHWAY', 'JED JHARSUGUDA', 'Public Light', 10.0, 'Brajrajnagar Crossing (Km 70+300)', true, 'TP02 Corridor LT Lighting - Brajrajnagar Crossing (Km 70+300)'),
    ('413001070006', 'TP02', 'LT', 'SR-E-EM-EB-74-600', 'HIGHWAY', 'JED JHARSUGUDA', 'Public Light', 12.0, 'Belpahar Chowk (Km 74+600)', true, 'TP02 Corridor LT Lighting - Belpahar Chowk (Km 74+600)'),
    ('413001070007', 'TP02', 'LT', 'SR-E-EM-EB-78-900', 'HIGHWAY', 'JED JHARSUGUDA', 'Public Light', 10.0, 'Bandhabahal Junction (Km 78+900)', true, 'TP02 Corridor LT Lighting - Bandhabahal Junction (Km 78+900)'),
    ('413001070008', 'TP02', 'LT', 'SR-E-EM-EB-83-200', 'HIGHWAY', 'JED JHARSUGUDA', 'Public Light', 15.0, 'Brundamal Section (Km 83+200)', true, 'TP02 Corridor LT Lighting - Brundamal Section (Km 83+200)'),
    ('413001070009', 'TP02', 'LT', 'SR-E-EM-EB-87-500', 'HIGHWAY', 'JED JHARSUGUDA', 'Public Light', 10.0, 'Paharsigida High Mast (Km 87+500)', true, 'TP02 Corridor LT Lighting - Paharsigida High Mast (Km 87+500)'),
    ('413001070010', 'TP02', 'LT', 'SR-E-EM-EB-91-800', 'HIGHWAY', 'JED JHARSUGUDA', 'Public Light', 12.0, 'Badmal South (Km 91+800)', true, 'TP02 Corridor LT Lighting - Badmal South (Km 91+800)'),
    ('413001070011', 'TP02', 'LT', 'SR-E-EM-EB-98-300', 'HIGHWAY', 'JED JHARSUGUDA', 'Public Light', 10.0, 'Kirmira Flyover (Km 98+300)', true, 'TP02 Corridor LT Lighting - Kirmira Flyover (Km 98+300)'),
    ('413001070012', 'TP02', 'LT', 'SR-E-EM-EB-101-500', 'HIGHWAY', 'JED JHARSUGUDA', 'Public Light', 10.0, 'Laikera Crossing (Km 101+500)', true, 'TP02 Corridor LT Lighting - Laikera Crossing (Km 101+500)'),
    ('413001070013', 'TP02', 'LT', 'SR-E-EM-EB-104-800', 'HIGHWAY', 'KUTRA', 'Public Light', 15.0, 'Kutra Approach (Km 104+800)', true, 'TP02 Corridor LT Lighting - Kutra Approach (Km 104+800)'),
    ('413001070014', 'TP02', 'LT', 'SR-E-EM-EB-107-200', 'HIGHWAY', 'KUTRA', 'Public Light', 12.0, 'Kolabira Junction (Km 107+200)', true, 'TP02 Corridor LT Lighting - Kolabira Junction (Km 107+200)'),
    ('413001070015', 'TP02', 'LT', 'SR-E-EM-EB-110-600', 'HIGHWAY', 'JED JHARSUGUDA', 'Public Light', 10.0, 'Jharsuguda North Link (Km 110+600)', true, 'TP02 Corridor LT Lighting - Jharsuguda North Link (Km 110+600)'),
    ('813000000281', 'TP03', 'HT', 'SR-E-EM-EB-000TP03', 'TOLL_PLAZA', 'SED SUNDARAGADA', 'General Purpose', 120.0, 'TP-03 Main Substation Incomer (Km 112+800)', true, 'Main HT Substation Incomer for Toll Plaza 03 (Garposh)'),
    ('812001070018', 'TP03', 'LT', 'SR-E-EM-EB-148-500', 'HIGHWAY', 'SED SUNDARAGADA', 'Public Light', 28.0, 'Bhawanipur / Garposh Corridor (Km 148+500)', true, 'TP03 Corridor LT Lighting - Bhawanipur / Garposh Corridor (Km 148+500)'),
    ('812001070020', 'TP03', 'LT', 'SR-E-EM-EB-160-200', 'HIGHWAY', 'SED SUNDARAGADA', 'Public Light', 15.0, 'Garposh Toll Approach (Km 160+200)', true, 'TP03 Corridor LT Lighting - Garposh Toll Approach (Km 160+200)'),
    ('812001070001', 'TP03', 'LT', 'SR-E-EM-EB-114-200', 'HIGHWAY', 'SED SUNDARAGADA', 'Public Light', 10.0, 'Sundargarh Entry (Km 114+200)', true, 'TP03 Corridor LT Lighting - Sundargarh Entry (Km 114+200)'),
    ('812001070002', 'TP03', 'LT', 'SR-E-EM-EB-117-600', 'HIGHWAY', 'SED SUNDARAGADA', 'Public Light', 12.0, 'Ujalpur Intersection (Km 117+600)', true, 'TP03 Corridor LT Lighting - Ujalpur Intersection (Km 117+600)'),
    ('812001070003', 'TP03', 'LT', 'SR-E-EM-EB-120-400', 'HIGHWAY', 'SED SUNDARAGADA', 'Public Light', 10.0, 'Tangarghat High Mast (Km 120+400)', true, 'TP03 Corridor LT Lighting - Tangarghat High Mast (Km 120+400)'),
    ('812001070004', 'TP03', 'LT', 'SR-E-EM-EB-124-800', 'HIGHWAY', 'SED SUNDARAGADA', 'Public Light', 15.0, 'Lefripada Crossing (Km 124+800)', true, 'TP03 Corridor LT Lighting - Lefripada Crossing (Km 124+800)'),
    ('812001070005', 'TP03', 'LT', 'SR-E-EM-EB-128-100', 'HIGHWAY', 'SED SUNDARAGADA', 'Public Light', 10.0, 'Dharuadihi Underpass (Km 128+100)', true, 'TP03 Corridor LT Lighting - Dharuadihi Underpass (Km 128+100)'),
    ('812001070006', 'TP03', 'LT', 'SR-E-EM-EB-132-500', 'HIGHWAY', 'SED SUNDARAGADA', 'Public Light', 12.0, 'Bargaon Junction (Km 132+500)', true, 'TP03 Corridor LT Lighting - Bargaon Junction (Km 132+500)'),
    ('812001070007', 'TP03', 'LT', 'SR-E-EM-EB-135-900', 'HIGHWAY', 'SED SUNDARAGADA', 'Public Light', 10.0, 'Subdega Crossing (Km 135+900)', true, 'TP03 Corridor LT Lighting - Subdega Crossing (Km 135+900)'),
    ('812001070008', 'TP03', 'LT', 'SR-E-EM-EB-139-200', 'HIGHWAY', 'SED SUNDARAGADA', 'Public Light', 14.0, 'Hemgir Section (Km 139+200)', true, 'TP03 Corridor LT Lighting - Hemgir Section (Km 139+200)'),
    ('812001070009', 'TP03', 'LT', 'SR-E-EM-EB-142-600', 'HIGHWAY', 'SED SUNDARAGADA', 'Public Light', 10.0, 'Garposh South Corridor (Km 142+600)', true, 'TP03 Corridor LT Lighting - Garposh South Corridor (Km 142+600)'),
    ('812001070010', 'TP03', 'LT', 'SR-E-EM-EB-145-800', 'HIGHWAY', 'SED SUNDARAGADA', 'Public Light', 12.0, 'Garposh Rail Overbridge (Km 145+800)', true, 'TP03 Corridor LT Lighting - Garposh Rail Overbridge (Km 145+800)'),
    ('812001070011', 'TP03', 'LT', 'SR-E-EM-EB-150-100', 'HIGHWAY', 'SED SUNDARAGADA', 'Public Light', 10.0, 'Bhawanipur High Mast (Km 150+100)', true, 'TP03 Corridor LT Lighting - Bhawanipur High Mast (Km 150+100)'),
    ('812001070012', 'TP03', 'LT', 'SR-E-EM-EB-152-700', 'HIGHWAY', 'SED SUNDARAGADA', 'Public Light', 12.0, 'Kutra-Garposh Link (Km 152+700)', true, 'TP03 Corridor LT Lighting - Kutra-Garposh Link (Km 152+700)'),
    ('812001070013', 'TP03', 'LT', 'SR-E-EM-EB-155-200', 'HIGHWAY', 'SED SUNDARAGADA', 'Public Light', 10.0, 'Sundargarh Bypass (Km 155+200)', true, 'TP03 Corridor LT Lighting - Sundargarh Bypass (Km 155+200)'),
    ('812001070014', 'TP03', 'LT', 'SR-E-EM-EB-157-800', 'HIGHWAY', 'SED SUNDARAGADA', 'Public Light', 15.0, 'Rourkela Border Approach (Km 157+800)', true, 'TP03 Corridor LT Lighting - Rourkela Border Approach (Km 157+800)'),
    ('812001070015', 'TP03', 'LT', 'SR-E-EM-EB-159-400', 'HIGHWAY', 'SED SUNDARAGADA', 'Public Light', 10.0, 'Sundargarh Admin Office (Km 159+400)', true, 'TP03 Corridor LT Lighting - Sundargarh Admin Office (Km 159+400)'),
    ('812001070016', 'TP03', 'LT', 'SR-E-EM-EB-161-100', 'HIGHWAY', 'SED SUNDARAGADA', 'Public Light', 12.0, 'Terminal Border Post (Km 161+100)', true, 'TP03 Corridor LT Lighting - Terminal Border Post (Km 161+100)'),
    ('812001070017', 'TP03', 'LT', 'SR-E-EM-EB-162-000', 'HIGHWAY', 'SED SUNDARAGADA', 'Public Light', 10.0, 'End of Concession Toll Link (Km 162+000)', true, 'TP03 Corridor LT Lighting - End of Concession Toll Link (Km 162+000)')
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
    remarks = EXCLUDED.remarks,
    updated_at = NOW();

-- ----------------------------------------------------------------------------
-- STEP 3: PREREQUISITE OPERATIONAL TABLES (energy_bills, energy_bills_provisional, payment_receipts, readings)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.energy_bills (
    bill_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_filename VARCHAR(256) NOT NULL,
    consumer_account_no VARCHAR(64),
    consumer_id VARCHAR(64),
    old_consumer_no VARCHAR(64),
    bill_number VARCHAR(64) UNIQUE,
    bill_month VARCHAR(32),
    bill_period VARCHAR(64),
    bill_days VARCHAR(16),
    bill_issue_date VARCHAR(32),
    due_date VARCHAR(32),
    rebate_date VARCHAR(32),
    tariff_category VARCHAR(64),
    tariff_type VARCHAR(64),
    division VARCHAR(128),
    sub_division VARCHAR(128),
    section VARCHAR(128),
    meter_sl_no VARCHAR(64),
    meter_rent_count VARCHAR(32),
    security_deposit NUMERIC(14, 2) DEFAULT 0.0,
    md_kw NUMERIC(10, 2) DEFAULT 0.0,
    md_kva NUMERIC(10, 2) DEFAULT 0.0,
    slab_normal_kwh NUMERIC(14, 2) DEFAULT 0.0,
    slab_peak_kwh NUMERIC(14, 2) DEFAULT 0.0,
    slab_solar_kwh NUMERIC(14, 2) DEFAULT 0.0,
    energy_charges NUMERIC(14, 2) DEFAULT 0.0,
    demand_charge NUMERIC(14, 2) DEFAULT 0.0,
    tod_incentive NUMERIC(14, 2) DEFAULT 0.0,
    tod_surcharge NUMERIC(14, 2) DEFAULT 0.0,
    electricity_charges NUMERIC(14, 2) DEFAULT 0.0,
    electricity_duty NUMERIC(14, 2) DEFAULT 0.0,
    meter_rent NUMERIC(14, 2) DEFAULT 0.0,
    customer_service_charge NUMERIC(14, 2) DEFAULT 0.0,
    dps_rs NUMERIC(14, 2) DEFAULT 0.0,
    current_total NUMERIC(14, 2) DEFAULT 0.0,
    prompt_rebate NUMERIC(14, 2) DEFAULT 0.0,
    total_amount_payable NUMERIC(14, 2) DEFAULT 0.0,
    net_after_rebate NUMERIC(14, 2) DEFAULT 0.0,
    cal_energy_charges NUMERIC(14, 2) DEFAULT 0.0,
    diff_energy_charges NUMERIC(14, 2) DEFAULT 0.0,
    cal_electricity_charges NUMERIC(14, 2) DEFAULT 0.0,
    diff_electricity_charges NUMERIC(14, 2) DEFAULT 0.0,
    cal_current_total NUMERIC(14, 2) DEFAULT 0.0,
    diff_current_total NUMERIC(14, 2) DEFAULT 0.0,
    verification_status VARCHAR(64) NOT NULL DEFAULT 'VERIFIED_MATCH',
    is_edited BOOLEAN NOT NULL DEFAULT FALSE,
    edited_by VARCHAR(128),
    edited_at TIMESTAMPTZ,
    edit_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Ensure all audit columns exist on energy_bills
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS bill_issue_date VARCHAR(32);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS due_date VARCHAR(32);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS rebate_date VARCHAR(32);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS tariff_type VARCHAR(64);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS md_kw NUMERIC(10, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS md_kva NUMERIC(10, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS demand_charge NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS tod_incentive NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS tod_surcharge NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS electricity_charges NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS electricity_duty NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS meter_rent NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS customer_service_charge NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS prompt_rebate NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS net_after_rebate NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS is_edited BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS edited_by VARCHAR(128);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS edited_at TIMESTAMPTZ;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS edit_notes TEXT;

CREATE TABLE IF NOT EXISTS public.energy_bills_provisional (
    bill_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_filename VARCHAR(256) NOT NULL,
    consumer_account_no VARCHAR(64),
    consumer_id VARCHAR(64),
    old_consumer_no VARCHAR(64),
    bill_number VARCHAR(64) UNIQUE,
    bill_month VARCHAR(32),
    bill_period VARCHAR(64),
    bill_days VARCHAR(16),
    bill_basis VARCHAR(32) NOT NULL DEFAULT 'AVERAGE',
    audit_flag TEXT,
    bill_issue_date VARCHAR(32),
    due_date VARCHAR(32),
    rebate_date VARCHAR(32),
    tariff_category VARCHAR(64),
    tariff_type VARCHAR(64),
    division VARCHAR(128),
    sub_division VARCHAR(128),
    section VARCHAR(128),
    meter_sl_no VARCHAR(64),
    meter_rent_count VARCHAR(32),
    security_deposit NUMERIC(14, 2) DEFAULT 0.0,
    md_kw NUMERIC(10, 2) DEFAULT 0.0,
    md_kva NUMERIC(10, 2) DEFAULT 0.0,
    slab_normal_kwh NUMERIC(14, 2) DEFAULT 0.0,
    slab_peak_kwh NUMERIC(14, 2) DEFAULT 0.0,
    slab_solar_kwh NUMERIC(14, 2) DEFAULT 0.0,
    energy_charges NUMERIC(14, 2) DEFAULT 0.0,
    demand_charge NUMERIC(14, 2) DEFAULT 0.0,
    tod_incentive NUMERIC(14, 2) DEFAULT 0.0,
    tod_surcharge NUMERIC(14, 2) DEFAULT 0.0,
    electricity_charges NUMERIC(14, 2) DEFAULT 0.0,
    electricity_duty NUMERIC(14, 2) DEFAULT 0.0,
    meter_rent NUMERIC(14, 2) DEFAULT 0.0,
    customer_service_charge NUMERIC(14, 2) DEFAULT 0.0,
    dps_rs NUMERIC(14, 2) DEFAULT 0.0,
    current_total NUMERIC(14, 2) DEFAULT 0.0,
    prompt_rebate NUMERIC(14, 2) DEFAULT 0.0,
    total_amount_payable NUMERIC(14, 2) DEFAULT 0.0,
    net_after_rebate NUMERIC(14, 2) DEFAULT 0.0,
    cal_energy_charges NUMERIC(14, 2) DEFAULT 0.0,
    diff_energy_charges NUMERIC(14, 2) DEFAULT 0.0,
    cal_electricity_charges NUMERIC(14, 2) DEFAULT 0.0,
    diff_electricity_charges NUMERIC(14, 2) DEFAULT 0.0,
    cal_current_total NUMERIC(14, 2) DEFAULT 0.0,
    diff_current_total NUMERIC(14, 2) DEFAULT 0.0,
    verification_status VARCHAR(64) NOT NULL DEFAULT 'PROVISIONAL_AVERAGE_AUDIT',
    is_edited BOOLEAN NOT NULL DEFAULT FALSE,
    edited_by VARCHAR(128),
    edited_at TIMESTAMPTZ,
    edit_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Ensure all columns on energy_bills_provisional
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS bill_basis VARCHAR(32) DEFAULT 'AVERAGE';
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS audit_flag TEXT;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS bill_issue_date VARCHAR(32);
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS due_date VARCHAR(32);
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS rebate_date VARCHAR(32);
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS tariff_type VARCHAR(64);
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS md_kw NUMERIC(10, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS md_kva NUMERIC(10, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS demand_charge NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS tod_incentive NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS tod_surcharge NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS electricity_charges NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS electricity_duty NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS meter_rent NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS customer_service_charge NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS prompt_rebate NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS net_after_rebate NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS is_edited BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS edited_by VARCHAR(128);
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS edited_at TIMESTAMPTZ;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS edit_notes TEXT;

CREATE TABLE IF NOT EXISTS public.payment_receipts (
    receipt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    receipt_no VARCHAR(64) NOT NULL UNIQUE,
    consumer_no VARCHAR(64),
    account_no VARCHAR(64),
    consumer_name VARCHAR(256),
    collections_date VARCHAR(32),
    amount_paid NUMERIC(14, 2) DEFAULT 0.0,
    payment_type VARCHAR(32),
    transaction_id VARCHAR(64),
    bill_month VARCHAR(32),
    category VARCHAR(64),
    source_pdf VARCHAR(256) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS energy_readings.eb (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) REFERENCES energy_master.asset(asset_id) ON DELETE SET NULL,
    asset_code VARCHAR(64) NOT NULL,
    consumer_number VARCHAR(64),
    reading_datetime TIMESTAMPTZ NOT NULL,
    cumulative_kwh NUMERIC(14, 2) NOT NULL DEFAULT 0.0,
    interval_kwh NUMERIC(14, 2) NOT NULL DEFAULT 0.0,
    maximum_demand NUMERIC(10, 2) DEFAULT 0.0,
    pf NUMERIC(4, 2) DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_reading_eb_asset_datetime UNIQUE (asset_code, reading_datetime)
);

CREATE INDEX IF NOT EXISTS idx_eb_readings_asset_code ON energy_readings.eb(asset_code);
CREATE INDEX IF NOT EXISTS idx_eb_readings_datetime ON energy_readings.eb(reading_datetime);

-- ----------------------------------------------------------------------------
-- STEP 4: SAFELY DROP EXISTING VIEWS WITH CASCADE (Eliminates column lock errors)
-- ----------------------------------------------------------------------------
DROP VIEW IF EXISTS public.v_energy_billing_kpis CASCADE;
DROP VIEW IF EXISTS public.v_energy_consumer_realtime CASCADE;
DROP VIEW IF EXISTS public.v_energy_bills_master CASCADE;
DROP VIEW IF EXISTS public.v_energy_bills_provisional_master CASCADE;
DROP VIEW IF EXISTS public.v_payment_receipts_master CASCADE;
DROP VIEW IF EXISTS public.v_missing_bills_realtime CASCADE;
DROP VIEW IF EXISTS public.v_energy_consumer_reconciliation CASCADE;
DROP VIEW IF EXISTS public.energy_consumer_master CASCADE;
DROP VIEW IF EXISTS public.consumer_account CASCADE;
DROP VIEW IF EXISTS public.reading_eb CASCADE;

-- Expose table views in public schema
CREATE VIEW public.energy_consumer_master AS SELECT * FROM energy_master.consumer_account;
CREATE VIEW public.consumer_account AS SELECT * FROM energy_master.consumer_account;
CREATE VIEW public.reading_eb AS SELECT * FROM energy_readings.eb;

-- ----------------------------------------------------------------------------
-- STEP 5: CREATE REAL-TIME DATABASE VIEWS
-- ----------------------------------------------------------------------------

-- ----------------------------------------------------------------------------
-- VIEW 1: v_energy_bills_master
-- Relates public.energy_bills with energy_master.consumer_account
-- Correlates payments with payment_receipts in real time
-- ----------------------------------------------------------------------------
CREATE VIEW public.v_energy_bills_master AS
WITH receipt_match AS (
    SELECT 
        COALESCE(TRIM(account_no), TRIM(consumer_no)) AS ac_no,
        TRIM(bill_month) AS b_mo,
        SUM(COALESCE(amount_paid, 0)) AS total_paid,
        MAX(collections_date) AS latest_payment_date
    FROM public.payment_receipts
    GROUP BY COALESCE(TRIM(account_no), TRIM(consumer_no)), TRIM(bill_month)
)
SELECT 
    b.bill_id,
    b.bill_number,
    b.consumer_account_no,
    b.source_filename,
    m.toll_plaza_id,
    m.bill_type,
    m.asset_code,
    m.consumer_scope,
    m.division_name,
    m.usage_type,
    m.sanctioned_load_kw,
    m.location,
    b.bill_month,
    b.bill_period,
    b.bill_days,
    'ACTUAL' AS bill_basis,
    false AS is_provisional_or_average,
    COALESCE(b.slab_normal_kwh, 0) AS slab_normal_kwh,
    COALESCE(b.slab_peak_kwh, 0) AS slab_peak_kwh,
    COALESCE(b.slab_solar_kwh, 0) AS slab_solar_kwh,
    (COALESCE(b.slab_normal_kwh, 0) + COALESCE(b.slab_peak_kwh, 0) + COALESCE(b.slab_solar_kwh, 0)) AS total_billed_kwh,
    COALESCE(b.energy_charges, 0) AS energy_charges,
    COALESCE(b.demand_charge, 0) AS demand_charge,
    COALESCE(b.tod_incentive, 0) AS tod_incentive,
    COALESCE(b.tod_surcharge, 0) AS tod_surcharge,
    COALESCE(b.electricity_charges, 0) AS electricity_charges,
    COALESCE(b.electricity_duty, 0) AS electricity_duty,
    COALESCE(b.current_total, 0) AS current_total,
    COALESCE(b.prompt_rebate, 0) AS prompt_rebate,
    COALESCE(b.total_amount_payable, b.current_total, 0) AS total_amount_payable,
    COALESCE(r.total_paid, 0) AS amount_paid,
    GREATEST(0.0, COALESCE(b.total_amount_payable, b.current_total, 0) - COALESCE(r.total_paid, 0)) AS outstanding_balance,
    CASE 
        WHEN (COALESCE(b.total_amount_payable, b.current_total, 0) - COALESCE(r.total_paid, 0)) <= 1.0 AND COALESCE(r.total_paid, 0) > 0 THEN 'PAID'
        WHEN COALESCE(r.total_paid, 0) > 0 THEN 'PARTIAL'
        ELSE 'UNPAID'
    END AS payment_status,
    'GENERATED' AS bill_present,
    r.latest_payment_date,
    b.verification_status,
    b.is_edited,
    b.created_at
FROM public.energy_bills b
INNER JOIN energy_master.consumer_account m 
    ON TRIM(b.consumer_account_no) = TRIM(m.consumer_account_no)
LEFT JOIN receipt_match r 
    ON TRIM(b.consumer_account_no) = r.ac_no AND TRIM(b.bill_month) = r.b_mo;

-- ----------------------------------------------------------------------------
-- VIEW 2: v_energy_bills_provisional_master
-- Relates public.energy_bills_provisional with energy_master.consumer_account
-- ----------------------------------------------------------------------------
CREATE VIEW public.v_energy_bills_provisional_master AS
WITH receipt_match AS (
    SELECT 
        COALESCE(TRIM(account_no), TRIM(consumer_no)) AS ac_no,
        TRIM(bill_month) AS b_mo,
        SUM(COALESCE(amount_paid, 0)) AS total_paid,
        MAX(collections_date) AS latest_payment_date
    FROM public.payment_receipts
    GROUP BY COALESCE(TRIM(account_no), TRIM(consumer_no)), TRIM(bill_month)
)
SELECT 
    bp.bill_id,
    bp.bill_number,
    bp.consumer_account_no,
    bp.source_filename,
    m.toll_plaza_id,
    m.bill_type,
    m.asset_code,
    m.consumer_scope,
    m.division_name,
    m.usage_type,
    m.sanctioned_load_kw,
    m.location,
    bp.bill_month,
    bp.bill_period,
    bp.bill_days,
    UPPER(COALESCE(bp.bill_basis, 'AVERAGE')) AS bill_basis,
    true AS is_provisional_or_average,
    bp.audit_flag,
    COALESCE(bp.slab_normal_kwh, 0) AS slab_normal_kwh,
    COALESCE(bp.slab_peak_kwh, 0) AS slab_peak_kwh,
    COALESCE(bp.slab_solar_kwh, 0) AS slab_solar_kwh,
    (COALESCE(bp.slab_normal_kwh, 0) + COALESCE(bp.slab_peak_kwh, 0) + COALESCE(bp.slab_solar_kwh, 0)) AS total_billed_kwh,
    COALESCE(bp.energy_charges, 0) AS energy_charges,
    COALESCE(bp.demand_charge, 0) AS demand_charge,
    COALESCE(bp.tod_incentive, 0) AS tod_incentive,
    COALESCE(bp.tod_surcharge, 0) AS tod_surcharge,
    COALESCE(bp.current_total, 0) AS current_total,
    COALESCE(bp.total_amount_payable, bp.current_total, 0) AS total_amount_payable,
    COALESCE(r.total_paid, 0) AS amount_paid,
    GREATEST(0.0, COALESCE(bp.total_amount_payable, bp.current_total, 0) - COALESCE(r.total_paid, 0)) AS outstanding_balance,
    CASE 
        WHEN (COALESCE(bp.total_amount_payable, bp.current_total, 0) - COALESCE(r.total_paid, 0)) <= 1.0 AND COALESCE(r.total_paid, 0) > 0 THEN 'PAID'
        WHEN COALESCE(r.total_paid, 0) > 0 THEN 'PARTIAL'
        ELSE 'UNPAID'
    END AS payment_status,
    'GENERATED' AS bill_present,
    r.latest_payment_date,
    bp.verification_status,
    bp.is_edited,
    bp.created_at
FROM public.energy_bills_provisional bp
INNER JOIN energy_master.consumer_account m 
    ON TRIM(bp.consumer_account_no) = TRIM(m.consumer_account_no)
LEFT JOIN receipt_match r 
    ON TRIM(bp.consumer_account_no) = r.ac_no AND TRIM(bp.bill_month) = r.b_mo;

-- ----------------------------------------------------------------------------
-- VIEW 3: v_energy_consumer_realtime
-- Real-time 360-degree Consumer View across all 60 registered accounts
-- ----------------------------------------------------------------------------
CREATE VIEW public.v_energy_consumer_realtime AS
WITH bills_actual_summary AS (
    SELECT 
        TRIM(consumer_account_no) AS ac_no,
        COUNT(bill_number) AS actual_bills_count,
        MAX(bill_month) AS latest_actual_month,
        SUM(COALESCE(slab_normal_kwh, 0) + COALESCE(slab_peak_kwh, 0) + COALESCE(slab_solar_kwh, 0)) AS actual_billed_kwh,
        SUM(COALESCE(current_total, 0)) AS actual_billed_amount,
        SUM(COALESCE(total_amount_payable, current_total, 0)) AS actual_amount_payable
    FROM public.energy_bills
    GROUP BY TRIM(consumer_account_no)
),
bills_prov_summary AS (
    SELECT 
        TRIM(consumer_account_no) AS ac_no,
        COUNT(bill_number) AS prov_bills_count,
        MAX(bill_month) AS latest_prov_month,
        SUM(COALESCE(slab_normal_kwh, 0) + COALESCE(slab_peak_kwh, 0) + COALESCE(slab_solar_kwh, 0)) AS prov_billed_kwh,
        SUM(COALESCE(current_total, 0)) AS prov_billed_amount,
        SUM(COALESCE(total_amount_payable, current_total, 0)) AS prov_amount_payable
    FROM public.energy_bills_provisional
    GROUP BY TRIM(consumer_account_no)
),
receipts_summary AS (
    SELECT 
        COALESCE(TRIM(account_no), TRIM(consumer_no)) AS ac_no,
        COUNT(receipt_no) AS total_receipts_count,
        SUM(COALESCE(amount_paid, 0)) AS total_amount_paid,
        MAX(collections_date) AS latest_payment_date
    FROM public.payment_receipts
    GROUP BY COALESCE(TRIM(account_no), TRIM(consumer_no))
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
    m.remarks,

    -- Counts & Coverage
    COALESCE(ba.actual_bills_count, 0) AS actual_bills_count,
    COALESCE(bp.prov_bills_count, 0) AS provisional_bills_count,
    (COALESCE(ba.actual_bills_count, 0) + COALESCE(bp.prov_bills_count, 0)) AS total_bills_count,
    COALESCE(ba.latest_actual_month, bp.latest_prov_month, '—') AS latest_bill_month,
    CASE 
        WHEN (COALESCE(ba.actual_bills_count, 0) + COALESCE(bp.prov_bills_count, 0)) > 0 THEN 'GENERATED'
        ELSE 'NOT GENERATED'
    END AS bill_present,

    -- Units (kWh)
    COALESCE(ba.actual_billed_kwh, 0.0) AS actual_billed_kwh,
    COALESCE(bp.prov_billed_kwh, 0.0) AS provisional_billed_kwh,
    (COALESCE(ba.actual_billed_kwh, 0.0) + COALESCE(bp.prov_billed_kwh, 0.0)) AS discom_billed_kwh,

    -- Financial Amounts (₹)
    COALESCE(ba.actual_billed_amount, 0.0) AS actual_billed_amount,
    COALESCE(bp.prov_billed_amount, 0.0) AS provisional_exposure_amount,
    (COALESCE(ba.actual_billed_amount, 0.0) + COALESCE(bp.prov_billed_amount, 0.0)) AS discom_billed_amount,
    (COALESCE(ba.actual_amount_payable, 0.0) + COALESCE(bp.prov_amount_payable, 0.0)) AS discom_amount_payable,

    -- Receipts Clearance
    COALESCE(r.total_receipts_count, 0) AS total_receipts_count,
    COALESCE(r.total_amount_paid, 0.0) AS total_amount_paid,
    COALESCE(r.latest_payment_date, '—') AS latest_payment_date,
    GREATEST(0.0, (COALESCE(ba.actual_amount_payable, 0.0) + COALESCE(bp.prov_amount_payable, 0.0)) - COALESCE(r.total_amount_paid, 0.0)) AS outstanding_balance,
    CASE 
        WHEN (COALESCE(ba.actual_bills_count, 0) + COALESCE(bp.prov_bills_count, 0)) = 0 THEN 'NOT GENERATED'
        WHEN GREATEST(0.0, (COALESCE(ba.actual_amount_payable, 0.0) + COALESCE(bp.prov_amount_payable, 0.0)) - COALESCE(r.total_amount_paid, 0.0)) <= 1.0 AND COALESCE(r.total_amount_paid, 0.0) > 0 THEN 'PAID'
        WHEN COALESCE(r.total_amount_paid, 0.0) > 0 THEN 'PARTIAL'
        ELSE 'UNPAID'
    END AS payment_status,

    m.created_at,
    m.updated_at
FROM energy_master.consumer_account m
LEFT JOIN energy_master.plaza p ON m.toll_plaza_id = p.plaza_id
LEFT JOIN energy_master.asset a ON m.asset_code = a.asset_code
LEFT JOIN bills_actual_summary ba ON TRIM(m.consumer_account_no) = ba.ac_no
LEFT JOIN bills_prov_summary bp ON TRIM(m.consumer_account_no) = bp.ac_no
LEFT JOIN receipts_summary r ON TRIM(m.consumer_account_no) = r.ac_no;

-- ----------------------------------------------------------------------------
-- VIEW 4: v_energy_billing_kpis
-- Real-time Executive Billing KPI Aggregations (Plaza, Month, HT/LT, Basis, Status)
-- ----------------------------------------------------------------------------
CREATE VIEW public.v_energy_billing_kpis AS
WITH all_bills_union AS (
    SELECT 
        bill_number, consumer_account_no, toll_plaza_id, bill_type, consumer_scope, division_name,
        bill_month, bill_basis, is_provisional_or_average, total_billed_kwh, current_total, total_amount_payable,
        amount_paid, outstanding_balance, payment_status
    FROM public.v_energy_bills_master
    UNION ALL
    SELECT 
        bill_number, consumer_account_no, toll_plaza_id, bill_type, consumer_scope, division_name,
        bill_month, bill_basis, is_provisional_or_average, total_billed_kwh, current_total, total_amount_payable,
        amount_paid, outstanding_balance, payment_status
    FROM public.v_energy_bills_provisional_master
)
SELECT 
    toll_plaza_id,
    bill_month,
    bill_type,
    bill_basis,
    payment_status,
    COUNT(bill_number) AS total_bills_count,
    COUNT(DISTINCT consumer_account_no) AS unique_consumers_count,
    SUM(total_billed_kwh) AS total_billed_kwh,
    SUM(current_total) AS total_invoiced_amount,
    SUM(total_amount_payable) AS total_amount_payable,
    SUM(amount_paid) AS total_amount_paid,
    SUM(outstanding_balance) AS total_outstanding_balance,
    ROUND(
        CASE 
            WHEN SUM(total_amount_payable) > 0 THEN (SUM(amount_paid) / SUM(total_amount_payable) * 100.0)
            ELSE 100.0 
        END, 
        2
    ) AS realization_rate_pct,
    ROUND(
        CASE 
            WHEN SUM(total_billed_kwh) > 0 THEN (SUM(total_amount_payable) / SUM(total_billed_kwh))
            ELSE 0.0 
        END, 
        2
    ) AS effective_cost_per_kwh
FROM all_bills_union
GROUP BY toll_plaza_id, bill_month, bill_type, bill_basis, payment_status;

-- ----------------------------------------------------------------------------
-- VIEW 5: v_missing_bills_realtime
-- Detects missing bills across the 60 consumers for active billing months
-- ----------------------------------------------------------------------------
CREATE VIEW public.v_missing_bills_realtime AS
WITH active_months AS (
    SELECT DISTINCT TRIM(bill_month) AS bill_month FROM public.energy_bills WHERE bill_month IS NOT NULL AND TRIM(bill_month) <> ''
    UNION
    SELECT DISTINCT TRIM(bill_month) AS bill_month FROM public.energy_bills_provisional WHERE bill_month IS NOT NULL AND TRIM(bill_month) <> ''
),
present_pairs AS (
    SELECT DISTINCT TRIM(consumer_account_no) AS ac_no, TRIM(bill_month) AS b_mo FROM public.energy_bills WHERE bill_month IS NOT NULL
    UNION
    SELECT DISTINCT TRIM(consumer_account_no) AS ac_no, TRIM(bill_month) AS b_mo FROM public.energy_bills_provisional WHERE bill_month IS NOT NULL
)
SELECT 
    m.consumer_account_no,
    m.toll_plaza_id,
    m.bill_type,
    m.asset_code,
    m.consumer_scope,
    m.division_name,
    m.usage_type,
    m.sanctioned_load_kw,
    m.location,
    mo.bill_month,
    'NOT GENERATED' AS bill_present,
    'UNPAID' AS payment_status,
    0.0 AS total_billed_kwh,
    0.0 AS total_amount_payable,
    0.0 AS amount_paid,
    0.0 AS outstanding_balance,
    '⚠️ Follow up with DISCOM / Ingest Bill PDF' AS action_required
FROM energy_master.consumer_account m
CROSS JOIN active_months mo
LEFT JOIN present_pairs pp 
    ON TRIM(m.consumer_account_no) = pp.ac_no AND mo.bill_month = pp.b_mo
WHERE pp.ac_no IS NULL;

-- ----------------------------------------------------------------------------
-- VIEW 6: v_energy_consumer_reconciliation
-- Telemetric meter vs DISCOM billing reconciliation (strictly joined on asset_code)
-- ----------------------------------------------------------------------------
CREATE VIEW public.v_energy_consumer_reconciliation AS
WITH readings_agg AS (
    SELECT 
        asset_code,
        COUNT(reading_id) AS total_meter_readings,
        MAX(reading_datetime) AS latest_reading_datetime,
        MAX(COALESCE(cumulative_kwh, 0)) AS latest_cumulative_kwh,
        SUM(COALESCE(interval_kwh, 0)) AS total_meter_interval_kwh,
        MAX(COALESCE(maximum_demand, 0)) AS max_recorded_demand_kw,
        AVG(COALESCE(pf, 1.0)) AS avg_recorded_pf
    FROM energy_readings.eb
    GROUP BY asset_code
)
SELECT 
    cr.*,
    COALESCE(rd.total_meter_readings, 0) AS total_meter_readings,
    COALESCE(rd.total_meter_interval_kwh, 0.0) AS juno_meter_kwh,
    COALESCE(rd.latest_cumulative_kwh, 0.0) AS latest_cumulative_kwh,
    COALESCE(rd.max_recorded_demand_kw, 0.0) AS max_recorded_demand_kw,
    COALESCE(rd.avg_recorded_pf, 1.0) AS avg_recorded_pf,
    rd.latest_reading_datetime,
    (cr.discom_billed_kwh - COALESCE(rd.total_meter_interval_kwh, 0.0)) AS kwh_variance,
    CASE 
        WHEN cr.discom_billed_kwh > 0 AND COALESCE(rd.total_meter_interval_kwh, 0.0) > 0 THEN
            ROUND(
                ABS(cr.discom_billed_kwh - COALESCE(rd.total_meter_interval_kwh, 0.0)) / cr.discom_billed_kwh * 100.0, 
                2
            )
        ELSE 0.0
    END AS variance_percentage
FROM public.v_energy_consumer_realtime cr
LEFT JOIN readings_agg rd ON cr.asset_code = rd.asset_code;

-- ----------------------------------------------------------------------------
-- STEP 6: ROW LEVEL SECURITY & OPEN ACCESS POLICIES
-- ----------------------------------------------------------------------------
ALTER TABLE energy_master.plaza ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_master.asset ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_master.consumer_account ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.energy_bills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.energy_bills_provisional ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payment_receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_readings.eb ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "allow_all_plaza" ON energy_master.plaza;
CREATE POLICY "allow_all_plaza" ON energy_master.plaza FOR ALL TO anon, authenticated, service_role, postgres USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_asset" ON energy_master.asset;
CREATE POLICY "allow_all_asset" ON energy_master.asset FOR ALL TO anon, authenticated, service_role, postgres USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_consumer_account" ON energy_master.consumer_account;
CREATE POLICY "allow_all_consumer_account" ON energy_master.consumer_account FOR ALL TO anon, authenticated, service_role, postgres USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_energy_bills" ON public.energy_bills;
CREATE POLICY "allow_all_energy_bills" ON public.energy_bills FOR ALL TO anon, authenticated, service_role, postgres USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_energy_bills_provisional" ON public.energy_bills_provisional;
CREATE POLICY "allow_all_energy_bills_provisional" ON public.energy_bills_provisional FOR ALL TO anon, authenticated, service_role, postgres USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_payment_receipts" ON public.payment_receipts;
CREATE POLICY "allow_all_payment_receipts" ON public.payment_receipts FOR ALL TO anon, authenticated, service_role, postgres USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "allow_all_reading_eb" ON energy_readings.eb;
CREATE POLICY "allow_all_reading_eb" ON energy_readings.eb FOR ALL TO anon, authenticated, service_role, postgres USING (true) WITH CHECK (true);

-- ----------------------------------------------------------------------------
-- STEP 7: GRANTS & PERMISSIONS
-- ----------------------------------------------------------------------------
GRANT USAGE ON SCHEMA public, energy_master, energy_readings, energy_import, energy_validation, energy_analytics 
TO anon, authenticated, service_role, postgres, authenticator;

GRANT ALL ON ALL TABLES IN SCHEMA public, energy_master, energy_readings, energy_import, energy_validation, energy_analytics 
TO anon, authenticated, service_role, postgres, authenticator;

GRANT ALL ON ALL SEQUENCES IN SCHEMA public, energy_master, energy_readings 
TO anon, authenticated, service_role, postgres, authenticator;

-- ----------------------------------------------------------------------------
-- STEP 8: POSTGREST SCHEMA CACHE RELOAD
-- ----------------------------------------------------------------------------
NOTIFY pgrst, 'reload schema';
NOTIFY pgrst, 'reload config';

DO $$
BEGIN
    RAISE NOTICE 'SUCCESS: Real-time database views, 60 consumer accounts (3 HT, 57 LT), and full RLS policies created with ZERO ERRORS!';
END $$;
