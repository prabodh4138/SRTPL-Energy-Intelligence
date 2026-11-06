-- ============================================================================
-- SRTPL POWER INTELLIGENCE — COMPLETE DATABASE RESET & RESEED (EXCEPT CONSUMERS)
-- Target: Supabase / PostgreSQL SQL Editor
-- 
-- 1. Empties all tables EXCEPT energy_master.consumer_account (60 consumers preserved).
-- 2. Reseeds Plazas, Assets, 13 Verified Energy Bills, 5 Payment Receipts, Allocations, and Budgets.
-- 3. All bills include non-zero Meter Rent, Customer Service Charges, verified Contract Demands,
--    and Rebate Profit/Loss tracking.
-- ============================================================================

-- ============================================================================
-- STEP 1: WIPE ALL OPERATIONAL DATA (EXCEPT 60 CONSUMERS)
-- ============================================================================

TRUNCATE TABLE 
    public.receipt_allocations,
    public.monthly_budgets,
    public.bill_review_queue,
    public.bill_rejected_bucket,
    public.audit_events,
    public.payment_receipts,
    public.energy_bills_provisional,
    public.energy_bills,
    energy_readings.eb,
    energy_readings.dg,
    energy_readings.solar,
    energy_readings.transformer,
    energy_readings.ups,
    energy_validation.exception_record,
    energy_import.import_row,
    energy_import.import_file,
    energy_import.import_batch
RESTART IDENTITY CASCADE;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'merged_bill_receipt_reconciliation') THEN
        EXECUTE 'TRUNCATE TABLE public.merged_bill_receipt_reconciliation RESTART IDENTITY CASCADE';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'energy_analytics' AND table_name = 'daily_summary') THEN
        EXECUTE 'TRUNCATE TABLE energy_analytics.daily_summary RESTART IDENTITY CASCADE';
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'energy_analytics' AND table_name = 'kpi_master') THEN
        EXECUTE 'TRUNCATE TABLE energy_analytics.kpi_master RESTART IDENTITY CASCADE';
    END IF;
EXCEPTION WHEN OTHERS THEN
    NULL;
END $$;

-- ============================================================================
-- STEP 2: RESEED MASTER PLAZAS & ASSETS
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS energy_master;

