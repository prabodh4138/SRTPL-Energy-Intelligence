-- ============================================================================
-- SRTPL POWER INTELLIGENCE — BILL REJECTED BUCKET DDL & POLICIES
-- Target: Supabase / PostgreSQL SQL Editor
-- Stores rejected bills, duplicate files, and audit-rejected records
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.bill_rejected_bucket (
    rejection_id VARCHAR(64) PRIMARY KEY,
    candidate_id VARCHAR(64),
    bill_number VARCHAR(64),
    consumer_account_no VARCHAR(64),
    toll_plaza_id VARCHAR(16),
    bill_month VARCHAR(32),
    amount NUMERIC(14, 2) DEFAULT 0.0,
    source_filename VARCHAR(256),
    rejection_reason TEXT,
    rejection_notes TEXT,
    rejected_by VARCHAR(128) DEFAULT 'Operator',
    rejected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_payload JSONB,
    status VARCHAR(32) DEFAULT 'REJECTED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_rejected_bucket_bill_no ON public.bill_rejected_bucket (bill_number);
CREATE INDEX IF NOT EXISTS idx_rejected_bucket_consumer ON public.bill_rejected_bucket (consumer_account_no);
CREATE INDEX IF NOT EXISTS idx_rejected_bucket_month ON public.bill_rejected_bucket (bill_month);

-- Row Level Security (RLS) Policy
ALTER TABLE public.bill_rejected_bucket ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "allow_all_rejected_bucket" ON public.bill_rejected_bucket;
CREATE POLICY "allow_all_rejected_bucket" ON public.bill_rejected_bucket FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

-- Reload PostgREST schema cache
NOTIFY pgrst, 'reload schema';

-- Verification Query
SELECT 'public.bill_rejected_bucket' AS table_name, COUNT(*) AS total_rejected_records FROM public.bill_rejected_bucket;
