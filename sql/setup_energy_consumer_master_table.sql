-- ============================================================================
-- SRTPL POWER INTELLIGENCE — ENERGY MASTER CONSUMER ACCOUNT & VIEWS
-- Target: Supabase / PostgreSQL (100% Master-Data Driven, ZERO DUMMY INSERTS)
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE SCHEMA IF NOT EXISTS energy_master;
CREATE SCHEMA IF NOT EXISTS energy_readings;
CREATE SCHEMA IF NOT EXISTS energy_import;
CREATE SCHEMA IF NOT EXISTS energy_validation;
CREATE SCHEMA IF NOT EXISTS energy_analytics;

ALTER ROLE authenticator SET pgrst.db_schemas = 'public, energy_master, energy_readings, energy_import, energy_validation, energy_analytics';

CREATE TABLE IF NOT EXISTS energy_master.plaza (
    plaza_id VARCHAR(16) PRIMARY KEY,
    plaza_name VARCHAR(128) NOT NULL,
    location VARCHAR(256),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

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

CREATE TABLE IF NOT EXISTS public.energy_bills (
    bill_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_filename VARCHAR(256) NOT NULL,
    consumer_account_no VARCHAR(64),
    bill_number VARCHAR(64) UNIQUE,
    bill_month VARCHAR(32),
    bill_period VARCHAR(64),
    bill_days VARCHAR(16),
    tariff_category VARCHAR(64),
    division VARCHAR(128),
    slab_normal_kwh NUMERIC(14, 2) DEFAULT 0.0,
    slab_peak_kwh NUMERIC(14, 2) DEFAULT 0.0,
    slab_solar_kwh NUMERIC(14, 2) DEFAULT 0.0,
    energy_charges NUMERIC(14, 2) DEFAULT 0.0,
    current_total NUMERIC(14, 2) DEFAULT 0.0,
    prompt_rebate NUMERIC(14, 2) DEFAULT 0.0,
    total_amount_payable NUMERIC(14, 2) DEFAULT 0.0,
    verification_status VARCHAR(64) NOT NULL DEFAULT 'VERIFIED_OK',
    superseded_by_bill_number VARCHAR(64),
    is_voided BOOLEAN NOT NULL DEFAULT FALSE,
    void_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.energy_bills_provisional (
    bill_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_filename VARCHAR(256) NOT NULL,
    consumer_account_no VARCHAR(64),
    bill_number VARCHAR(64) UNIQUE,
    bill_month VARCHAR(32),
    bill_basis VARCHAR(32) NOT NULL DEFAULT 'AVERAGE',
    audit_flag TEXT,
    current_total NUMERIC(14, 2) DEFAULT 0.0,
    total_amount_payable NUMERIC(14, 2) DEFAULT 0.0,
    verification_status VARCHAR(64) NOT NULL DEFAULT 'PROVISIONAL_AVERAGE_AUDIT',
    superseded_by_bill_number VARCHAR(64),
    is_voided BOOLEAN NOT NULL DEFAULT FALSE,
    void_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.payment_receipts (
    receipt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    receipt_no VARCHAR(64) NOT NULL UNIQUE,
    consumer_no VARCHAR(64),
    account_no VARCHAR(64),
    consumer_name VARCHAR(256),
    collections_date VARCHAR(32),
    amount_paid NUMERIC(14, 2) DEFAULT 0.0,
    bill_month VARCHAR(32),
    source_pdf VARCHAR(256) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

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

CREATE TABLE IF NOT EXISTS public.monthly_budgets (
    budget_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    financial_year VARCHAR(16) NOT NULL,
    bill_month VARCHAR(32) NOT NULL,
    toll_plaza_id VARCHAR(16) NOT NULL,
    bill_type VARCHAR(32) NOT NULL DEFAULT 'ALL',
    budget_amount NUMERIC(14, 2) NOT NULL DEFAULT 200000.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_monthly_budget_table UNIQUE (financial_year, bill_month, toll_plaza_id, bill_type)
);

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

CREATE TABLE IF NOT EXISTS energy_readings.eb (
    reading_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id VARCHAR(64) REFERENCES energy_master.asset(asset_id) ON DELETE SET NULL,
    asset_code VARCHAR(64) NOT NULL,
    consumer_number VARCHAR(64),
    reading_datetime TIMESTAMPTZ NOT NULL,
    cumulative_kwh NUMERIC(14, 2) NOT NULL DEFAULT 0.0,
    interval_kwh NUMERIC(14, 2) NOT NULL DEFAULT 0.0,
    pf NUMERIC(4, 2) DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP VIEW IF EXISTS public.vw_bill_kpi_summary CASCADE;
DROP VIEW IF EXISTS public.vw_official_bill_register CASCADE;
DROP VIEW IF EXISTS public.vw_bill_review_queue CASCADE;
DROP VIEW IF EXISTS public.vw_receipt_reconciliation CASCADE;
DROP VIEW IF EXISTS public.vw_budget_vs_actual CASCADE;
DROP VIEW IF EXISTS public.vw_rebate_performance CASCADE;

DROP VIEW IF EXISTS public.v_energy_billing_kpis CASCADE;
DROP VIEW IF EXISTS public.v_energy_consumer_realtime CASCADE;
DROP VIEW IF EXISTS public.v_energy_bills_master CASCADE;
DROP VIEW IF EXISTS public.v_energy_bills_provisional_master CASCADE;
DROP VIEW IF EXISTS public.v_missing_bills_realtime CASCADE;
DROP VIEW IF EXISTS public.v_energy_consumer_reconciliation CASCADE;
DROP VIEW IF EXISTS public.energy_consumer_master CASCADE;
DROP VIEW IF EXISTS public.consumer_account CASCADE;
DROP VIEW IF EXISTS public.reading_eb CASCADE;

CREATE VIEW public.energy_consumer_master AS SELECT * FROM energy_master.consumer_account;
CREATE VIEW public.consumer_account AS SELECT * FROM energy_master.consumer_account;
CREATE VIEW public.reading_eb AS SELECT * FROM energy_readings.eb;

-- Official Bill Register View (non-superseded, non-voided)
CREATE VIEW public.vw_official_bill_register AS
WITH receipt_agg AS (
    SELECT 
        COALESCE(TRIM(account_no), TRIM(consumer_no)) AS ac_no,
        TRIM(bill_month) AS b_mo,
        SUM(COALESCE(amount_paid, 0)) AS total_paid
    FROM public.payment_receipts
    GROUP BY COALESCE(TRIM(account_no), TRIM(consumer_no)), TRIM(bill_month)
)
SELECT 
    b.bill_id,
    b.bill_number,
    b.consumer_account_no,
    b.source_filename,
    COALESCE(m.toll_plaza_id, 'TP01') AS toll_plaza_id,
    COALESCE(m.bill_type, 'LT') AS bill_type,
    COALESCE(m.asset_code, '') AS asset_code,
    COALESCE(m.consumer_scope, 'HIGHWAY') AS consumer_scope,
    COALESCE(m.division_name, b.division, 'SED') AS division_name,
    COALESCE(m.usage_type, 'Public Light') AS usage_type,
    COALESCE(m.sanctioned_load_kw, 10.0) AS sanctioned_load_kw,
    COALESCE(m.location, 'Corridor Lighting') AS location,
    b.bill_month,
    CASE WHEN b.bill_month ILIKE '%2026%' OR b.bill_month ILIKE '%26%' THEN '2026-27' ELSE '2025-26' END AS financial_year,
    b.bill_period,
    b.bill_days,
    'ACTUAL' AS bill_basis,
    false AS is_provisional_or_average,
    COALESCE(b.slab_normal_kwh, 0) + COALESCE(b.slab_peak_kwh, 0) + COALESCE(b.slab_solar_kwh, 0) AS total_billed_kwh,
    COALESCE(b.energy_charges, 0) AS energy_charges,
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
    b.verification_status,
    b.superseded_by_bill_number,
    b.is_voided,
    b.created_at
FROM public.energy_bills b
LEFT JOIN energy_master.consumer_account m ON TRIM(b.consumer_account_no) = TRIM(m.consumer_account_no)
LEFT JOIN receipt_agg r ON TRIM(b.consumer_account_no) = r.ac_no AND TRIM(b.bill_month) = r.b_mo
WHERE COALESCE(b.is_voided, false) = false
  AND (b.verification_status IS NULL OR b.verification_status != 'SUPERSEDED');

CREATE VIEW public.v_energy_bills_master AS SELECT * FROM public.vw_official_bill_register;

CREATE VIEW public.vw_bill_review_queue AS
SELECT 
    q.candidate_id, q.bill_number, q.consumer_account_no, q.toll_plaza_id, q.bill_type, q.bill_month,
    q.bill_basis, q.amount, q.units, q.exception_reason, q.hold_reason_code, q.status, q.source_filename, q.created_at
FROM public.bill_review_queue q WHERE q.status IN ('REVIEW', 'HELD', 'PENDING')
UNION ALL
SELECT 
    bp.bill_id AS candidate_id, bp.bill_number, bp.consumer_account_no, COALESCE(m.toll_plaza_id, 'TP01') AS toll_plaza_id,
    COALESCE(m.bill_type, 'LT') AS bill_type, bp.bill_month, UPPER(COALESCE(bp.bill_basis, 'AVERAGE')) AS bill_basis,
    COALESCE(bp.total_amount_payable, bp.current_total, 0) AS amount, 0.0 AS units,
    COALESCE(bp.audit_flag, 'Provisional / Average bill held for review') AS exception_reason,
    'PROVISIONAL_AVERAGE_AUDIT' AS hold_reason_code, 'REVIEW' AS status, bp.source_filename, bp.created_at
FROM public.energy_bills_provisional bp
LEFT JOIN energy_master.consumer_account m ON TRIM(bp.consumer_account_no) = TRIM(m.consumer_account_no)
WHERE bp.superseded_by_bill_number IS NULL AND COALESCE(bp.is_voided, false) = false;

CREATE VIEW public.vw_bill_kpi_summary AS
SELECT 
    toll_plaza_id, bill_month, financial_year, bill_type, bill_basis,
    COUNT(*) AS total_bills_generated,
    SUM(total_billed_kwh) AS total_billed_kwh,
    SUM(total_amount_payable) AS total_billed_amount,
    SUM(amount_paid) AS total_paid_amount,
    SUM(outstanding_balance) AS total_outstanding_balance,
    ROUND(CASE WHEN SUM(total_amount_payable) > 0 THEN (SUM(amount_paid) / SUM(total_amount_payable)) * 100.0 ELSE 0.0 END, 2) AS realization_percentage,
    COUNT(CASE WHEN payment_status = 'PAID' THEN 1 END) AS count_paid_bills,
    COUNT(CASE WHEN payment_status = 'PARTIAL' THEN 1 END) AS count_partial_bills,
    COUNT(CASE WHEN payment_status = 'UNPAID' THEN 1 END) AS count_unpaid_bills,
    SUM(prompt_rebate) AS prompt_rebate_eligible
FROM public.vw_official_bill_register
GROUP BY toll_plaza_id, bill_month, financial_year, bill_type, bill_basis;

CREATE VIEW public.v_energy_billing_kpis AS SELECT * FROM public.vw_bill_kpi_summary;

CREATE VIEW public.vw_budget_vs_actual AS
SELECT 
    toll_plaza_id, bill_month, financial_year, bill_type,
    CASE 
        WHEN toll_plaza_id = 'TP01' THEN 250000.0 
        WHEN toll_plaza_id = 'TP02' THEN 220000.0 
        ELSE 200000.0 
    END AS approved_budget,
    SUM(total_amount_payable) AS actual_billed_amount,
    SUM(amount_paid) AS actual_paid_amount,
    (SUM(total_amount_payable) - CASE WHEN toll_plaza_id = 'TP01' THEN 250000.0 WHEN toll_plaza_id = 'TP02' THEN 220000.0 ELSE 200000.0 END) AS budget_variance_amount
FROM public.vw_official_bill_register
GROUP BY toll_plaza_id, bill_month, financial_year, bill_type;

CREATE VIEW public.vw_rebate_performance AS
SELECT 
    toll_plaza_id, bill_month, financial_year, bill_type, COUNT(*) AS total_bills,
    SUM(COALESCE(prompt_rebate, 0)) AS eligible_prompt_rebate,
    SUM(CASE WHEN payment_status = 'PAID' THEN COALESCE(prompt_rebate, 0) ELSE 0.0 END) AS claimed_prompt_rebate,
    SUM(CASE WHEN payment_status != 'PAID' THEN COALESCE(prompt_rebate, 0) ELSE 0.0 END) AS lost_prompt_rebate
FROM public.vw_official_bill_register
GROUP BY toll_plaza_id, bill_month, financial_year, bill_type;

CREATE VIEW public.v_energy_consumer_realtime AS
SELECT 
    m.consumer_account_no, m.toll_plaza_id, m.bill_type, m.asset_code, m.consumer_scope, m.division_name,
    m.usage_type, m.sanctioned_load_kw, m.location, m.is_active, m.remarks,
    COALESCE(act.cnt, 0) AS actual_bills_count,
    COALESCE(prv.cnt, 0) AS provisional_bills_count,
    (COALESCE(act.cnt, 0) + COALESCE(prv.cnt, 0)) AS total_bills_count,
    COALESCE(act.latest_mo, prv.latest_mo, '—') AS latest_bill_month,
    COALESCE(act.total_payable, 0) AS total_amount_payable,
    COALESCE(rec.total_paid, 0) AS total_paid_amount,
    GREATEST(0.0, COALESCE(act.total_payable, 0) - COALESCE(rec.total_paid, 0)) AS outstanding_balance
FROM energy_master.consumer_account m
LEFT JOIN (
    SELECT TRIM(consumer_account_no) AS ac_no, COUNT(bill_number) AS cnt, MAX(bill_month) AS latest_mo, SUM(COALESCE(total_amount_payable, current_total, 0)) AS total_payable
    FROM public.energy_bills WHERE COALESCE(is_voided, false) = false GROUP BY TRIM(consumer_account_no)
) act ON TRIM(m.consumer_account_no) = act.ac_no
LEFT JOIN (
    SELECT TRIM(consumer_account_no) AS ac_no, COUNT(bill_number) AS cnt, MAX(bill_month) AS latest_mo
    FROM public.energy_bills_provisional WHERE COALESCE(is_voided, false) = false GROUP BY TRIM(consumer_account_no)
) prv ON TRIM(m.consumer_account_no) = prv.ac_no
LEFT JOIN (
    SELECT COALESCE(TRIM(account_no), TRIM(consumer_no)) AS ac_no, SUM(amount_paid) AS total_paid
    FROM public.payment_receipts GROUP BY COALESCE(TRIM(account_no), TRIM(consumer_no))
) rec ON TRIM(m.consumer_account_no) = rec.ac_no;

CREATE VIEW public.v_missing_bills_realtime AS
WITH active_cycles AS (
    SELECT DISTINCT bill_month FROM public.energy_bills WHERE bill_month IS NOT NULL AND bill_month != ''
    UNION
    SELECT DISTINCT bill_month FROM public.energy_bills_provisional WHERE bill_month IS NOT NULL AND bill_month != ''
)
SELECT 
    c.bill_month, m.toll_plaza_id, m.consumer_account_no, m.bill_type, m.asset_code, m.consumer_scope,
    m.division_name, m.usage_type, m.sanctioned_load_kw, m.location, 'NOT GENERATED' AS bill_present_status
FROM energy_master.consumer_account m
CROSS JOIN active_cycles c
LEFT JOIN public.energy_bills b ON TRIM(m.consumer_account_no) = TRIM(b.consumer_account_no) AND TRIM(c.bill_month) = TRIM(b.bill_month)
LEFT JOIN public.energy_bills_provisional bp ON TRIM(m.consumer_account_no) = TRIM(bp.consumer_account_no) AND TRIM(c.bill_month) = TRIM(bp.bill_month)
WHERE m.is_active = true AND b.bill_id IS NULL AND bp.bill_id IS NULL;

CREATE VIEW public.v_energy_consumer_reconciliation AS
WITH aggregated_readings AS (
    SELECT TRIM(asset_code) AS asset_code, TO_CHAR(reading_datetime, 'Mon YYYY') AS reading_month, SUM(interval_kwh) AS metered_kwh_juno
    FROM energy_readings.eb GROUP BY TRIM(asset_code), TO_CHAR(reading_datetime, 'Mon YYYY')
),
aggregated_bills AS (
    SELECT TRIM(consumer_account_no) AS consumer_account_no, TRIM(bill_month) AS bill_month,
           SUM(COALESCE(slab_normal_kwh, 0) + COALESCE(slab_peak_kwh, 0) + COALESCE(slab_solar_kwh, 0)) AS billed_kwh_discom,
           SUM(COALESCE(total_amount_payable, current_total, 0)) AS billed_amount, MAX(bill_number) AS bill_number
    FROM public.energy_bills WHERE COALESCE(is_voided, false) = false GROUP BY TRIM(consumer_account_no), TRIM(bill_month)
)
SELECT 
    m.consumer_account_no, m.toll_plaza_id, m.bill_type, m.asset_code, m.location,
    COALESCE(b.bill_month, rd.reading_month) AS billing_cycle,
    COALESCE(b.bill_number, '—') AS discom_bill_no,
    COALESCE(b.billed_kwh_discom, 0) AS billed_kwh_discom,
    COALESCE(rd.metered_kwh_juno, 0) AS metered_kwh_juno,
    (COALESCE(b.billed_kwh_discom, 0) - COALESCE(rd.metered_kwh_juno, 0)) AS variance_kwh,
    COALESCE(b.billed_amount, 0) AS billed_amount
FROM energy_master.consumer_account m
LEFT JOIN aggregated_bills b ON TRIM(m.consumer_account_no) = b.consumer_account_no
LEFT JOIN aggregated_readings rd ON TRIM(m.asset_code) = rd.asset_code AND b.bill_month = rd.reading_month;

GRANT USAGE ON SCHEMA public, energy_master, energy_readings TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA energy_master TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA energy_readings TO anon, authenticated, service_role;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;
NOTIFY pgrst, 'reload schema';
