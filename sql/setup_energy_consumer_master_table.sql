-- ============================================================================
-- SRTPL POWER INTELLIGENCE — ENERGY CONSUMER & ASSET MAPPING MASTER TABLE
-- Target Project: Supabase (energy_master.consumer_account & public.energy_consumer_master)
--
-- EXACT SPECIFICATION:
-- Total 60 DISCOM Consumers:
--   - Exactly 3 HT (High Tension): Toll Plaza Main Substation Incomers (120 kW each)
--     * TP01: 416000000110 (SEED SAMBALPUR)
--     * TP02: 413000000002 (JED JHARSUGUDA)
--     * TP03: 813000000281 (SED SUNDARAGADA)
--   - Exactly 57 LT (Low Tension): Highway Corridor Lighting & Street Lights (4-34 kW)
--     * TP01: 19 LT connections
--     * TP02: 19 LT connections
--     * TP03: 19 LT connections
--
-- Direct Relational Integrity:
--   - Primary Master Table: energy_master.consumer_account
--   - Direct Relational Joins with public.energy_bills, public.energy_bills_provisional,
--     and public.payment_receipts via consumer_account_no.
--   - Telemetry join strictly on asset_code (eliminates Cartesian duplicate rows).
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE SCHEMA IF NOT EXISTS energy_master;

-- ----------------------------------------------------------------------------
-- STEP 1: CREATE MASTER TABLE IN energy_master
-- ----------------------------------------------------------------------------
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

-- Ensure all columns exist
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

-- Create Indexes for lightning fast lookups & joins
CREATE INDEX IF NOT EXISTS idx_consumer_account_asset ON energy_master.consumer_account(asset_code);
CREATE INDEX IF NOT EXISTS idx_consumer_account_plaza ON energy_master.consumer_account(toll_plaza_id);
CREATE INDEX IF NOT EXISTS idx_consumer_account_division ON energy_master.consumer_account(division_name);
CREATE INDEX IF NOT EXISTS idx_consumer_account_bill_type ON energy_master.consumer_account(bill_type);

-- ----------------------------------------------------------------------------
-- STEP 2: ENSURE MATCHING ASSETS EXIST IN energy_master.asset
-- ----------------------------------------------------------------------------
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
SET asset_code = EXCLUDED.asset_code,
    asset_name = EXCLUDED.asset_name,
    plaza_id = EXCLUDED.plaza_id;

-- ----------------------------------------------------------------------------
-- STEP 3: SEED MASTER CONSUMER DATA (EXACTLY 60 ACCOUNTS: 3 HT, 57 LT)
-- ----------------------------------------------------------------------------
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
-- STEP 5: DIRECT RELATIONAL VIEWS (BILLS & RECEIPTS RELATED TO CONSUMER MASTER)
-- ----------------------------------------------------------------------------
-- Direct relation between public.energy_bills and energy_master.consumer_account
CREATE OR REPLACE VIEW public.v_energy_bills_master AS
SELECT 
    b.*,
    m.toll_plaza_id AS master_toll_plaza_id,
    m.bill_type AS master_bill_type,
    m.asset_code AS master_asset_code,
    m.consumer_scope AS master_consumer_scope,
    m.division_name AS master_division_name,
    m.usage_type AS master_usage_type,
    m.sanctioned_load_kw AS master_sanctioned_load_kw,
    m.location AS master_location,
    m.is_active AS master_is_active
FROM public.energy_bills b
INNER JOIN energy_master.consumer_account m 
    ON b.consumer_account_no = m.consumer_account_no;

-- Direct relation between public.energy_bills_provisional and energy_master.consumer_account
CREATE OR REPLACE VIEW public.v_energy_bills_provisional_master AS
SELECT 
    bp.*,
    m.toll_plaza_id AS master_toll_plaza_id,
    m.bill_type AS master_bill_type,
    m.asset_code AS master_asset_code,
    m.consumer_scope AS master_consumer_scope,
    m.division_name AS master_division_name,
    m.usage_type AS master_usage_type,
    m.sanctioned_load_kw AS master_sanctioned_load_kw,
    m.location AS master_location,
    m.is_active AS master_is_active
