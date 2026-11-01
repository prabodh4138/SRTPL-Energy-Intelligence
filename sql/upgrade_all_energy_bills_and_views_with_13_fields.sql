-- ============================================================================
-- SRTPL POWER INTELLIGENCE — COMPREHENSIVE SCHEMA UPGRADE & VIEW REBUILD
-- Guarantees all 13 extraction fields, Feeder Classification (HT/LT),
-- Scope (PLAZA/HIGHWAY), Sanctioned Loads, and Rejected Bucket Archive.
-- Fixes column reference error for toll_plaza_id. Run in Supabase SQL Editor.
-- ============================================================================

-- 0. ENSURE SCHEMAS EXIST
CREATE SCHEMA IF NOT EXISTS energy_master;
CREATE SCHEMA IF NOT EXISTS public;

-- 1. UPGRADE public.energy_bills WITH ALL 13 EXTRACTED FIELDS & AUDIT COLUMNS
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS toll_plaza_id VARCHAR(16);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS bill_type VARCHAR(32) DEFAULT 'LT';
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS consumer_scope VARCHAR(64) DEFAULT 'HIGHWAY';
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS sanctioned_load_kw NUMERIC(10, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS contract_demand VARCHAR(64);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS security_deposit NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS md NUMERIC(10, 4) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS md_kw NUMERIC(10, 4) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS md_kva NUMERIC(10, 4) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS cuml_md_kva NUMERIC(10, 4) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS cuml_md_kw NUMERIC(10, 4) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS dps_rs NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS rebate_date VARCHAR(32);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS meter_sl_no VARCHAR(64);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS section VARCHAR(128);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS sub_division VARCHAR(128);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS division VARCHAR(128);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS tariff_category VARCHAR(128);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS tariff_type VARCHAR(64);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS bill_period VARCHAR(64);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS bill_days VARCHAR(16);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS bill_issue_date VARCHAR(32);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS due_date VARCHAR(32);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS bill_basis VARCHAR(32) DEFAULT 'ACTUAL';
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS net_payable_amount_before_rbt_dt_rs NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS net_payable_amount_after_rbt_dt_rs NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS slab_normal_kwh NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS slab_peak_kwh NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS slab_solar_kwh NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS energy_charges NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS demand_charge NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS tod_incentive NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS tod_surcharge NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS electricity_charges NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS electricity_duty NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS meter_rent NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS customer_service_charge NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS current_total NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS prompt_rebate NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS total_amount_payable NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS net_after_rebate NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS verification_status VARCHAR(64) DEFAULT 'VERIFIED_MATCH';
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS is_edited BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS edited_by VARCHAR(128);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS edited_at TIMESTAMPTZ;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS edit_notes TEXT;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS superseded_by_bill_number VARCHAR(64);
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS is_voided BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS void_reason TEXT;

-- 2. UPGRADE public.energy_bills_provisional
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS toll_plaza_id VARCHAR(16);
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS bill_type VARCHAR(32) DEFAULT 'LT';
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS consumer_scope VARCHAR(64) DEFAULT 'HIGHWAY';
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS sanctioned_load_kw NUMERIC(10, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS contract_demand VARCHAR(64);
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS security_deposit NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS md NUMERIC(10, 4) DEFAULT 0.0;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS md_kw NUMERIC(10, 4) DEFAULT 0.0;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS md_kva NUMERIC(10, 4) DEFAULT 0.0;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS cuml_md_kva NUMERIC(10, 4) DEFAULT 0.0;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS cuml_md_kw NUMERIC(10, 4) DEFAULT 0.0;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS dps_rs NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS rebate_date VARCHAR(32);
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS meter_sl_no VARCHAR(64);
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS section VARCHAR(128);
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS sub_division VARCHAR(128);
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS division VARCHAR(128);
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS tariff_category VARCHAR(128);
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS tariff_type VARCHAR(64);
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS bill_period VARCHAR(64);
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS bill_days VARCHAR(16);
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS bill_issue_date VARCHAR(32);
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS due_date VARCHAR(32);
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS bill_basis VARCHAR(32) DEFAULT 'PROVISIONAL';
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS net_payable_amount_before_rbt_dt_rs NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS net_payable_amount_after_rbt_dt_rs NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS is_edited BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS edited_by VARCHAR(128);
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS edited_at TIMESTAMPTZ;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS edit_notes TEXT;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS is_superseded BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE public.energy_bills_provisional ADD COLUMN IF NOT EXISTS superseded_by_bill_number VARCHAR(64);

-- 3. UPGRADE public.bill_review_queue
ALTER TABLE public.bill_review_queue ADD COLUMN IF NOT EXISTS toll_plaza_id VARCHAR(16);
ALTER TABLE public.bill_review_queue ADD COLUMN IF NOT EXISTS bill_type VARCHAR(32) DEFAULT 'LT';
ALTER TABLE public.bill_review_queue ADD COLUMN IF NOT EXISTS consumer_scope VARCHAR(64) DEFAULT 'HIGHWAY';
ALTER TABLE public.bill_review_queue ADD COLUMN IF NOT EXISTS sanctioned_load_kw NUMERIC(10, 2) DEFAULT 0.0;
ALTER TABLE public.bill_review_queue ADD COLUMN IF NOT EXISTS contract_demand VARCHAR(64);
ALTER TABLE public.bill_review_queue ADD COLUMN IF NOT EXISTS security_deposit NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.bill_review_queue ADD COLUMN IF NOT EXISTS md NUMERIC(10, 4) DEFAULT 0.0;
ALTER TABLE public.bill_review_queue ADD COLUMN IF NOT EXISTS cuml_md_kva NUMERIC(10, 4) DEFAULT 0.0;
ALTER TABLE public.bill_review_queue ADD COLUMN IF NOT EXISTS cuml_md_kw NUMERIC(10, 4) DEFAULT 0.0;
ALTER TABLE public.bill_review_queue ADD COLUMN IF NOT EXISTS dps_rs NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.bill_review_queue ADD COLUMN IF NOT EXISTS rebate_date VARCHAR(32);
ALTER TABLE public.bill_review_queue ADD COLUMN IF NOT EXISTS meter_sl_no VARCHAR(64);
ALTER TABLE public.bill_review_queue ADD COLUMN IF NOT EXISTS section VARCHAR(128);
ALTER TABLE public.bill_review_queue ADD COLUMN IF NOT EXISTS sub_division VARCHAR(128);
ALTER TABLE public.bill_review_queue ADD COLUMN IF NOT EXISTS tariff_category VARCHAR(128);
ALTER TABLE public.bill_review_queue ADD COLUMN IF NOT EXISTS net_payable_amount_before_rbt_dt_rs NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.bill_review_queue ADD COLUMN IF NOT EXISTS net_payable_amount_after_rbt_dt_rs NUMERIC(14, 2) DEFAULT 0.0;

-- 4. ENSURE PAYMENT RECEIPTS & BUDGET TABLES EXIST
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
    source_pdf VARCHAR(256),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.payment_receipts ADD COLUMN IF NOT EXISTS account_no VARCHAR(64);
ALTER TABLE public.payment_receipts ADD COLUMN IF NOT EXISTS consumer_no VARCHAR(64);
ALTER TABLE public.payment_receipts ADD COLUMN IF NOT EXISTS bill_month VARCHAR(32);
ALTER TABLE public.payment_receipts ADD COLUMN IF NOT EXISTS amount_paid NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.payment_receipts ADD COLUMN IF NOT EXISTS collections_date VARCHAR(32);

CREATE TABLE IF NOT EXISTS public.monthly_budgets (
    budget_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    toll_plaza_id VARCHAR(16) NOT NULL,
    bill_month VARCHAR(32) NOT NULL,
    financial_year VARCHAR(32) DEFAULT '2026-27',
    bill_type VARCHAR(32) DEFAULT 'ALL',
    budget_amount NUMERIC(14, 2) NOT NULL DEFAULT 200000.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT monthly_budgets_unique UNIQUE (toll_plaza_id, bill_month, financial_year, bill_type)
);

-- 5. CREATE DEDICATED REJECTED BUCKET TABLE
CREATE TABLE IF NOT EXISTS public.bill_rejected_bucket (
    rejection_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id VARCHAR(64),
    bill_number VARCHAR(64),
    consumer_account_no VARCHAR(64),
    toll_plaza_id VARCHAR(16),
    bill_type VARCHAR(32) DEFAULT 'LT',
    bill_month VARCHAR(32),
    amount NUMERIC(14, 2) DEFAULT 0.0,
    units NUMERIC(14, 2) DEFAULT 0.0,
    rejection_reason TEXT NOT NULL,
    rejected_by VARCHAR(128) DEFAULT 'OPERATOR',
    rejected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_filename VARCHAR(256),
    raw_payload JSONB,
    audit_notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_bill_rejected_bn ON public.bill_rejected_bucket(bill_number);
CREATE INDEX IF NOT EXISTS idx_bill_rejected_ac ON public.bill_rejected_bucket(consumer_account_no);
CREATE INDEX IF NOT EXISTS idx_bill_rejected_mo ON public.bill_rejected_bucket(bill_month);

-- 6. REBUILD public.vw_official_bill_register WITH ALL 13 FIELDS
DROP VIEW IF EXISTS public.vw_bill_kpi_summary CASCADE;
DROP VIEW IF EXISTS public.vw_budget_vs_actual CASCADE;
DROP VIEW IF EXISTS public.vw_rebate_performance CASCADE;
DROP VIEW IF EXISTS public.v_energy_bills_master CASCADE;
DROP VIEW IF EXISTS public.vw_official_bill_register CASCADE;

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
    COALESCE(
        m.toll_plaza_id, 
        b.toll_plaza_id,
        CASE 
            WHEN b.consumer_account_no LIKE '416%' OR b.consumer_account_no LIKE '411%' THEN 'TP01'
            WHEN b.consumer_account_no LIKE '413%' THEN 'TP02'
            WHEN b.consumer_account_no LIKE '812%' OR b.consumer_account_no LIKE '813%' THEN 'TP03'
            ELSE 'TP01'
        END
    ) AS toll_plaza_id,
    COALESCE(
        b.bill_type, 
        m.bill_type, 
        CASE 
            WHEN b.consumer_account_no IN ('416000000110', '813000000281', '812001020208') THEN 'HT'
            ELSE 'LT'
        END
    ) AS bill_type,
    COALESCE(
        b.consumer_scope, 
        m.consumer_scope, 
        CASE 
            WHEN b.consumer_account_no IN ('416000000110', '813000000281', '812001020208') THEN 'PLAZA'
            ELSE 'HIGHWAY'
        END
    ) AS consumer_scope,
    COALESCE(m.asset_code, '') AS asset_code,
    COALESCE(b.division, m.division_name, 'SED') AS division_name,
    COALESCE(b.tariff_category, m.usage_type, 'Public Light') AS usage_type,
    COALESCE(
        b.sanctioned_load_kw, 
        m.sanctioned_load_kw, 
        CASE 
            WHEN b.consumer_account_no IN ('416000000110', '813000000281') THEN 120.0
            WHEN b.consumer_account_no = '812001020208' THEN 100.0
            ELSE 10.0
        END
    ) AS sanctioned_load_kw,
    COALESCE(m.location, 'Corridor Lighting') AS location,
    b.bill_month,
    CASE 
        WHEN b.bill_month ILIKE '%2026%' OR b.bill_month ILIKE '%26%' THEN '2026-27'
        WHEN b.bill_month ILIKE '%2025%' OR b.bill_month ILIKE '%25%' THEN '2025-26'
        ELSE '2026-27'
    END AS financial_year,
    b.bill_period,
    b.bill_days,
    COALESCE(b.bill_basis, 'ACTUAL') AS bill_basis,
    false AS is_provisional_or_average,
    
    -- All 13 Extracted Fields
    COALESCE(
        b.contract_demand, 
        CASE 
            WHEN b.consumer_account_no IN ('416000000110', '813000000281') THEN '120 KVA'
            WHEN b.consumer_account_no = '812001020208' THEN '100 KVA'
            ELSE CONCAT(COALESCE(b.sanctioned_load_kw, m.sanctioned_load_kw, 10.0)::text, ' KW')
        END
    ) AS contract_demand,
    COALESCE(b.security_deposit, 0.0) AS security_deposit,
    COALESCE(b.md, b.md_kw, b.md_kva, 0.0) AS md,
    COALESCE(b.cuml_md_kva, 0.0) AS cuml_md_kva,
    COALESCE(b.cuml_md_kw, 0.0) AS cuml_md_kw,
    COALESCE(b.dps_rs, 0.0) AS dps_rs,
    COALESCE(b.rebate_date, '') AS rebate_date,
    COALESCE(b.meter_sl_no, '') AS meter_sl_no,
    COALESCE(b.tariff_category, m.usage_type, '') AS tariff_category,
    COALESCE(b.section, '') AS section,
    COALESCE(b.sub_division, '') AS sub_division,
    COALESCE(b.net_payable_amount_before_rbt_dt_rs, b.total_amount_payable, b.current_total, 0.0) AS net_payable_amount_before_rbt_dt_rs,
    COALESCE(b.net_payable_amount_after_rbt_dt_rs, b.net_after_rebate, 0.0) AS net_payable_amount_after_rbt_dt_rs,

    -- Slabs & Financial Breakdown
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
    b.is_edited,
    b.edited_by,
    b.edited_at,
    b.edit_notes,
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

-- 7. REBUILD DOWNSTREAM COMPATIBILITY VIEWS
CREATE VIEW public.v_energy_bills_master AS 
SELECT * FROM public.vw_official_bill_register;

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

-- 8. PERMISSIONS & CACHE RELOAD
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role, postgres;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated, service_role, postgres;
GRANT ALL ON ALL ROUTINES IN SCHEMA public TO anon, authenticated, service_role, postgres;

NOTIFY pgrst, 'reload schema';
NOTIFY pgrst, 'reload config';
