-- ============================================================================
-- SRTPL POWER INTELLIGENCE — INSTANT SCHEMA UPGRADE FOR PUBLIC.ENERGY_BILLS
-- Run this in your Supabase SQL Editor to ensure all 19 extended & audit columns
-- exist and reload the PostgREST schema cache immediately.
-- ============================================================================

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

-- Reload Supabase Schema Cache
NOTIFY pgrst, 'reload schema';
NOTIFY pgrst, 'reload config';