FROM public.energy_bills_provisional bp
INNER JOIN energy_master.consumer_account m 
    ON bp.consumer_account_no = m.consumer_account_no;

-- ----------------------------------------------------------------------------
-- STEP 6: CORRELATED RECONCILIATION VIEW ACROSS ALL TABLES
-- ----------------------------------------------------------------------------
-- Joins Master Data (Primary Dimension) with:
-- 1. DISCOM Actual Energy Bills (public.energy_bills)
-- 2. DISCOM Provisional / Average Bills (public.energy_bills_provisional)
-- 3. JUNO Physical Meter Telemetry (energy_readings.eb / public.reading_eb)
-- 4. Payment Receipts (public.payment_receipts)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW public.v_energy_consumer_reconciliation AS
WITH bills_actual_agg AS (
    SELECT 
        consumer_account_no,
        COUNT(bill_number) AS actual_bills_count,
        MAX(bill_month) AS latest_actual_bill_month,
        SUM(COALESCE(slab_normal_kwh, 0) + COALESCE(slab_peak_kwh, 0) + COALESCE(slab_solar_kwh, 0)) AS actual_billed_kwh,
        SUM(COALESCE(current_total, 0)) AS actual_billed_amount,
        SUM(COALESCE(total_amount_payable, 0)) AS actual_amount_payable,
        MAX(created_at) AS latest_actual_bill_uploaded_at
    FROM public.energy_bills
    GROUP BY consumer_account_no
),
bills_prov_agg AS (
    SELECT 
        consumer_account_no,
        COUNT(bill_number) AS prov_bills_count,
        MAX(bill_month) AS latest_prov_bill_month,
        SUM(COALESCE(slab_normal_kwh, 0) + COALESCE(slab_peak_kwh, 0) + COALESCE(slab_solar_kwh, 0)) AS prov_billed_kwh,
        SUM(COALESCE(current_total, 0)) AS prov_billed_amount,
        SUM(COALESCE(total_amount_payable, 0)) AS prov_amount_payable,
        MAX(created_at) AS latest_prov_bill_uploaded_at
    FROM public.energy_bills_provisional
    GROUP BY consumer_account_no
),
readings_agg AS (
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

    -- DISCOM Actual vs. Provisional Bill Counts & Units
    COALESCE(ba.actual_bills_count, 0) AS actual_bills_count,
    COALESCE(bp.prov_bills_count, 0) AS provisional_bills_count,
    (COALESCE(ba.actual_bills_count, 0) + COALESCE(bp.prov_bills_count, 0)) AS total_bills_count,
    COALESCE(ba.latest_actual_bill_month, bp.latest_prov_bill_month, '—') AS latest_bill_month,
    COALESCE(ba.actual_billed_kwh, 0.0) AS actual_billed_kwh,
    COALESCE(bp.prov_billed_kwh, 0.0) AS provisional_billed_kwh,
    (COALESCE(ba.actual_billed_kwh, 0.0) + COALESCE(bp.prov_billed_kwh, 0.0)) AS discom_billed_kwh,

    -- Invoiced Amounts & Provisional Risk Exposure
    COALESCE(ba.actual_billed_amount, 0.0) AS actual_billed_amount,
    COALESCE(bp.prov_billed_amount, 0.0) AS provisional_exposure_amount,
    (COALESCE(ba.actual_billed_amount, 0.0) + COALESCE(bp.prov_billed_amount, 0.0)) AS discom_billed_amount,
    (COALESCE(ba.actual_amount_payable, 0.0) + COALESCE(bp.prov_amount_payable, 0.0)) AS discom_amount_payable,

    -- Payment Receipts & Balance Clearance Correlation
    COALESCE(r.total_receipts_count, 0) AS total_receipts_count,
    COALESCE(r.total_amount_paid, 0.0) AS total_amount_paid,
    COALESCE(r.latest_payment_date, '—') AS latest_payment_date,
    ((COALESCE(ba.actual_amount_payable, 0.0) + COALESCE(bp.prov_amount_payable, 0.0)) - COALESCE(r.total_amount_paid, 0.0)) AS outstanding_balance,
    CASE 
        WHEN ((COALESCE(ba.actual_amount_payable, 0.0) + COALESCE(bp.prov_amount_payable, 0.0)) - COALESCE(r.total_amount_paid, 0.0)) <= 1.0 AND COALESCE(r.total_amount_paid, 0.0) > 0 THEN 'PAID'
        WHEN COALESCE(r.total_amount_paid, 0.0) > 0 THEN 'PARTIAL'
        ELSE 'UNPAID'
    END AS payment_status,

    -- JUNO Physical Meter Telemetry Correlation (Strictly joined on asset_code)
    COALESCE(rd.total_meter_readings, 0) AS total_meter_readings,
    COALESCE(rd.total_meter_interval_kwh, 0.0) AS juno_meter_kwh,
    COALESCE(rd.latest_cumulative_kwh, 0.0) AS latest_cumulative_kwh,
    COALESCE(rd.max_recorded_demand_kw, 0.0) AS max_recorded_demand_kw,
    COALESCE(rd.avg_recorded_pf, 1.0) AS avg_recorded_pf,
    rd.latest_reading_datetime,

    -- Automated Reconciliation Variance (Metered kWh vs DISCOM Billed kWh)
    ((COALESCE(ba.actual_billed_kwh, 0.0) + COALESCE(bp.prov_billed_kwh, 0.0)) - COALESCE(rd.total_meter_interval_kwh, 0.0)) AS kwh_variance,
    CASE 
        WHEN (COALESCE(ba.actual_billed_kwh, 0.0) + COALESCE(bp.prov_billed_kwh, 0.0)) > 0 AND COALESCE(rd.total_meter_interval_kwh, 0.0) > 0 THEN
            ROUND(
                ABS((COALESCE(ba.actual_billed_kwh, 0.0) + COALESCE(bp.prov_billed_kwh, 0.0)) - COALESCE(rd.total_meter_interval_kwh, 0.0)) 
                / (COALESCE(ba.actual_billed_kwh, 0.0) + COALESCE(bp.prov_billed_kwh, 0.0)) * 100.0, 
                2
            )
        ELSE 0.0
    END AS variance_percentage,

    m.created_at,
    m.updated_at
FROM energy_master.consumer_account m
LEFT JOIN energy_master.plaza p ON m.toll_plaza_id = p.plaza_id
LEFT JOIN energy_master.asset a ON m.asset_code = a.asset_code
LEFT JOIN bills_actual_agg ba ON m.consumer_account_no = ba.consumer_account_no
LEFT JOIN bills_prov_agg bp ON m.consumer_account_no = bp.consumer_account_no
LEFT JOIN receipts_agg r ON m.consumer_account_no = r.account_key
LEFT JOIN readings_agg rd ON m.asset_code = rd.asset_code;

-- ----------------------------------------------------------------------------
-- STEP 7: ROW LEVEL SECURITY & PERMISSIONS
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
GRANT ALL ON VIEW public.v_energy_bills_master TO anon, authenticated, service_role, postgres, authenticator;
GRANT ALL ON VIEW public.v_energy_bills_provisional_master TO anon, authenticated, service_role, postgres, authenticator;
GRANT ALL ON VIEW public.v_energy_consumer_reconciliation TO anon, authenticated, service_role, postgres, authenticator;

-- ----------------------------------------------------------------------------
-- STEP 8: POSTGREST SCHEMA CACHE RELOAD
-- ----------------------------------------------------------------------------
NOTIFY pgrst, 'reload schema';
NOTIFY pgrst, 'reload config';
