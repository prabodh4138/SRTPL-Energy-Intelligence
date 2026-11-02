-- ============================================================================
-- SRTPL POWER INTELLIGENCE — COMPANY PROFIT / LOSS & REBATE AUDIT SCHEMA UPGRADE
-- Authoritative Schema Upgrade for Supabase PostgreSQL
-- 
-- Rules:
-- 1. Payment on or before Rebate Date -> REBATE AVAILED -> COMPANY PROFIT (company_profit_rs)
-- 2. Payment after Rebate Date       -> REBATE LOSS    -> COMPANY LOSS   (company_loss_rs)
-- 3. Unpaid & current_date > rebate  -> REBATE LOSS    -> COMPANY LOSS   (company_loss_rs)
-- 4. Unpaid & current_date <= rebate -> PENDING (ELIGIBLE) -> POTENTIAL PROFIT
-- ============================================================================

-- 1. UPGRADE public.energy_bills WITH AUDIT & REBATE FINANCIAL IMPACT COLUMNS
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS prompt_rebate NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS rebate_status VARCHAR(32) DEFAULT 'PENDING (ELIGIBLE)';
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS rebate_availed NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS rebate_loss NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS company_profit_rs NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS company_loss_rs NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS financial_impact VARCHAR(32) DEFAULT 'POTENTIAL PROFIT';
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS rebate_remarks TEXT;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS meter_rent_rs NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS customer_service_charge_rs NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS net_payable_amount_before_rbt_dt_rs NUMERIC(14, 2) DEFAULT 0.0;
ALTER TABLE public.energy_bills ADD COLUMN IF NOT EXISTS net_payable_amount_after_rbt_dt_rs NUMERIC(14, 2) DEFAULT 0.0;

-- 2. UPGRADE public.payment_receipts
ALTER TABLE public.payment_receipts ADD COLUMN IF NOT EXISTS office_name VARCHAR(128) DEFAULT 'ESO RE SECTION';
ALTER TABLE public.payment_receipts ADD COLUMN IF NOT EXISTS category VARCHAR(128) DEFAULT 'PUBLIC LIGHT';
ALTER TABLE public.payment_receipts ADD COLUMN IF NOT EXISTS collections_date VARCHAR(32);
ALTER TABLE public.payment_receipts ADD COLUMN IF NOT EXISTS payment_date VARCHAR(32);

