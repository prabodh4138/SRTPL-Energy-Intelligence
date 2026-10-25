-- ============================================================================
-- SRTPL POWER INTELLIGENCE — PROVISIONAL & AVERAGE BILLS AUDIT TABLE
-- Target Project: Supabase (public.energy_bills_provisional)
-- 
-- Stores non-actual (AVERAGE / PROVISIONAL / ESTIMATED / DEFECTIVE) bills
-- completely isolated from actual energy bills and KPIs.
-- Allows audit tracking, meter interval review, and duplicate detection hints.
-- ============================================================================

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

-- Ensure all audit columns exist if table was already created
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

-- Disable Row Level Security or grant open access for application operation
ALTER TABLE public.energy_bills_provisional DISABLE ROW LEVEL SECURITY;

GRANT ALL ON public.energy_bills_provisional TO anon, authenticated, service_role, postgres;

NOTIFY pgrst, 'reload config';
NOTIFY pgrst, 'reload schema';