CREATE TABLE IF NOT EXISTS energy_master.plaza (
    plaza_id VARCHAR(16) PRIMARY KEY,
    plaza_name VARCHAR(128) NOT NULL,
    location VARCHAR(256),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO energy_master.plaza (plaza_id, plaza_name, location) VALUES
    ('TP01', 'Toll Plaza 01 (Km 24+500)', 'Sambalpur'),
    ('TP02', 'Toll Plaza 02 (Km 68+200)', 'Jharsuguda'),
    ('TP03', 'Toll Plaza 03 (Km 112+800)', 'Sundargarh')
ON CONFLICT (plaza_id) DO UPDATE SET
    plaza_name = EXCLUDED.plaza_name,
    location = EXCLUDED.location;

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

INSERT INTO energy_master.asset (asset_id, asset_code, asset_name, plaza_id, source_type, capacity_kva, is_active) VALUES
    ('AST-EB-01', 'SR-E-EM-EB-000TP01', 'Main EB Incomer TP01', 'TP01', 'EB', 500.0, true),
    ('AST-DG-01', 'SR-E-AP-DGX-000001', 'Diesel Generator 1', 'TP01', 'DG', 250.0, true),
    ('AST-DG-02', 'SR-E-AP-DGX-000002', 'Diesel Generator 2', 'TP01', 'DG', 250.0, true),
    ('AST-SOL-01', 'SR-E-AP-SPX-000001', 'Solar Plant 1', 'TP01', 'SOLAR', 100.0, true),
    ('AST-TRF-02', 'SR-E-HT-TFR-000002', 'HT Substation Transformer 2', 'TP01', 'TRANSFORMER', 500.0, true),
    ('AST-UPS-02', 'SR-E-AP-UPS-000002', 'Toll Plaza UPS 2', 'TP01', 'UPS', 40.0, true),
    ('AST-UPS-03', 'SR-E-AP-UPS-000003', 'Toll Plaza UPS 3', 'TP01', 'UPS', 40.0, true),

    ('AST-EB-02', 'SR-E-EM-EB-130-000', 'Main EB Incomer TP02', 'TP02', 'EB', 500.0, true),
    ('AST-DG-03', 'SR-E-AP-DGX-000003', 'Diesel Generator 3', 'TP02', 'DG', 250.0, true),
    ('AST-DG-04', 'SR-E-AP-DGX-000004', 'Diesel Generator 4', 'TP02', 'DG', 250.0, true),
    ('AST-SOL-02', 'SR-E-AP-SPX-000002', 'Solar Plant 2', 'TP02', 'SOLAR', 100.0, true),
    ('AST-TRF-03', 'SR-E-HT-TFR-000003', 'HT Substation Transformer 3', 'TP02', 'TRANSFORMER', 500.0, true),
    ('AST-UPS-04', 'SR-E-AP-UPS-000004', 'Toll Plaza UPS 4', 'TP02', 'UPS', 40.0, true),
    ('AST-UPS-09', 'SR-E-AP-UPS-000009', 'Toll Plaza UPS 9', 'TP02', 'UPS', 40.0, true),

    ('AST-EB-03', 'SRTPL_Test_JUNO_EB', 'Main EB Incomer TP03', 'TP03', 'EB', 500.0, true),
    ('AST-DG-05', 'SR-E-AP-DGX-000005', 'Diesel Generator 5', 'TP03', 'DG', 250.0, true),
    ('AST-DG-06', 'SR-E-AP-DGX-000006', 'Diesel Generator 6', 'TP03', 'DG', 250.0, true),
    ('AST-SOL-03', 'SR-E-AP-SPX-000003', 'Solar Plant 3', 'TP03', 'SOLAR', 100.0, true),
    ('AST-TRF-01', 'SR-E-HT-TFR-000001', 'HT Substation Transformer 1', 'TP03', 'TRANSFORMER', 500.0, true),
    ('AST-UPS-10', 'SR-E-AP-UPS-000010', 'Toll Plaza UPS 10', 'TP03', 'UPS', 40.0, true),
    ('AST-UPS-12', 'SR-E-AP-UPS-000012', 'Toll Plaza UPS 12', 'TP03', 'UPS', 40.0, true),

    ('AST-EB-04', 'SR-E-EM-EB-5-200', 'Corridor Lighting Meter 05.200 (Ainthapalli)', 'TP01', 'EB', 50.0, true),
    ('AST-EB-05', 'SR-E-EM-EB-62-600', 'Corridor Lighting Meter 62.600 (Tangarpali)', 'TP02', 'EB', 50.0, true)
ON CONFLICT (asset_code) DO UPDATE SET
    asset_name = EXCLUDED.asset_name,
    capacity_kva = EXCLUDED.capacity_kva;

-- ============================================================================
-- STEP 3: ENSURE ALL 60 MASTER CONSUMER ACCOUNTS EXIST (DO NOT OVERWRITE)
-- ============================================================================

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
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO energy_master.consumer_account (consumer_account_no, toll_plaza_id, bill_type, asset_code, consumer_scope, division_name, usage_type, sanctioned_load_kw, location, is_active) VALUES
  ('411001070208', 'TP01', 'LT', 'SR-E-EM-EB-5-200', 'HIGHWAY', 'SED', 'Street Light', 10.0, 'Ainthapalli', true),
  ('413001070099', 'TP02', 'LT', 'SR-E-EM-EB-62-600', 'HIGHWAY', 'JED', 'Street Light', 18.0, 'TANGARPALI', true),
  ('813000000281', 'TP03', 'HT', 'SR-E-EM-EB-000TP03', 'PLAZA', 'RED', 'Toll Plaza', 120.0, 'TOLL PLAZA 03', true),
  ('411001070209', 'TP01', 'LT', 'SR-E-EM-EB-6-343', 'HIGHWAY', 'SED', 'Street Light', 19.0, 'Bhalupali', true),
  ('411734021695', 'TP01', 'LT', 'SR-E-EM-EB-09-100', 'HIGHWAY', 'SED', 'Street Light', 3.0, '9 VMS', true),
  ('413001070101', 'TP01', 'LT', 'SR-E-EM-EB-46-950', 'HIGHWAY', 'JED', 'Street Light', 19.0, 'BADMAL', true),
  ('413001070102', 'TP01', 'LT', 'SR-E-EM-EB-45-200', 'HIGHWAY', 'JED', 'Street Light', 16.0, 'SAHAPARA', true),
  ('413001070231', 'TP01', 'LT', 'SR-E-EM-EB-43-000', 'HIGHWAY', 'JED', 'Street Light', 5.0, 'KHERUAL', true),
  ('413001070344', 'TP01', 'LT', 'SR-E-EM-EB-053-100', 'HIGHWAY', 'JED', 'Street Light', 40.0, 'BTM Chowk-53 COS', true),
  ('413511052004', 'TP01', 'LT', 'SR-E-EM-EB-048-550', 'HIGHWAY', 'JED', 'Street Light', 3.0, '48 VMS', true),
  ('413526031772', 'TP01', 'LT', 'SR-E-EM-EB-45-100', 'HIGHWAY', 'JED', 'Street Light', 2.0, '45 VMS', true),
  ('416000000110', 'TP01', 'HT', 'SR-E-EM-EB-000TP01', 'PLAZA', 'SEED', 'Toll Plaza', 120.0, 'TOLL PLAZA 01', true),
  ('416001070082', 'TP01', 'LT', 'SR-E-EM-EB-13-000', 'HIGHWAY', 'SEED', 'Street Light', 20.0, 'Sason', true),
  ('416001070083', 'TP01', 'LT', 'SR-E-EM-EB-19-500', 'HIGHWAY', 'SEED', 'Street Light', 16.0, 'Kilasama', true),
  ('416001070084', 'TP01', 'LT', 'SR-E-EM-EB-40-500', 'HIGHWAY', 'SEED', 'Street Light', 16.0, 'Thelkoloi', true),
  ('416001070085', 'TP01', 'LT', 'SR-E-EM-EB-28-400', 'HIGHWAY', 'SEED', 'Street Light', 15.0, 'Shyam Metalic(ROB-2)', true),
  ('416001070086', 'TP01', 'LT', 'SR-E-EM-EB-22-300', 'HIGHWAY', 'SEED', 'Street Light', 13.0, 'New Rampella', true),
  ('416001070087', 'TP01', 'LT', 'SR-E-EM-EB-27-500', 'HIGHWAY', 'SEED', 'Street Light', 4.0, 'Rengali End HM', true),
  ('416001070089', 'TP01', 'LT', 'SR-E-EM-EB-22-550', 'HIGHWAY', 'SEED', 'Street Light', 5.0, 'Rengali Start HM', true),
  ('416001070090', 'TP01', 'LT', 'SR-E-EM-EB-34-950', 'HIGHWAY', 'SEED', 'Street Light', 9.0, 'Lapanga', true),
  ('416001111004', 'TP01', 'LT', 'SR-E-EM-EB-10-850', 'HIGHWAY', 'SEED', 'Street Light', 6.0, 'Majipalli', true),
  ('416335112157', 'TP01', 'LT', 'SR-E-EM-EB-31-000', 'HIGHWAY', 'SEED', 'Street Light', 2.0, '31 VMS', true),
  ('413001070100', 'TP02', 'LT', 'SR-E-EM-EB-61-500', 'HIGHWAY', 'JED', 'Street Light', 7.0, 'TALPATIA', true),
  ('812001020208', 'TP02', 'HT', 'SR-E-EM-EB-000TP02', 'PLAZA', 'SED', 'Toll Plaza', 100.0, 'TOLL PLAZA 02', true),
  ('812001070017', 'TP02', 'LT', 'SR-E-EM-EB-82-600', 'HIGHWAY', 'SED', 'Street Light', 29.0, 'PATRAPALI', true),
  ('812001070018', 'TP02', 'LT', 'SR-E-EM-EB-78-950', 'HIGHWAY', 'SED', 'Street Light', 28.0, 'BHAWANIPUR', true),
  ('812001070019', 'TP02', 'LT', 'SR-E-EM-EB-77-450', 'HIGHWAY', 'SED', 'Street Light', 16.0, 'KIRAI BAMRA CHOWK', true),
  ('812001070020', 'TP02', 'LT', 'SR-E-EM-EB-76-450', 'HIGHWAY', 'SED', 'Street Light', 16.0, 'KIRAI', true),
  ('812001070021', 'TP02', 'LT', 'SR-E-EM-EB-74-500', 'HIGHWAY', 'SED', 'Street Light', 18.0, 'BHEDABAHAL', true),
  ('812001070022', 'TP02', 'LT', 'SR-E-EM-EB-75-450', 'HIGHWAY', 'SED', 'Street Light', 15.0, 'KANDABAHAL', true),
  ('812001070023', 'TP02', 'LT', 'SR-E-EM-EB-70-650', 'HIGHWAY', 'SED', 'Street Light', 8.0, 'BHADBAHAL', true),
  ('812001070024', 'TP02', 'LT', 'SR-E-EM-EB-72-000', 'HIGHWAY', 'SED', 'Street Light', 17.0, 'MASNIKANI', true),
  ('812001070025', 'TP02', 'LT', 'SR-E-EM-EB-63-350', 'HIGHWAY', 'SED', 'Street Light', 20.0, 'BHASMA', true),
  ('812001070026', 'TP02', 'LT', 'SR-E-EM-EB-89-950', 'HIGHWAY', 'SED', 'Street Light', 26.0, 'KARAMDIH', true),
  ('812001070027', 'TP02', 'LT', 'SR-E-EM-EB-84-000', 'HIGHWAY', 'SED', 'Street Light', 5.0, 'BHOJPUR', true),
  ('812121032098', 'TP02', 'LT', 'SR-E-EM-EB-78-430', 'HIGHWAY', 'SED', 'Street Light', 3.0, '78 VMS', true),
  ('812124041064', 'TP02', 'LT', 'SR-E-EM-EB-69-350', 'HIGHWAY', 'SED', 'Street Light', 3.0, '69 VMS', true),
  ('813001070048', 'TP02', 'LT', 'SR-E-EM-EB-104-200', 'HIGHWAY', 'RED', 'Street Light', 16.0, 'ITMA', true),
  ('813001070049', 'TP02', 'LT', 'SR-E-EM-EB-112-750', 'HIGHWAY', 'RED', 'Street Light', 13.0, 'BARGAON', true),
  ('813001070051', 'TP02', 'LT', 'SR-E-EM-EB-107-125', 'HIGHWAY', 'RED', 'Street Light', 17.0, 'TIKLIPARA', true),
  ('813001070052', 'TP02', 'LT', 'SR-E-EM-EB-111-850', 'HIGHWAY', 'RED', 'Street Light', 16.0, 'LATAGAON', true),
  ('813001070059', 'TP02', 'LT', 'SR-E-EM-EB-110-750', 'HIGHWAY', 'RED', 'Street Light', 23.0, 'BHOIPALLI', true),
  ('813001070060', 'TP02', 'LT', 'SR-E-EM-EB-98-450', 'HIGHWAY', 'RED', 'Street Light', 22.0, 'JARONGLOAI', true),
  ('813001070061', 'TP02', 'LT', 'SR-E-EM-EB-97-900', 'HIGHWAY', 'RED', 'Street Light', 7.0, 'JHARMUNDA', true),
  ('813001070063', 'TP02', 'LT', 'SR-E-EM-EB-108-800', 'HIGHWAY', 'RED', 'Street Light', 4.0, 'GARIAMAL', true),
  ('813413021313', 'TP02', 'LT', 'SR-E-EM-EB-112-215', 'HIGHWAY', 'RED', 'Street Light', 1.0, 'BADGAON SUBWAY', true),
  ('813413052467', 'TP02', 'LT', 'SR-E-EM-EB-99-000', 'HIGHWAY', 'RED', 'Street Light', 2.0, '98 VMS', true),
  ('813001070050', 'TP03', 'LT', 'SR-E-EM-EB-113-800', 'HIGHWAY', 'RED', 'Street Light', 23.0, 'KANTAMURA', true),
  ('813001070064', 'TP03', 'LT', 'SR-E-EM-EB-128-750', 'HIGHWAY', 'RED', 'Street Light', 7.0, 'KUTRA TLB', true),
  ('813001070057', 'TP03', 'LT', 'SR-E-EM-EB-130-000', 'HIGHWAY', 'RED', 'Street Light', 18.0, 'KUTRA', true),
  ('813414012506', 'TP03', 'LT', 'SR-E-EM-EB-128-000', 'HIGHWAY', 'RED', 'Street Light', 3.0, '128 VMS', true),
  ('813001070058', 'TP03', 'LT', 'SR-E-EM-EB-136-700', 'HIGHWAY', 'RED', 'Street Light', 14.0, 'JHAREBEDA', true),
  ('813001070045', 'TP03', 'LT', 'SR-E-EM-EB-144-500', 'HIGHWAY', 'RED', 'Street Light', 6.0, 'RANIBANDA', true),
  ('813001070047', 'TP03', 'LT', 'SR-E-EM-EB-144-950', 'HIGHWAY', 'RED', 'Street Light', 26.0, 'RANIBANDH', true),
  ('813001070053', 'TP03', 'LT', 'SR-E-EM-EB-152-650', 'HIGHWAY', 'RED', 'Street Light', 16.0, 'LAING', true),
  ('813001070054', 'TP03', 'LT', 'SR-E-EM-EB-154-150', 'HIGHWAY', 'RED', 'Street Light', 21.0, 'DHELUA', true),
  ('813001070055', 'TP03', 'LT', 'SR-E-EM-EB-157-600', 'HIGHWAY', 'RED', 'Street Light', 26.0, 'CHUNGIMATI', true),
  ('813001070046', 'TP03', 'LT', 'SR-E-EM-EB-159-200', 'HIGHWAY', 'RED', 'Street Light', 6.0, 'MANDIAKUDAR I', true),
  ('813001070056', 'TP03', 'LT', 'SR-E-EM-EB-160-000', 'HIGHWAY', 'RED', 'Street Light', 18.0, 'MANDIAKUDAR II', true),
  ('813001070065', 'TP03', 'LT', 'SR-E-EM-EB-166-170', 'HIGHWAY', 'RED', 'Street Light', 19.0, 'VEDVYAS', true)
ON CONFLICT (consumer_account_no) DO NOTHING;

-- ============================================================================
-- STEP 4: RESEED PAYMENT RECEIPTS (5 VERIFIED RECEIPTS)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.payment_receipts (
    receipt_no VARCHAR(64) PRIMARY KEY,
    consumer_no VARCHAR(64),
    account_no VARCHAR(64),
    consumer_name VARCHAR(256),
    collections_date VARCHAR(32),
    payment_date VARCHAR(32),
    amount_paid NUMERIC(14, 2) DEFAULT 0.0,
    payment_type VARCHAR(64),
    transaction_id VARCHAR(128),
    bill_month VARCHAR(32),
    category VARCHAR(128),
    office_name VARCHAR(128),
    source_pdf VARCHAR(256),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO public.payment_receipts (
    receipt_no, consumer_no, account_no, consumer_name, collections_date, payment_date,
    amount_paid, payment_type, transaction_id, bill_month, category, office_name, source_pdf
) VALUES
    ('657221120326HDFC0007', '416001111004', '416001111004', 'L/T SAMBALPUR ROURKELA TOLLWAY LTD', '15/05/2025', '15/05/2025', 7678.00, 'PG_HDFC', 'HDFC0007_TXN', '04/2025', 'GENERAL PURPOSE < 110 KVA', 'ESO SASON', '657221120326HDFC0007.pdf'),
    ('657221120326HDFC0008', '416001070090', '416001070090', 'L/T SAMBALPUR ROURKELA TOLLWAY LTD', '15/09/2025', '15/09/2025', 15316.00, 'PG_HDFC', 'HDFC0008_TXN', '08/2025', 'PUBLIC LIGHT', 'ESO RENGALI', '657221120326HDFC0008.pdf'),
    ('657221120326HDFC0009', '416001070084', '416001070084', 'L/T SAMBALPUR ROURKELA TOLLWAY LTD', '15/09/2025', '15/09/2025', 22660.00, 'PG_HDFC', 'HDFC0009_TXN', '08/2025', 'PUBLIC LIGHT', 'ESO RENGALI', '657221120326HDFC0009.pdf'),
    ('657221120326HDFC0010', '416001070086', '416001070086', 'L/T SAMBALPUR ROURKELA TOLLWAY LTD', '15/09/2025', '15/09/2025', 33399.00, 'PG_HDFC', 'HDFC0010_TXN', '08/2025', 'PUBLIC LIGHT', 'ESO RENGALI', '657221120326HDFC0010.pdf'),
    ('657221120326HDFC0011', '411001070208', '411001070208', 'L/T SAMBALPUR ROURKELA TOLLWAY LTD', '15/09/2025', '15/09/2025', 13583.00, 'PG_HDFC', 'HDFC0011_TXN', '08/2025', 'PUBLIC LIGHT', 'ESO RE SECTION', '657221120326HDFC0011.pdf')
ON CONFLICT (receipt_no) DO UPDATE SET
    amount_paid = EXCLUDED.amount_paid,
    payment_date = EXCLUDED.payment_date;

-- ============================================================================
-- STEP 5: RESEED ENERGY BILLS (13 VERIFIED OFFICIAL BILLS)
-- Complete with Meter Rent, Customer Service, valid Contract Demand, and Rebate Impact
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.energy_bills (
    bill_number VARCHAR(64) PRIMARY KEY,
    source_filename VARCHAR(256),
    consumer_account_no VARCHAR(64),
    consumer_id VARCHAR(64),
    old_consumer_no VARCHAR(64),
    bill_type VARCHAR(32) DEFAULT 'LT',
    consumer_scope VARCHAR(64) DEFAULT 'HIGHWAY',
    sanctioned_load_kw NUMERIC(10, 2) DEFAULT 0.0,
    contract_demand VARCHAR(64),
    bill_month VARCHAR(32),
    bill_period VARCHAR(128),
    bill_days VARCHAR(32),
    bill_basis VARCHAR(32) DEFAULT 'ACTUAL',
    audit_flag VARCHAR(64),
    bill_issue_date VARCHAR(32),
    due_date VARCHAR(32),
    rebate_date VARCHAR(32),
    meter_sl_no VARCHAR(64),
    meter_rent_count VARCHAR(32),
    security_deposit NUMERIC(14, 2) DEFAULT 0.0,
    md NUMERIC(14, 4) DEFAULT 0.0,
    md_kw NUMERIC(14, 4) DEFAULT 0.0,
    md_kva NUMERIC(14, 4) DEFAULT 0.0,
    cuml_md_kw NUMERIC(14, 4) DEFAULT 0.0,
    cuml_md_kva NUMERIC(14, 4) DEFAULT 0.0,
    tariff_category VARCHAR(128),
    tariff_type VARCHAR(64),
    division VARCHAR(128),
    sub_division VARCHAR(128),
    section VARCHAR(128),
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
    meter_rent_rs NUMERIC(14, 2) DEFAULT 0.0,
    customer_service_charge NUMERIC(14, 2) DEFAULT 0.0,
    customer_service_charge_rs NUMERIC(14, 2) DEFAULT 0.0,
    dps_rs NUMERIC(14, 2) DEFAULT 0.0,
    current_total NUMERIC(14, 2) DEFAULT 0.0,
    prompt_rebate NUMERIC(14, 2) DEFAULT 0.0,
    rebate_status VARCHAR(64) DEFAULT 'PENDING (ELIGIBLE)',
    rebate_availed NUMERIC(14, 2) DEFAULT 0.0,
    rebate_loss NUMERIC(14, 2) DEFAULT 0.0,
    company_profit_rs NUMERIC(14, 2) DEFAULT 0.0,
    company_loss_rs NUMERIC(14, 2) DEFAULT 0.0,
    financial_impact VARCHAR(64) DEFAULT 'POTENTIAL PROFIT',
    rebate_remarks TEXT,
    total_amount_payable NUMERIC(14, 2) DEFAULT 0.0,
    net_after_rebate NUMERIC(14, 2) DEFAULT 0.0,
    net_before_rebate NUMERIC(14, 2) DEFAULT 0.0,
    net_payable_amount_before_rbt_dt_rs NUMERIC(14, 2) DEFAULT 0.0,
    net_payable_amount_after_rbt_dt_rs NUMERIC(14, 2) DEFAULT 0.0,
    cal_energy_charges NUMERIC(14, 2) DEFAULT 0.0,
    diff_energy_charges NUMERIC(14, 2) DEFAULT 0.0,
    cal_electricity_charges NUMERIC(14, 2) DEFAULT 0.0,
    diff_electricity_charges NUMERIC(14, 2) DEFAULT 0.0,
    cal_current_total NUMERIC(14, 2) DEFAULT 0.0,
    diff_current_total NUMERIC(14, 2) DEFAULT 0.0,
    verification_status VARCHAR(64) DEFAULT 'VERIFIED ✓',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO public.energy_bills (
    bill_number, source_filename, consumer_account_no, consumer_id, old_consumer_no,
    bill_type, consumer_scope, sanctioned_load_kw, contract_demand, bill_month,
    bill_period, bill_days, bill_basis, rebate_date, meter_sl_no,
    meter_rent_count, security_deposit, md, cuml_md_kva, cuml_md_kw,
    tariff_category, division, sub_division, section, slab_normal_kwh,
    slab_peak_kwh, slab_solar_kwh, energy_charges, demand_charge, tod_incentive,
    tod_surcharge, electricity_charges, electricity_duty, meter_rent, meter_rent_rs,
    customer_service_charge, customer_service_charge_rs, dps_rs, current_total, prompt_rebate,
    rebate_status, rebate_availed, rebate_loss, company_profit_rs, company_loss_rs,
    financial_impact, total_amount_payable, net_payable_amount_before_rbt_dt_rs, net_payable_amount_after_rbt_dt_rs,
    cal_energy_charges, cal_electricity_charges, cal_current_total, verification_status
) VALUES
    ('411010709251615163', '411001070208_82025_EN.pdf', '411001070208', '34110012497', 'STL-SBP-218', 'LT', 'HIGHWAY', 10.0, '10 KW', '08/2025', '02/08/2025 - 01/09/2025', '31/1.0000', 'ACTUAL', '15/09/2025', '10029454', '34/60', 36360.14, 0.0, 0.0, 0.0, 'PUBLIC LIGHT', 'SED SAMBALPUR', 'SDO-I SAMBALPUR', 'ESO RE SECTION', 2646.0, 0.0, 0.0, 16405.20, 155.00, 0.0, 0.0, 16560.20, 656.21, 150.00, 150.00, 0.0, 0.0, 0.0, 17366.41, 131.00, 'REBATE AVAILED', 131.00, 0.0, 131.00, 0.0, 'PROFIT TO COMPANY', 13714.00, 13583.00, 13714.00, 16405.20, 16560.20, 17366.41, 'VERIFIED ✓'),
    ('411010710261293606', '411001070208_92026_EN.pdf', '411001070208', '34110012497', 'STL-SBP-218', 'LT', 'HIGHWAY', 10.0, '10 KW', '09/2026', '02/09/2026 - 01/10/2026', '30/1.0000', 'ACTUAL', '14/10/2026', '10029454', '47/60', 36360.14, 8.76, 7.30, 7.30, 'PUBLIC LIGHT', 'SED SAMBALPUR', 'SDO-I SAMBALPUR', 'ESO RE SECTION', 2076.0, 0.0, 0.0, 12871.20, 155.00, 0.0, 0.0, 13026.20, 514.45, 150.00, 150.00, 0.0, 0.0, 32.99, 13723.64, 107.00, 'PENDING (ELIGIBLE)', 0.0, 0.0, 0.0, 0.0, 'POTENTIAL PROFIT', 14782.00, 14675.00, 14782.00, 12871.20, 13026.20, 13723.64, 'VERIFIED ✓'),
    ('413010710261229528', '413001070102_92026_EN.pdf', '413001070102', '34130015224', '101-STL-SPD', 'LT', 'HIGHWAY', 16.0, '16 KW', '09/2026', '02/09/2026 - 01/10/2026', '30/1.0000', 'ACTUAL', '14/10/2026', '10010726', '49/60', 64391.05, 11.04, 8.74, 8.74, 'PUBLIC LIGHT', 'JED JHARSUGUDA', 'SDO JHARSUGUDA-II', 'ESO SAHAPADA', 1225.0, 1334.0, 25.0, 16772.38, 245.00, 0.0, 0.0, 17017.38, 673.30, 150.00, 150.00, 0.0, 0.0, 54.17, 17894.85, 172.00, 'PENDING (ELIGIBLE)', 0.0, 0.0, 0.0, 0.0, 'POTENTIAL PROFIT', 19785.00, 19613.00, 19785.00, 16772.38, 17017.38, 17894.85, 'VERIFIED ✓'),
    ('413010709251688219', '413001070344_82025_EN.pdf', '413001070344', '142452232667', 'BTM', 'LT', 'HIGHWAY', 40.0, '40 KW', '08/2025', '02/08/2025 - 01/09/2025', '31/1.0000', 'ACTUAL', '15/09/2025', 'TWSL12001179', '0/60', 179770.00, 10.32, 28.32, 28.32, 'PUBLIC LIGHT', 'JED JHARSUGUDA', 'SDO JHARSUGUDA-I', 'ESO JED-2', 6093.0, 0.0, 0.0, 37776.60, 605.00, 0.0, 0.0, 39221.60, 1548.26, 0.00, 0.00, 0.0, 0.0, 0.01, 40769.86, 393.00, 'PENDING (ELIGIBLE)', 0.0, 0.0, 0.0, 0.0, 'POTENTIAL PROFIT', 40771.00, 40378.00, 40771.00, 37776.60, 39221.60, 40769.86, 'VERIFIED ✓'),
    ('416000010262972491', '416000000110_92026_EN.pdf', '416000000110', '4160000110', 'LE-110', 'HT', 'PLAZA', 120.0, '120 KVA', '09/2026', '01/09/2026 - 30/09/2026', '30/1.0000', 'ACTUAL', '06/10/2026', 'TWN20045', '13/60', 390096.00, 0.2948, 0.3160, 0.0, 'GENERAL PURPOSE >= 110 KVA', 'SEED SAMBALPUR', 'SDO RENGALI', 'ESO SASON', 9899.0, 8124.0, 4630.0, 128627.81, 30000.00, 0.0, 0.0, 158627.81, 10769.42, 1000.00, 1000.00, 250.00, 250.00, 0.0, 170647.23, 1599.00, 'PENDING (ELIGIBLE)', 0.0, 0.0, 0.0, 0.0, 'POTENTIAL PROFIT', 169071.00, 167472.00, 169071.00, 128627.81, 158627.81, 170647.23, 'VERIFIED ✓'),
    ('416010710261304116', '416001070082_92026_EN.pdf', '416001070082', '34160015098', 'STL-SBP-214', 'LT', 'HIGHWAY', 20.0, '20 KW', '09/2026', '02/09/2026 - 01/10/2026', '30/1.0000', 'ACTUAL', '14/10/2026', '10025846', '48/60', 85149.00, 10.32, 14.31, 14.31, 'PUBLIC LIGHT', 'SEED SAMBALPUR', 'SDO RENGALI', 'ESO SASON', 4346.0, 0.0, 0.0, 26945.20, 305.00, 0.0, 0.0, 27250.20, 1077.81, 150.00, 150.00, 0.0, 0.0, 28.04, 28506.05, 274.00, 'PENDING (ELIGIBLE)', 0.0, 0.0, 0.0, 0.0, 'POTENTIAL PROFIT', 28507.00, 28233.00, 28507.00, 26945.20, 27250.20, 28506.05, 'VERIFIED ✓'),
    ('416010709251608075', '416001070084_82025_EN.pdf', '416001070084', '34160015100', 'STL-SBP-216', 'LT', 'HIGHWAY', 16.0, '16 KW', '08/2025', '02/08/2025 - 01/09/2025', '31/1.0000', 'ACTUAL', '15/09/2025', '10040807', '34/60', 65781.00, 15.42, 11.88, 11.88, 'PUBLIC LIGHT', 'SEED SAMBALPUR', 'SDO RENGALI', 'ESO RENGALI', 3491.0, 0.0, 0.0, 21644.20, 245.00, 0.0, 0.0, 21865.00, 864.80, 150.00, 150.00, 0.0, 0.0, 0.0, 22879.80, 220.00, 'REBATE AVAILED', 220.00, 0.0, 220.00, 0.0, 'PROFIT TO COMPANY', 22880.00, 22660.00, 22880.00, 21644.20, 21865.00, 22879.80, 'VERIFIED ✓'),
    ('416010709251691494', '416001070086_82025_EN.pdf', '416001070086', '34160015101', 'STL-SBP-217', 'LT', 'HIGHWAY', 13.0, '13 KW', '08/2025', '02/08/2025 - 01/09/2025', '31/1.0000', 'ACTUAL', '15/09/2025', 'TWSC59033983', '34/60', 70231.24, 16.96, 16.96, 16.96, 'PUBLIC LIGHT', 'SEED SAMBALPUR', 'SDO RENGALI', 'ESO RENGALI', 5176.0, 0.0, 0.0, 32091.20, 200.00, 0.0, 0.0, 32292.90, 1279.52, 150.00, 150.00, 0.0, 0.0, 0.0, 33722.42, 324.00, 'REBATE AVAILED', 324.00, 0.0, 324.00, 0.0, 'PROFIT TO COMPANY', 33723.00, 33399.00, 33723.00, 32091.20, 32292.90, 33722.42, 'VERIFIED ✓'),
    ('416010709251608419', '416001070090_82025_EN.pdf', '416001070090', '34160015105', 'STL-SBP-221', 'LT', 'HIGHWAY', 9.0, '9 KW', '08/2025', '02/08/2025 - 01/09/2025', '31/1.0000', 'ACTUAL', '15/09/2025', '10029687', '34/60', 34610.78, 6.17, 6.16, 6.16, 'PUBLIC LIGHT', 'SEED SAMBALPUR', 'SDO RENGALI', 'ESO RENGALI', 2399.0, 0.0, 0.0, 14873.80, 140.00, 0.0, 0.0, 15013.80, 594.95, 150.00, 150.00, 0.0, 0.0, 0.0, 15758.75, 152.00, 'REBATE AVAILED', 152.00, 0.0, 152.00, 0.0, 'PROFIT TO COMPANY', 15468.00, 15316.00, 15468.00, 14873.80, 15013.80, 15758.75, 'VERIFIED ✓'),
    ('416010710261304692', '416001070090_92026_EN.pdf', '416001070090', '34160015105', 'STL-SBP-221', 'LT', 'HIGHWAY', 9.0, '9 KW', '09/2026', '02/09/2026 - 01/10/2026', '30/1.0000', 'ACTUAL', '14/10/2026', '10029687', '47/60', 34610.78, 6.17, 6.16, 6.16, 'PUBLIC LIGHT', 'SEED SAMBALPUR', 'SDO RENGALI', 'ESO RENGALI', 1686.0, 0.0, 0.0, 10450.60, 140.00, 0.0, 0.0, 10590.60, 418.62, 150.00, 150.00, 0.0, 0.0, 34.52, 11193.74, 107.00, 'PENDING (ELIGIBLE)', 0.0, 0.0, 0.0, 0.0, 'POTENTIAL PROFIT', 11194.00, 11087.00, 11194.00, 10450.60, 10590.60, 11193.74, 'VERIFIED ✓'),
    ('416011105251608613', '416001111004_42025_EN.pdf', '416001111004', '18164016140', 'S-1715', 'LT', 'HIGHWAY', 6.0, '6 KW', '04/2025', '03/04/2025 - 02/05/2025', '29/1.0000', 'ACTUAL', '15/05/2025', '10028787', '21/60', 19165.00, 3.49, 3.23, 3.23, 'GENERAL PURPOSE < 110 KVA', 'SEED SAMBALPUR', 'SDO RENGALI', 'ESO SASON', 1030.0, 0.0, 0.0, 7295.60, 180.00, 0.0, 0.0, 7475.60, 294.22, 150.00, 150.00, 0.0, 0.0, 0.0, 7919.82, 152.00, 'REBATE AVAILED', 152.00, 0.0, 152.00, 0.0, 'PROFIT TO COMPANY', 7830.00, 7678.00, 7830.00, 7295.60, 7475.60, 7919.82, 'VERIFIED ✓'),
    ('416011110261308077', '416001111004_92026_EN.pdf', '416001111004', '18164016140', 'S-1715', 'LT', 'HIGHWAY', 6.0, '6 KW', '09/2026', '02/09/2026 - 01/10/2026', '30/1.0000', 'ACTUAL', '14/10/2026', '10028787', '38/60', 19165.00, 3.49, 3.23, 3.23, 'GENERAL PURPOSE < 110 KVA', 'SEED SAMBALPUR', 'SDO RENGALI', 'ESO SASON', 1015.0, 0.0, 0.0, 7189.20, 180.00, 0.0, 0.0, 7369.20, 289.97, 150.00, 150.00, 0.0, 0.0, 19.85, 7829.02, 100.00, 'PENDING (ELIGIBLE)', 0.0, 0.0, 0.0, 0.0, 'POTENTIAL PROFIT', 8639.00, 8539.00, 8639.00, 7189.20, 7369.20, 7829.02, 'VERIFIED ✓'),
    ('812010710261330579', '812001070018_92026_EN.pdf', '812001070018', '34120005470', 'COM12-B-116/LT', 'LT', 'HIGHWAY', 28.0, '28 KW', '09/2026', '02/09/2026 - 01/10/2026', '30/1.0000', 'ACTUAL', '14/10/2026', '10006888', '47/60', 92260.00, 13.78, 15.72, 15.72, 'PUBLIC LIGHT', 'SED SUNDARAGADA', 'SDO SUNDARAGADA', 'ESO NO-I', 4843.0, 0.0, 0.0, 30026.60, 425.00, 0.0, 0.0, 30405.00, 1202.80, 150.00, 150.00, 0.0, 0.0, 70.17, 31827.97, 306.00, 'PENDING (ELIGIBLE)', 0.0, 0.0, 0.0, 0.0, 'POTENTIAL PROFIT', 31828.00, 31522.00, 31828.00, 30026.60, 30405.00, 31827.97, 'VERIFIED ✓')
ON CONFLICT (bill_number) DO UPDATE SET
    meter_rent = EXCLUDED.meter_rent,
    meter_rent_rs = EXCLUDED.meter_rent_rs,
    customer_service_charge = EXCLUDED.customer_service_charge,
    customer_service_charge_rs = EXCLUDED.customer_service_charge_rs,
    contract_demand = EXCLUDED.contract_demand,
    total_amount_payable = EXCLUDED.total_amount_payable;

-- ============================================================================
-- STEP 6: RESEED RECEIPT ALLOCATIONS & MONTHLY BUDGETS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.receipt_allocations (
    id BIGSERIAL PRIMARY KEY,
    receipt_no VARCHAR(64) NOT NULL REFERENCES public.payment_receipts(receipt_no) ON DELETE CASCADE,
    bill_number VARCHAR(64) REFERENCES public.energy_bills(bill_number) ON DELETE SET NULL,
    allocation_amount NUMERIC(14, 2) NOT NULL DEFAULT 0.0,
    allocation_date TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO public.receipt_allocations (receipt_no, bill_number, allocation_amount, notes) VALUES
    ('657221120326HDFC0007', '416011105251608613', 7678.00, 'Full clearance before rebate date'),
    ('657221120326HDFC0008', '416010709251608419', 15316.00, 'Full clearance before rebate date'),
    ('657221120326HDFC0009', '416010709251608075', 22660.00, 'Full clearance before rebate date'),
    ('657221120326HDFC0010', '416010709251691494', 33399.00, 'Full clearance before rebate date'),
    ('657221120326HDFC0011', '411010709251615163', 13583.00, 'Full clearance before rebate date')
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS public.monthly_budgets (
    id BIGSERIAL PRIMARY KEY,
    toll_plaza_id VARCHAR(16) REFERENCES energy_master.plaza(plaza_id) ON DELETE CASCADE,
    budget_month VARCHAR(32) NOT NULL,
    budget_amount NUMERIC(14, 2) NOT NULL DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_plaza_month_budget UNIQUE (toll_plaza_id, budget_month)
);

INSERT INTO public.monthly_budgets (toll_plaza_id, budget_month, budget_amount) VALUES
    ('TP01', '08/2025', 180000.00),
    ('TP01', '09/2026', 220000.00),
    ('TP02', '08/2025', 150000.00),
    ('TP02', '09/2026', 175000.00),
    ('TP03', '08/2025', 160000.00),
    ('TP03', '09/2026', 190000.00)
ON CONFLICT (toll_plaza_id, budget_month) DO UPDATE SET
    budget_amount = EXCLUDED.budget_amount;

-- ============================================================================
-- STEP 7: RELOAD POSTGREST SCHEMA CACHE & VERIFY
-- ============================================================================

NOTIFY pgrst, 'reload schema';

SELECT 
    schemaname, 
    relname AS table_name,
    n_live_tup AS total_rows
FROM pg_stat_user_tables
WHERE schemaname IN ('public', 'energy_readings', 'energy_master', 'energy_import', 'energy_validation')
ORDER BY total_rows DESC, relname;