-- 3. CREATE public.receipt_allocations TABLE (IF NOT EXISTS)
CREATE TABLE IF NOT EXISTS public.receipt_allocations (
    id BIGSERIAL PRIMARY KEY,
    receipt_no VARCHAR(64) NOT NULL REFERENCES public.payment_receipts(receipt_no) ON DELETE CASCADE,
    bill_number VARCHAR(64) REFERENCES public.energy_bills(bill_number) ON DELETE SET NULL,
    allocation_amount NUMERIC(14, 2) NOT NULL DEFAULT 0.0,
    allocation_date TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. REBUILD VIEW: vw_rebate_performance
DROP VIEW IF EXISTS public.vw_rebate_performance CASCADE;

CREATE OR REPLACE VIEW public.vw_rebate_performance AS
SELECT 
    b.toll_plaza_id,
    b.bill_month,
    COUNT(b.bill_number) AS total_bills,
    COALESCE(SUM(b.prompt_rebate), 0.0) AS total_eligible_rebate_rs,
    COALESCE(SUM(b.company_profit_rs), 0.0) AS company_profit_rs,
    COALESCE(SUM(b.company_loss_rs), 0.0) AS company_loss_rs,
    COALESCE(SUM(b.rebate_availed), 0.0) AS total_rebate_availed_rs,
    COALESCE(SUM(b.rebate_loss), 0.0) AS total_rebate_loss_rs,
    CASE 
        WHEN COALESCE(SUM(b.prompt_rebate), 0.0) > 0 
        THEN ROUND((COALESCE(SUM(b.company_profit_rs), 0.0) / SUM(b.prompt_rebate)) * 100.0, 2)
        ELSE 0.0 
    END AS realization_rate_pct,
    CASE 
        WHEN COALESCE(SUM(b.company_profit_rs), 0.0) >= COALESCE(SUM(b.company_loss_rs), 0.0) THEN 'COMPANY PROFIT'
        ELSE 'COMPANY LOSS'
    END AS financial_impact
FROM public.energy_bills b
WHERE b.bill_basis = 'ACTUAL'
GROUP BY b.toll_plaza_id, b.bill_month;

-- 5. REBUILD VIEW: vw_merged_bill_receipt_reconciliation
DROP VIEW IF EXISTS public.vw_merged_bill_receipt_reconciliation CASCADE;

CREATE OR REPLACE VIEW public.vw_merged_bill_receipt_reconciliation AS
SELECT 
    b.consumer_account_no,
    b.bill_month,
    b.bill_number,
    b.toll_plaza_id,
    b.bill_type,
    b.consumer_scope,
    b.meter_sl_no,
    b.bill_issue_date,
    b.due_date,
    b.rebate_date,
    COALESCE(b.energy_charges, 0.0) AS energy_charges,
    COALESCE(b.electricity_duty, 0.0) AS electricity_duty,
    COALESCE(b.meter_rent, b.meter_rent_rs, 0.0) AS meter_rent,
    COALESCE(b.customer_service_charge, b.customer_service_charge_rs, 0.0) AS customer_service_charge,
    COALESCE(b.total_amount_payable, b.current_total, 0.0) AS total_amount_payable,
    COALESCE(b.net_payable_amount_before_rbt_dt_rs, b.net_before_rebate, b.total_amount_payable, 0.0) AS net_payable_amount_before_rbt_dt_rs,
    COALESCE(b.net_payable_amount_after_rbt_dt_rs, b.net_after_rebate, b.total_amount_payable, 0.0) AS net_payable_amount_after_rbt_dt_rs,
    COALESCE(b.prompt_rebate, 0.0) AS prompt_rebate,
    COALESCE(b.rebate_status, 'PENDING (ELIGIBLE)') AS rebate_status,
    COALESCE(b.rebate_availed, 0.0) AS rebate_availed,
    COALESCE(b.rebate_loss, 0.0) AS rebate_loss,
    COALESCE(b.company_profit_rs, 0.0) AS company_profit_rs,
    COALESCE(b.company_loss_rs, 0.0) AS company_loss_rs,
    COALESCE(b.financial_impact, 'POTENTIAL PROFIT') AS financial_impact,
    b.rebate_remarks,
    r.receipt_no,
    r.payment_type,
    COALESCE(r.collections_date, r.payment_date, '') AS collections_date,
    COALESCE(r.amount_paid, 0.0) AS amount_paid,
    COALESCE(r.office_name, 'ESO RE SECTION') AS office_name,
    COALESCE(r.category, b.tariff_category, 'PUBLIC LIGHT') AS category,
    GREATEST(0.0, COALESCE(b.total_amount_payable, 0.0) - COALESCE(r.amount_paid, 0.0)) AS outstanding_balance,
    CASE 
        WHEN COALESCE(r.amount_paid, 0.0) >= COALESCE(b.total_amount_payable, 0.0) - 1.0 AND COALESCE(r.amount_paid, 0.0) > 0 THEN 'PAID'
        WHEN COALESCE(r.amount_paid, 0.0) > 0 THEN 'PARTIAL'
        ELSE 'UNPAID'
    END AS payment_status,
    b.source_filename
FROM public.energy_bills b
LEFT JOIN public.payment_receipts r 
    ON (b.consumer_account_no = r.consumer_no OR b.consumer_account_no = r.account_no)
    AND b.bill_month = r.bill_month;

-- 6. REBUILD VIEW: vw_official_bill_register
DROP VIEW IF EXISTS public.vw_official_bill_register CASCADE;

CREATE OR REPLACE VIEW public.vw_official_bill_register AS
SELECT 
    b.bill_number,
    b.source_filename,
    b.consumer_account_no,
    b.consumer_id,
    b.old_consumer_no,
    b.bill_type,
    b.consumer_scope,
    b.sanctioned_load_kw,
    b.contract_demand,
    b.bill_month,
    b.bill_period,
    b.bill_days,
    b.bill_basis,
    b.bill_issue_date,
    b.due_date,
    b.rebate_date,
    b.meter_sl_no,
    b.meter_rent_count,
    b.security_deposit,
    b.md,
    b.md_kw,
    b.md_kva,
    b.cuml_md_kw,
    b.cuml_md_kva,
    b.tariff_category,
    b.tariff_type,
    b.division,
    b.sub_division,
    b.section,
    b.energy_charges,
    b.demand_charge,
    b.tod_incentive,
    b.tod_surcharge,
    b.electricity_charges,
    b.electricity_duty,
    COALESCE(b.meter_rent, b.meter_rent_rs, 0.0) AS meter_rent,
    COALESCE(b.customer_service_charge, b.customer_service_charge_rs, 0.0) AS customer_service_charge,
    b.dps_rs,
    b.current_total,
    b.prompt_rebate,
    b.rebate_status,
    b.rebate_availed,
    b.rebate_loss,
    b.company_profit_rs,
    b.company_loss_rs,
    b.financial_impact,
    b.rebate_remarks,
    b.total_amount_payable,
    COALESCE(b.net_payable_amount_before_rbt_dt_rs, b.net_before_rebate, b.total_amount_payable) AS net_payable_amount_before_rbt_dt_rs,
    COALESCE(b.net_payable_amount_after_rbt_dt_rs, b.net_after_rebate, b.total_amount_payable) AS net_payable_amount_after_rbt_dt_rs,
    b.verification_status,
    b.created_at
FROM public.energy_bills b
WHERE b.bill_basis = 'ACTUAL';

-- Grant access to schemas and views
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;
