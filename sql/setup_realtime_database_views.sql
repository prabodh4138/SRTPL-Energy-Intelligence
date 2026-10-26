-- ============================================================================
-- SRTPL POWER INTELLIGENCE — REAL-TIME DATABASE VIEWS & RELATIONAL ARCHITECTURE
-- Aligned with: SRTPL Bill Reconciliation Full Implementation Roadmap & Acceptance Plan
-- Target: PostgreSQL / Supabase
--
-- Master Table Authority: energy_master.consumer_account (NO DUMMY INSERTS)
-- 100% relational: links energy_master.consumer_account, public.energy_bills,
-- public.energy_bills_provisional, public.payment_receipts, public.receipt_allocations.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- STEP 1: PREREQUISITE SCHEMAS
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS energy_master;
CREATE SCHEMA IF NOT EXISTS energy_readings;
CREATE SCHEMA IF NOT EXISTS energy_import;
CREATE SCHEMA IF NOT EXISTS energy_validation;
CREATE SCHEMA IF NOT EXISTS energy_analytics;

ALTER ROLE authenticator SET pgrst.db_schemas = 'public, energy_master, energy_readings, energy_import, energy_validation, energy_analytics';

-- ============================================================================
-- STEP 2: MASTER & OPERATIONAL TABLES (DDL ONLY — ZERO DUMMY DATA INSERTS)
-- ============================================================================

-- Master Plazas
CREATE TABLE IF NOT EXISTS energy_master.plaza (
    plaza_id VARCHAR(16) PRIMARY KEY,
    plaza_name VARCHAR(128) NOT NULL,
    location VARCHAR(256),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Master Assets
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

-- Master Consumer Accounts Table (PRIMARY AUTHORITATIVE MASTER TABLE)
CREATE TABLE IF NOT EXISTS energy_master.consumer_account (
    consumer_account_no VARCHAR(64) PRIMARY KEY,
    toll_plaza_id VARCHAR(16) REFERENCES energy_master.plaza(plaza_id) ON DELETE SET NULL,
    bill_type VARCHAR(32) NOT NULL DEFAULT 'LT',
    asset_code VARCHAR(64),
    consumer_scope VARCHAR(64) NOT NULL DEFAULT 'HIGHWAY',
    division_name VARCHAR(128),
    usage_type VARCHAR(128) NOT NULL DEFAULT 'Public Light',
    sanctioned_load_kw NUMERIC(10, 2) NOT NULL DEFAULT 10.0,
    location VARCHAR(256),
    is_active BOOLEAN NOT NULL DEFAULT true,
    remarks TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

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

-- Official Actual Energy Bills
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
    verification_status VARCHAR(64) NOT NULL DEFAULT 'VERIFIED_OK',
    superseded_by_bill_number VARCHAR(64),
    is_voided BOOLEAN NOT NULL DEFAULT FALSE,
    void_reason TEXT,
    is_edited BOOLEAN NOT NULL DEFAULT FALSE,
    edited_by VARCHAR(128),
    edited_at TIMESTAMPTZ,
    edit_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

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
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS superseded_by_bill_number VARCHAR(64);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS is_voided BOOLEAN DEFAULT FALSE;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS void_reason TEXT;

-- Provisional & Average Bills Audit Archive
CREATE TABLE IF NOT EXISTS public.energy_bills_provisional (
    bill_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_filename VARCHAR(256) NOT NULL,
    consumer_account_no VARCHAR(64),
    consumer_id VARCHAR(64),
    old_consumer_no VARCHAR(64),
    bill_number VARCHAR(64) UNIQUE,
    bill_month VARCHAR(32),
    bill_basis VARCHAR(32) NOT NULL DEFAULT 'AVERAGE',
    audit_flag TEXT,
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
    verification_status VARCHAR(64) NOT NULL DEFAULT 'PROVISIONAL_AVERAGE_AUDIT',
    superseded_by_bill_number VARCHAR(64),
    is_voided BOOLEAN NOT NULL DEFAULT FALSE,
    void_reason TEXT,
    is_edited BOOLEAN NOT NULL DEFAULT FALSE,
    edited_by VARCHAR(128),
    edited_at TIMESTAMPTZ,
    edit_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS bill_basis VARCHAR(32) DEFAULT 'AVERAGE';
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS audit_flag TEXT;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS superseded_by_bill_number VARCHAR(64);
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS is_voided BOOLEAN DEFAULT FALSE;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS void_reason TEXT;

-- Payment Receipts Table
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

-- Receipt Allocations Table (Multi-to-Multi with Zero Inflation)
CREATE TABLE IF NOT EXISTS public.receipt_allocations (
    allocation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    receipt_no VARCHAR(64) NOT NULL REFERENCES public.payment_receipts(receipt_no) ON DELETE CASCADE,
    bill_number VARCHAR(64),
    consumer_account_no VARCHAR(64) NOT NULL,
    bill_month VARCHAR(32) NOT NULL,
    allocated_amount NUMERIC(14, 2) NOT NULL,
    allocation_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Monthly Budgets Table
CREATE TABLE IF NOT EXISTS public.monthly_budgets (
    budget_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    financial_year VARCHAR(16) NOT NULL,
    bill_month VARCHAR(32) NOT NULL,
    toll_plaza_id VARCHAR(16) NOT NULL,
    bill_type VARCHAR(32) NOT NULL DEFAULT 'ALL',
    budget_amount NUMERIC(14, 2) NOT NULL DEFAULT 200000.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_monthly_budget UNIQUE (financial_year, bill_month, toll_plaza_id, bill_type)
);

-- Persistent Bill Review Queue
CREATE TABLE IF NOT EXISTS public.bill_review_queue (
    candidate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bill_number VARCHAR(64),
    consumer_account_no VARCHAR(64),
    toll_plaza_id VARCHAR(16),
    bill_type VARCHAR(32),
    bill_month VARCHAR(32),
    bill_basis VARCHAR(32) DEFAULT 'ACTUAL',
    amount NUMERIC(14, 2) DEFAULT 0.0,
    units NUMERIC(14, 2) DEFAULT 0.0,
    exception_reason TEXT,
    hold_reason_code VARCHAR(64) DEFAULT 'UNRESOLVED_CHECK',
    status VARCHAR(32) DEFAULT 'REVIEW',
    raw_payload JSONB,
    source_filename VARCHAR(256),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Audit Events Table
CREATE TABLE IF NOT EXISTS public.audit_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type VARCHAR(64) NOT NULL,
    entity_type VARCHAR(64),
    entity_id VARCHAR(128),
    details TEXT,
    user_id VARCHAR(128) DEFAULT 'operator',
    result VARCHAR(32) DEFAULT 'RECORDED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- JUNO EB Meter Readings Table
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

-- ============================================================================
-- STEP 3: DROP EXISTING VIEWS WITH CASCADE
-- Prevents schema column locks / name change collisions
-- ============================================================================
DROP VIEW IF EXISTS public.vw_bill_kpi_summary CASCADE;
DROP VIEW IF EXISTS public.vw_official_bill_register CASCADE;
DROP VIEW IF EXISTS public.vw_bill_review_queue CASCADE;
DROP VIEW IF EXISTS public.vw_receipt_reconciliation CASCADE;
DROP VIEW IF EXISTS public.vw_import_batch_acknowledgement CASCADE;
DROP VIEW IF EXISTS public.vw_duplicate_rejections CASCADE;
DROP VIEW IF EXISTS public.vw_budget_vs_actual CASCADE;
DROP VIEW IF EXISTS public.vw_rebate_performance CASCADE;

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

-- Public table alias views
CREATE VIEW public.energy_consumer_master AS SELECT * FROM energy_master.consumer_account;
CREATE VIEW public.consumer_account AS SELECT * FROM energy_master.consumer_account;
CREATE VIEW public.reading_eb AS SELECT * FROM energy_readings.eb;

-- ============================================================================
-- STEP 4: CREATE ROADMAP SECTION 10 SQL KPI VIEWS & FINANCIAL REPORTING
-- ============================================================================

-- ----------------------------------------------------------------------------
-- VIEW 1: public.vw_official_bill_register
-- One row per official reportable bill. Excludes superseded and voided records.
-- Correlates payments with payment_receipts without double-counting.
-- ----------------------------------------------------------------------------
CREATE VIEW public.vw_official_bill_register AS
WITH receipt_agg AS (
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
    COALESCE(m.toll_plaza_id, 
        CASE 
            WHEN b.consumer_account_no LIKE '416%' OR b.consumer_account_no LIKE '411%' THEN 'TP01'
            WHEN b.consumer_account_no LIKE '413%' THEN 'TP02'
            WHEN b.consumer_account_no LIKE '812%' OR b.consumer_account_no LIKE '813%' THEN 'TP03'
            ELSE 'TP01'
        END
    ) AS toll_plaza_id,
    COALESCE(m.bill_type, 'LT') AS bill_type,
    COALESCE(m.asset_code, '') AS asset_code,
    COALESCE(m.consumer_scope, 'HIGHWAY') AS consumer_scope,
    COALESCE(m.division_name, b.division, 'SED') AS division_name,
    COALESCE(m.usage_type, b.tariff_category, 'Public Light') AS usage_type,
    COALESCE(m.sanctioned_load_kw, 10.0) AS sanctioned_load_kw,
    COALESCE(m.location, 'Corridor Lighting') AS location,
    b.bill_month,
    CASE 
        WHEN b.bill_month ILIKE '%2026%' OR b.bill_month ILIKE '%26%' THEN '2026-27'
        WHEN b.bill_month ILIKE '%2025%' OR b.bill_month ILIKE '%25%' THEN '2025-26'
        ELSE '2026-27'
    END AS financial_year,
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
    'POSTED' AS lifecycle_status,
    'GENERATED' AS bill_present,
    r.latest_payment_date,
    b.verification_status,
    b.superseded_by_bill_number,
    b.is_voided,
    b.void_reason,
    b.created_at
FROM public.energy_bills b
LEFT JOIN energy_master.consumer_account m 
    ON TRIM(b.consumer_account_no) = TRIM(m.consumer_account_no)
LEFT JOIN receipt_agg r 
    ON TRIM(b.consumer_account_no) = r.ac_no AND TRIM(b.bill_month) = r.b_mo
WHERE COALESCE(b.is_voided, false) = false
  AND (b.verification_status IS NULL OR b.verification_status != 'SUPERSEDED');

-- ----------------------------------------------------------------------------
-- VIEW 2: public.vw_bill_review_queue
-- One row per review candidate/exception with reason and status
-- ----------------------------------------------------------------------------
CREATE VIEW public.vw_bill_review_queue AS
SELECT 
    q.candidate_id,
    q.bill_number,
    q.consumer_account_no,
    q.toll_plaza_id,
    q.bill_type,
    q.bill_month,
    q.bill_basis,
    q.amount,
    q.units,
    q.exception_reason,
    q.hold_reason_code,
    q.status,
    q.source_filename,
    q.created_at
FROM public.bill_review_queue q
WHERE q.status IN ('REVIEW', 'HELD', 'PENDING')
UNION ALL
SELECT 
    bp.bill_id AS candidate_id,
    bp.bill_number,
    bp.consumer_account_no,
    COALESCE(m.toll_plaza_id, 'TP01') AS toll_plaza_id,
    COALESCE(m.bill_type, 'LT') AS bill_type,
    bp.bill_month,
    UPPER(COALESCE(bp.bill_basis, 'AVERAGE')) AS bill_basis,
    COALESCE(bp.total_amount_payable, bp.current_total, 0) AS amount,
    (COALESCE(bp.slab_normal_kwh, 0) + COALESCE(bp.slab_peak_kwh, 0) + COALESCE(bp.slab_solar_kwh, 0)) AS units,
    COALESCE(bp.audit_flag, 'Provisional / Average bill held for review') AS exception_reason,
    'PROVISIONAL_AVERAGE_AUDIT' AS hold_reason_code,
    'REVIEW' AS status,
    bp.source_filename,
    bp.created_at
FROM public.energy_bills_provisional bp
LEFT JOIN energy_master.consumer_account m ON TRIM(bp.consumer_account_no) = TRIM(m.consumer_account_no)
WHERE bp.superseded_by_bill_number IS NULL
  AND COALESCE(bp.is_voided, false) = false;

-- ----------------------------------------------------------------------------
-- VIEW 3: public.vw_receipt_reconciliation
-- Clearly defined grain for receipts with zero double-counting
-- ----------------------------------------------------------------------------
CREATE VIEW public.vw_receipt_reconciliation AS
WITH allocated_sum AS (
    SELECT 
        TRIM(receipt_no) AS r_no,
        SUM(COALESCE(allocated_amount, 0)) AS total_allocated,
        COUNT(allocation_id) AS allocation_count
    FROM public.receipt_allocations
    GROUP BY TRIM(receipt_no)
)
SELECT 
    pr.receipt_id,
    pr.receipt_no,
    pr.consumer_no,
    pr.account_no,
    pr.consumer_name,
    pr.collections_date,
    pr.bill_month,
    COALESCE(pr.amount_paid, 0) AS receipt_amount,
    COALESCE(a.total_allocated, pr.amount_paid, 0) AS allocated_amount,
    GREATEST(0.0, COALESCE(pr.amount_paid, 0) - COALESCE(a.total_allocated, pr.amount_paid, 0)) AS unallocated_balance,
    CASE 
        WHEN COALESCE(pr.amount_paid, 0) = 0 THEN 'ZERO_AMOUNT'
        WHEN COALESCE(a.total_allocated, pr.amount_paid, 0) >= pr.amount_paid THEN 'MATCHED'
        WHEN COALESCE(a.total_allocated, 0) > 0 THEN 'PARTIAL'
        ELSE 'UNALLOCATED'
    END AS allocation_status,
    pr.source_pdf,
    pr.created_at
FROM public.payment_receipts pr
LEFT JOIN allocated_sum a ON TRIM(pr.receipt_no) = a.r_no;

-- ----------------------------------------------------------------------------
-- VIEW 4: public.vw_budget_vs_actual
-- Compares approved budget per plaza/month with actual bills
-- ----------------------------------------------------------------------------
CREATE VIEW public.vw_budget_vs_actual AS
WITH actuals AS (
    SELECT 
        toll_plaza_id,
        bill_month,
        financial_year,
        bill_type,
        SUM(total_billed_kwh) AS actual_units,
        SUM(total_amount_payable) AS actual_bill_amount,
        SUM(amount_paid) AS actual_paid_amount
    FROM public.vw_official_bill_register
    GROUP BY toll_plaza_id, bill_month, financial_year, bill_type
),
budgets AS (
    SELECT 
        toll_plaza_id,
        bill_month,
        financial_year,
        bill_type,
        SUM(budget_amount) AS approved_budget_amount
    FROM public.monthly_budgets
    GROUP BY toll_plaza_id, bill_month, financial_year, bill_type
)
SELECT 
    COALESCE(a.toll_plaza_id, b.toll_plaza_id) AS toll_plaza_id,
    COALESCE(a.bill_month, b.bill_month) AS bill_month,
    COALESCE(a.financial_year, b.financial_year, '2026-27') AS financial_year,
    COALESCE(a.bill_type, b.bill_type, 'ALL') AS bill_type,
    COALESCE(b.approved_budget_amount, 
        CASE 
            WHEN COALESCE(a.toll_plaza_id, b.toll_plaza_id) = 'TP01' THEN 250000.0
            WHEN COALESCE(a.toll_plaza_id, b.toll_plaza_id) = 'TP02' THEN 220000.0
            WHEN COALESCE(a.toll_plaza_id, b.toll_plaza_id) = 'TP03' THEN 200000.0
            ELSE 200000.0
        END
    ) AS approved_budget,
    COALESCE(a.actual_bill_amount, 0) AS actual_billed_amount,
    COALESCE(a.actual_paid_amount, 0) AS actual_paid_amount,
    (COALESCE(a.actual_bill_amount, 0) - COALESCE(b.approved_budget_amount, 
        CASE 
            WHEN COALESCE(a.toll_plaza_id, b.toll_plaza_id) = 'TP01' THEN 250000.0
            WHEN COALESCE(a.toll_plaza_id, b.toll_plaza_id) = 'TP02' THEN 220000.0
            WHEN COALESCE(a.toll_plaza_id, b.toll_plaza_id) = 'TP03' THEN 200000.0
            ELSE 200000.0
        END
    )) AS budget_variance_amount,
    ROUND(
        CASE 
            WHEN COALESCE(b.approved_budget_amount, 200000.0) > 0 
            THEN ((COALESCE(a.actual_bill_amount, 0) - COALESCE(b.approved_budget_amount, 200000.0)) / COALESCE(b.approved_budget_amount, 200000.0)) * 100.0 
            ELSE 0.0 
        END, 
        2
    ) AS budget_variance_percentage
FROM actuals a
FULL OUTER JOIN budgets b 
    ON a.toll_plaza_id = b.toll_plaza_id 
   AND a.bill_month = b.bill_month 
   AND a.bill_type = b.bill_type;

-- ----------------------------------------------------------------------------
-- VIEW 5: public.vw_rebate_performance
-- Rebate tracking: eligible vs claimed vs lost
-- ----------------------------------------------------------------------------
CREATE VIEW public.vw_rebate_performance AS
SELECT 
    toll_plaza_id,
    bill_month,
    financial_year,
    bill_type,
    COUNT(*) AS total_bills,
    SUM(COALESCE(prompt_rebate, 0)) AS eligible_prompt_rebate,
    SUM(
        CASE 
            WHEN payment_status = 'PAID' THEN COALESCE(prompt_rebate, 0)
            ELSE 0.0 
        END
    ) AS claimed_prompt_rebate,
    SUM(
        CASE 
            WHEN payment_status != 'PAID' THEN COALESCE(prompt_rebate, 0)
            ELSE 0.0 
        END
    ) AS lost_prompt_rebate,
    ROUND(
        CASE 
            WHEN SUM(COALESCE(prompt_rebate, 0)) > 0 
            THEN (SUM(CASE WHEN payment_status = 'PAID' THEN COALESCE(prompt_rebate, 0) ELSE 0.0 END) / SUM(COALESCE(prompt_rebate, 0))) * 100.0 
            ELSE 0.0 
        END, 
        2
    ) AS rebate_realization_rate
FROM public.vw_official_bill_register
GROUP BY toll_plaza_id, bill_month, financial_year, bill_type;

-- ----------------------------------------------------------------------------
-- VIEW 6: public.vw_bill_kpi_summary
-- Executive KPI Summary by plaza, month, type, basis
-- ----------------------------------------------------------------------------
CREATE VIEW public.vw_bill_kpi_summary AS
SELECT 
    toll_plaza_id,
    bill_month,
    financial_year,
    bill_type,
    bill_basis,
    COUNT(*) AS total_bills_generated,
    SUM(total_billed_kwh) AS total_billed_kwh,
    SUM(total_amount_payable) AS total_billed_amount,
    SUM(amount_paid) AS total_paid_amount,
    SUM(outstanding_balance) AS total_outstanding_balance,
    ROUND(
        CASE 
            WHEN SUM(total_amount_payable) > 0 
            THEN (SUM(amount_paid) / SUM(total_amount_payable)) * 100.0 
            ELSE 0.0 
        END, 
        2
    ) AS realization_percentage,
    COUNT(CASE WHEN payment_status = 'PAID' THEN 1 END) AS count_paid_bills,
    COUNT(CASE WHEN payment_status = 'PARTIAL' THEN 1 END) AS count_partial_bills,
    COUNT(CASE WHEN payment_status = 'UNPAID' THEN 1 END) AS count_unpaid_bills,
    SUM(prompt_rebate) AS prompt_rebate_eligible
FROM public.vw_official_bill_register
GROUP BY toll_plaza_id, bill_month, financial_year, bill_type, bill_basis;

-- ----------------------------------------------------------------------------
-- VIEW 7: public.vw_import_batch_acknowledgement
-- Batch status with counts
-- ----------------------------------------------------------------------------
CREATE VIEW public.vw_import_batch_acknowledgement AS
SELECT 
    event_id AS batch_id,
    event_time,
    event_type,
    details,
    result AS batch_status,
    created_at
FROM public.audit_events
WHERE event_type ILIKE '%BATCH%' OR event_type ILIKE '%UPLOAD%' OR event_type ILIKE '%IMPORT%';

-- ----------------------------------------------------------------------------
-- VIEW 8: public.vw_duplicate_rejections
-- Audit of duplicate attempts rejected
-- ----------------------------------------------------------------------------
CREATE VIEW public.vw_duplicate_rejections AS
SELECT 
    event_id,
    event_time,
    entity_id AS bill_number_attempted,
    details AS rejection_reason,
    result,
    created_at
FROM public.audit_events
WHERE result = 'DUPLICATE_REJECTED';

-- ============================================================================
-- STEP 5: COMPATIBILITY VIEWS (v_energy_bills_master, v_energy_consumer_realtime, etc.)
-- ============================================================================

CREATE VIEW public.v_energy_bills_master AS
SELECT * FROM public.vw_official_bill_register;

CREATE VIEW public.v_energy_bills_provisional_master AS
SELECT 
    bp.bill_id,
    bp.bill_number,
    bp.consumer_account_no,
    bp.source_filename,
    COALESCE(m.toll_plaza_id, 
        CASE 
            WHEN bp.consumer_account_no LIKE '416%' OR bp.consumer_account_no LIKE '411%' THEN 'TP01'
            WHEN bp.consumer_account_no LIKE '413%' THEN 'TP02'
            WHEN bp.consumer_account_no LIKE '812%' OR bp.consumer_account_no LIKE '813%' THEN 'TP03'
            ELSE 'TP01'
        END
    ) AS toll_plaza_id,
    COALESCE(m.bill_type, 'LT') AS bill_type,
    COALESCE(m.asset_code, '') AS asset_code,
    COALESCE(m.consumer_scope, 'HIGHWAY') AS consumer_scope,
    COALESCE(m.division_name, bp.division, 'SED') AS division_name,
    COALESCE(m.usage_type, bp.tariff_category, 'Public Light') AS usage_type,
    COALESCE(m.sanctioned_load_kw, 10.0) AS sanctioned_load_kw,
    COALESCE(m.location, 'Corridor Lighting') AS location,
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
    0.0 AS amount_paid,
    COALESCE(bp.total_amount_payable, bp.current_total, 0) AS outstanding_balance,
    'UNPAID' AS payment_status,
    'GENERATED' AS bill_present,
    NULL::VARCHAR AS latest_payment_date,
    bp.verification_status,
    bp.is_edited,
    bp.created_at
FROM public.energy_bills_provisional bp
LEFT JOIN energy_master.consumer_account m 
    ON TRIM(bp.consumer_account_no) = TRIM(m.consumer_account_no);

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
    WHERE COALESCE(is_voided, false) = false
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
    WHERE COALESCE(is_voided, false) = false
    GROUP BY TRIM(consumer_account_no)
),
receipts_summary AS (
    SELECT 
        COALESCE(TRIM(account_no), TRIM(consumer_no)) AS ac_no,
        COUNT(receipt_no) AS payments_count,
        MAX(collections_date) AS latest_payment_date,
        SUM(COALESCE(amount_paid, 0)) AS total_paid_amount
    FROM public.payment_receipts
    GROUP BY COALESCE(TRIM(account_no), TRIM(consumer_no))
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
    m.is_active,
    m.remarks,
    COALESCE(act.actual_bills_count, 0) AS actual_bills_count,
    COALESCE(prv.prov_bills_count, 0) AS provisional_bills_count,
    (COALESCE(act.actual_bills_count, 0) + COALESCE(prv.prov_bills_count, 0)) AS total_bills_count,
    COALESCE(act.latest_actual_month, prv.latest_prov_month, '—') AS latest_bill_month,
    COALESCE(act.actual_billed_kwh, 0) AS actual_billed_kwh,
    COALESCE(prv.prov_billed_kwh, 0) AS provisional_billed_kwh,
    COALESCE(act.actual_billed_amount, 0) AS actual_billed_amount,
    COALESCE(act.actual_amount_payable, 0) AS total_amount_payable,
    COALESCE(rec.total_paid_amount, 0) AS total_paid_amount,
    GREATEST(0.0, COALESCE(act.actual_amount_payable, 0) - COALESCE(rec.total_paid_amount, 0)) AS outstanding_balance,
    CASE 
        WHEN (COALESCE(act.actual_amount_payable, 0) - COALESCE(rec.total_paid_amount, 0)) <= 1.0 AND COALESCE(rec.total_paid_amount, 0) > 0 THEN 'PAID'
        WHEN COALESCE(rec.total_paid_amount, 0) > 0 THEN 'PARTIAL'
        ELSE 'UNPAID'
    END AS overall_payment_status,
    rec.latest_payment_date,
    m.created_at,
    m.updated_at
FROM energy_master.consumer_account m
LEFT JOIN bills_actual_summary act ON TRIM(m.consumer_account_no) = act.ac_no
LEFT JOIN bills_prov_summary prv ON TRIM(m.consumer_account_no) = prv.ac_no
LEFT JOIN receipts_summary rec ON TRIM(m.consumer_account_no) = rec.ac_no;

CREATE VIEW public.v_energy_billing_kpis AS
SELECT * FROM public.vw_bill_kpi_summary;

CREATE VIEW public.v_missing_bills_realtime AS
WITH active_cycles AS (
    SELECT DISTINCT bill_month 
    FROM public.energy_bills 
    WHERE bill_month IS NOT NULL AND bill_month != ''
    UNION
    SELECT DISTINCT bill_month 
    FROM public.energy_bills_provisional 
    WHERE bill_month IS NOT NULL AND bill_month != ''
)
SELECT 
    c.bill_month,
    m.toll_plaza_id,
    m.consumer_account_no,
    m.bill_type,
    m.asset_code,
    m.consumer_scope,
    m.division_name,
    m.usage_type,
    m.sanctioned_load_kw,
    m.location,
    'NOT GENERATED' AS bill_present_status,
    'MISSING_IN_CYCLE' AS issue_type
FROM energy_master.consumer_account m
CROSS JOIN active_cycles c
LEFT JOIN public.energy_bills b 
    ON TRIM(m.consumer_account_no) = TRIM(b.consumer_account_no) 
    AND TRIM(c.bill_month) = TRIM(b.bill_month)
    AND COALESCE(b.is_voided, false) = false
LEFT JOIN public.energy_bills_provisional bp 
    ON TRIM(m.consumer_account_no) = TRIM(bp.consumer_account_no) 
    AND TRIM(c.bill_month) = TRIM(bp.bill_month)
    AND COALESCE(bp.is_voided, false) = false
WHERE m.is_active = true
  AND b.bill_id IS NULL
  AND bp.bill_id IS NULL;

CREATE VIEW public.v_energy_consumer_reconciliation AS
WITH aggregated_readings AS (
    SELECT 
        TRIM(asset_code) AS asset_code,
        TO_CHAR(reading_datetime, 'Mon YYYY') AS reading_month,
        SUM(COALESCE(interval_kwh, 0)) AS metered_kwh_juno,
        AVG(COALESCE(pf, 1.0)) AS avg_pf,
        MAX(COALESCE(maximum_demand, 0)) AS peak_demand_kw
    FROM energy_readings.eb
    GROUP BY TRIM(asset_code), TO_CHAR(reading_datetime, 'Mon YYYY')
),
aggregated_bills AS (
    SELECT 
        TRIM(consumer_account_no) AS consumer_account_no,
        TRIM(bill_month) AS bill_month,
        SUM(COALESCE(slab_normal_kwh, 0) + COALESCE(slab_peak_kwh, 0) + COALESCE(slab_solar_kwh, 0)) AS billed_kwh_discom,
        SUM(COALESCE(total_amount_payable, current_total, 0)) AS billed_amount,
        MAX(bill_number) AS bill_number
    FROM public.energy_bills
    WHERE COALESCE(is_voided, false) = false
    GROUP BY TRIM(consumer_account_no), TRIM(bill_month)
)
SELECT 
    m.consumer_account_no,
    m.toll_plaza_id,
    m.bill_type,
    m.asset_code,
    m.location,
    COALESCE(b.bill_month, rd.reading_month) AS billing_cycle,
    COALESCE(b.bill_number, '—') AS discom_bill_no,
    COALESCE(b.billed_kwh_discom, 0) AS billed_kwh_discom,
    COALESCE(rd.metered_kwh_juno, 0) AS metered_kwh_juno,
    (COALESCE(b.billed_kwh_discom, 0) - COALESCE(rd.metered_kwh_juno, 0)) AS variance_kwh,
    ROUND(
        CASE 
            WHEN COALESCE(b.billed_kwh_discom, 0) > 0 
            THEN ((COALESCE(b.billed_kwh_discom, 0) - COALESCE(rd.metered_kwh_juno, 0)) / b.billed_kwh_discom) * 100.0 
            ELSE 0.0 
        END, 
        2
    ) AS variance_pct,
    COALESCE(b.billed_amount, 0) AS billed_amount,
    COALESCE(rd.avg_pf, 1.0) AS avg_power_factor,
    COALESCE(rd.peak_demand_kw, 0) AS peak_demand_kw,
    CASE 
        WHEN b.bill_number IS NULL THEN 'NO_DISCOM_BILL'
        WHEN rd.reading_month IS NULL THEN 'NO_JUNO_TELEMETRY'
        WHEN ABS(COALESCE(b.billed_kwh_discom, 0) - COALESCE(rd.metered_kwh_juno, 0)) > 500.0 THEN 'DISCREPANCY_ALERT'
        ELSE 'RECONCILED'
    END AS reconciliation_status
FROM energy_master.consumer_account m
LEFT JOIN aggregated_bills b ON TRIM(m.consumer_account_no) = b.consumer_account_no
LEFT JOIN aggregated_readings rd ON TRIM(m.asset_code) = rd.asset_code AND b.bill_month = rd.reading_month;

-- ============================================================================
-- STEP 6: PERMISSIONS & RLS CONFIGURATION
-- ============================================================================
ALTER TABLE energy_master.consumer_account ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.energy_bills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.energy_bills_provisional ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payment_receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.receipt_allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.monthly_budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bill_review_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE energy_readings.eb ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    DROP POLICY IF EXISTS "Public access to consumer_account" ON energy_master.consumer_account;
    CREATE POLICY "Public access to consumer_account" ON energy_master.consumer_account FOR ALL USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "Public access to energy_bills" ON public.energy_bills;
    CREATE POLICY "Public access to energy_bills" ON public.energy_bills FOR ALL USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "Public access to energy_bills_provisional" ON public.energy_bills_provisional;
    CREATE POLICY "Public access to energy_bills_provisional" ON public.energy_bills_provisional FOR ALL USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "Public access to payment_receipts" ON public.payment_receipts;
    CREATE POLICY "Public access to payment_receipts" ON public.payment_receipts FOR ALL USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "Public access to receipt_allocations" ON public.receipt_allocations;
    CREATE POLICY "Public access to receipt_allocations" ON public.receipt_allocations FOR ALL USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "Public access to monthly_budgets" ON public.monthly_budgets;
    CREATE POLICY "Public access to monthly_budgets" ON public.monthly_budgets FOR ALL USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "Public access to bill_review_queue" ON public.bill_review_queue;
    CREATE POLICY "Public access to bill_review_queue" ON public.bill_review_queue FOR ALL USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "Public access to audit_events" ON public.audit_events;
    CREATE POLICY "Public access to audit_events" ON public.audit_events FOR ALL USING (true) WITH CHECK (true);

    DROP POLICY IF EXISTS "Public access to eb_readings" ON energy_readings.eb;
    CREATE POLICY "Public access to eb_readings" ON energy_readings.eb FOR ALL USING (true) WITH CHECK (true);
EXCEPTION WHEN OTHERS THEN
    NULL;
END $$;

GRANT USAGE ON SCHEMA public, energy_master, energy_readings TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA energy_master TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA energy_readings TO anon, authenticated, service_role;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;

-- Notify PostgREST schema cache reload
NOTIFY pgrst, 'reload schema';
