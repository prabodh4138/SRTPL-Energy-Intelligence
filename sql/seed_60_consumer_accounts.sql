-- ============================================================================
-- SRTPL POWER INTELLIGENCE — ENERGY_MASTER.CONSUMER_ACCOUNT TABLE & 60 MASTER RECORDS
-- Target: Supabase / PostgreSQL SQL Editor
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS energy_master;

-- 1. Ensure energy_master.plaza exists and contains TP01, TP02, TP03 for foreign key integrity
CREATE TABLE IF NOT EXISTS energy_master.plaza (
  plaza_id character varying(16) NOT NULL,
  plaza_name character varying(128) NOT NULL,
  location character varying(256) NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT plaza_pkey PRIMARY KEY (plaza_id)
);

INSERT INTO energy_master.plaza (plaza_id, plaza_name, location) VALUES
  ('TP01', 'Toll Plaza 01 (Km 24+500)', 'Sambalpur'),
  ('TP02', 'Toll Plaza 02 (Km 68+200)', 'Jharsuguda'),
  ('TP03', 'Toll Plaza 03 (Km 112+800)', 'Sundargarh')
ON CONFLICT (plaza_id) DO UPDATE SET
  plaza_name = EXCLUDED.plaza_name,
  location = EXCLUDED.location;

-- 2. Create energy_master.consumer_account table
CREATE TABLE IF NOT EXISTS energy_master.consumer_account (
  consumer_account_no character varying(64) not null,
  toll_plaza_id character varying(16) null,
  bill_type character varying(32) not null default 'HT'::character varying,
  asset_code character varying(64) not null,
  consumer_scope character varying(64) not null default 'HIGHWAY'::character varying,
  division_name character varying(128) not null,
  usage_type character varying(128) not null default 'Street Light'::character varying,
  sanctioned_load_kw numeric(10, 2) not null default 0.0,
  location character varying(256) not null,
  is_active boolean not null default true,
  remarks text null,
  created_at timestamp with time zone not null default now(),
  updated_at timestamp with time zone not null default now(),
  constraint consumer_account_pkey primary key (consumer_account_no),
  constraint consumer_account_toll_plaza_id_fkey foreign KEY (toll_plaza_id) references energy_master.plaza (plaza_id) on delete set null
);

-- 3. Create Performance Indexes
CREATE INDEX IF NOT EXISTS idx_consumer_account_asset ON energy_master.consumer_account USING btree (asset_code);
CREATE INDEX IF NOT EXISTS idx_consumer_account_plaza ON energy_master.consumer_account USING btree (toll_plaza_id);
CREATE INDEX IF NOT EXISTS idx_consumer_account_division ON energy_master.consumer_account USING btree (division_name);
CREATE INDEX IF NOT EXISTS idx_consumer_account_bill_type ON energy_master.consumer_account USING btree (bill_type);

-- 4. Enable Row Level Security (RLS) with Full Read/Write access for API
ALTER TABLE energy_master.consumer_account ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "allow_all_consumer_account" ON energy_master.consumer_account;
CREATE POLICY "allow_all_consumer_account" ON energy_master.consumer_account FOR ALL TO anon, authenticated, service_role USING (true) WITH CHECK (true);

-- 5. Insert / Upsert 60 Authentic Master Consumer Accounts
INSERT INTO energy_master.consumer_account (
  consumer_account_no, toll_plaza_id, bill_type, asset_code, 
  consumer_scope, division_name, usage_type, sanctioned_load_kw, 
  location, is_active, remarks, created_at, updated_at
) VALUES
  ('411001070208', 'TP01', 'LT', 'SR-E-EM-EB-5-200', 'HIGHWAY', 'SED', 'Street Light', 10.0, 'Ainthapalli', true, NULL, now(), now()),
  ('413001070099', 'TP02', 'LT', 'SR-E-EM-EB-62-600', 'HIGHWAY', 'JED', 'Street Light', 18.0, 'TANGARPALI', true, NULL, now(), now()),
  ('813000000281', 'TP03', 'HT', 'SR-E-EM-EB-000TP03', 'PLAZA', 'RED', 'Toll Plaza', 120.0, 'TOLL PLAZA 03', true, NULL, now(), now()),
  ('411001070209', 'TP01', 'LT', 'SR-E-EM-EB-6-343', 'HIGHWAY', 'SED', 'Street Light', 19.0, 'Bhalupali', true, NULL, now(), now()),
  ('411734021695', 'TP01', 'LT', 'SR-E-EM-EB-09-100', 'HIGHWAY', 'SED', 'Street Light', 3.0, '9 VMS', true, NULL, now(), now()),
  ('413001070101', 'TP01', 'LT', 'SR-E-EM-EB-46-950', 'HIGHWAY', 'JED', 'Street Light', 19.0, 'BADMAL', true, NULL, now(), now()),
  ('413001070102', 'TP01', 'LT', 'SR-E-EM-EB-45-200', 'HIGHWAY', 'JED', 'Street Light', 16.0, 'SAHAPARA', true, NULL, now(), now()),
  ('413001070231', 'TP01', 'LT', 'SR-E-EM-EB-43-000', 'HIGHWAY', 'JED', 'Street Light', 5.0, 'KHERUAL', true, NULL, now(), now()),
  ('413001070344', 'TP01', 'LT', 'SR-E-EM-EB-053-100', 'HIGHWAY', 'JED', 'Street Light', 40.0, 'BTM Chowk-53 COS', true, NULL, now(), now()),
  ('413511052004', 'TP01', 'LT', 'SR-E-EM-EB-048-550', 'HIGHWAY', 'JED', 'Street Light', 3.0, '48 VMS', true, NULL, now(), now()),
  ('413526031772', 'TP01', 'LT', 'SR-E-EM-EB-45-100', 'HIGHWAY', 'JED', 'Street Light', 2.0, '45 VMS', true, NULL, now(), now()),
  ('416000000110', 'TP01', 'HT', 'SR-E-EM-EB-000TP01', 'PLAZA', 'SEED', 'Toll Plaza', 120.0, 'TOLL PLAZA 01', true, NULL, now(), now()),
  ('416001070082', 'TP01', 'LT', 'SR-E-EM-EB-13-000', 'HIGHWAY', 'SEED', 'Street Light', 20.0, 'Sason', true, NULL, now(), now()),
  ('416001070083', 'TP01', 'LT', 'SR-E-EM-EB-19-500', 'HIGHWAY', 'SEED', 'Street Light', 16.0, 'Kilasama', true, NULL, now(), now()),
  ('416001070084', 'TP01', 'LT', 'SR-E-EM-EB-40-500', 'HIGHWAY', 'SEED', 'Street Light', 16.0, 'Thelkoloi', true, NULL, now(), now()),
  ('416001070085', 'TP01', 'LT', 'SR-E-EM-EB-28-400', 'HIGHWAY', 'SEED', 'Street Light', 15.0, 'Shyam Metalic(ROB-2)', true, NULL, now(), now()),
  ('416001070086', 'TP01', 'LT', 'SR-E-EM-EB-22-300', 'HIGHWAY', 'SEED', 'Street Light', 13.0, 'New Rampella', true, NULL, now(), now()),
  ('416001070087', 'TP01', 'LT', 'SR-E-EM-EB-27-500', 'HIGHWAY', 'SEED', 'Street Light', 4.0, 'Rengali End HM', true, NULL, now(), now()),
  ('416001070089', 'TP01', 'LT', 'SR-E-EM-EB-22-550', 'HIGHWAY', 'SEED', 'Street Light', 5.0, 'Rengali Start HM', true, NULL, now(), now()),
  ('416001070090', 'TP01', 'LT', 'SR-E-EM-EB-34-950', 'HIGHWAY', 'SEED', 'Street Light', 9.0, 'Lapanga', true, NULL, now(), now()),
  ('416001111004', 'TP01', 'LT', 'SR-E-EM-EB-10-850', 'HIGHWAY', 'SEED', 'Street Light', 6.0, 'Majipalli', true, NULL, now(), now()),
  ('416335112157', 'TP01', 'LT', 'SR-E-EM-EB-31-000', 'HIGHWAY', 'SEED', 'Street Light', 2.0, '31 VMS', true, NULL, now(), now()),
  ('413001070100', 'TP02', 'LT', 'SR-E-EM-EB-61-500', 'HIGHWAY', 'JED', 'Street Light', 7.0, 'TALPATIA', true, NULL, now(), now()),
  ('812001020208', 'TP02', 'HT', 'SR-E-EM-EB-000TP02', 'PLAZA', 'SED', 'Toll Plaza', 100.0, 'TOLL PLAZA 02', true, NULL, now(), now()),
  ('812001070017', 'TP02', 'LT', 'SR-E-EM-EB-82-600', 'HIGHWAY', 'SED', 'Street Light', 29.0, 'PATRAPALI', true, NULL, now(), now()),
  ('812001070018', 'TP02', 'LT', 'SR-E-EM-EB-78-950', 'HIGHWAY', 'SED', 'Street Light', 28.0, 'BHAWANIPUR', true, NULL, now(), now()),
  ('812001070019', 'TP02', 'LT', 'SR-E-EM-EB-77-450', 'HIGHWAY', 'SED', 'Street Light', 16.0, 'KIRAI BAMRA CHOWK', true, NULL, now(), now()),
  ('812001070020', 'TP02', 'LT', 'SR-E-EM-EB-76-450', 'HIGHWAY', 'SED', 'Street Light', 16.0, 'KIRAI', true, NULL, now(), now()),
  ('812001070021', 'TP02', 'LT', 'SR-E-EM-EB-74-500', 'HIGHWAY', 'SED', 'Street Light', 18.0, 'BHEDABAHAL', true, NULL, now(), now()),
  ('812001070022', 'TP02', 'LT', 'SR-E-EM-EB-75-450', 'HIGHWAY', 'SED', 'Street Light', 15.0, 'KANDABAHAL', true, NULL, now(), now()),
  ('812001070023', 'TP02', 'LT', 'SR-E-EM-EB-70-650', 'HIGHWAY', 'SED', 'Street Light', 8.0, 'BHADBAHAL', true, NULL, now(), now()),
  ('812001070024', 'TP02', 'LT', 'SR-E-EM-EB-72-000', 'HIGHWAY', 'SED', 'Street Light', 17.0, 'MASNIKANI', true, NULL, now(), now()),
  ('812001070025', 'TP02', 'LT', 'SR-E-EM-EB-63-350', 'HIGHWAY', 'SED', 'Street Light', 20.0, 'BHASMA', true, NULL, now(), now()),
  ('812001070026', 'TP02', 'LT', 'SR-E-EM-EB-89-950', 'HIGHWAY', 'SED', 'Street Light', 26.0, 'KARAMDIH', true, NULL, now(), now()),
  ('812001070027', 'TP02', 'LT', 'SR-E-EM-EB-84-000', 'HIGHWAY', 'SED', 'Street Light', 5.0, 'BHOJPUR', true, NULL, now(), now()),
  ('812121032098', 'TP02', 'LT', 'SR-E-EM-EB-78-430', 'HIGHWAY', 'SED', 'Street Light', 3.0, '78 VMS', true, NULL, now(), now()),
  ('812124041064', 'TP02', 'LT', 'SR-E-EM-EB-69-350', 'HIGHWAY', 'SED', 'Street Light', 3.0, '69 VMS', true, NULL, now(), now()),
  ('813001070048', 'TP02', 'LT', 'SR-E-EM-EB-104-200', 'HIGHWAY', 'RED', 'Street Light', 16.0, 'ITMA', true, NULL, now(), now()),
  ('813001070049', 'TP02', 'LT', 'SR-E-EM-EB-112-750', 'HIGHWAY', 'RED', 'Street Light', 13.0, 'BARGAON', true, NULL, now(), now()),
  ('813001070051', 'TP02', 'LT', 'SR-E-EM-EB-107-125', 'HIGHWAY', 'RED', 'Street Light', 17.0, 'TIKLIPARA', true, NULL, now(), now()),
  ('813001070052', 'TP02', 'LT', 'SR-E-EM-EB-111-850', 'HIGHWAY', 'RED', 'Street Light', 16.0, 'LATAGAON', true, NULL, now(), now()),
  ('813001070059', 'TP02', 'LT', 'SR-E-EM-EB-110-750', 'HIGHWAY', 'RED', 'Street Light', 23.0, 'BHOIPALLI', true, NULL, now(), now()),
  ('813001070060', 'TP02', 'LT', 'SR-E-EM-EB-98-450', 'HIGHWAY', 'RED', 'Street Light', 22.0, 'JARONGLOAI', true, NULL, now(), now()),
  ('813001070061', 'TP02', 'LT', 'SR-E-EM-EB-97-900', 'HIGHWAY', 'RED', 'Street Light', 7.0, 'JHARMUNDA', true, NULL, now(), now()),
  ('813001070063', 'TP02', 'LT', 'SR-E-EM-EB-108-800', 'HIGHWAY', 'RED', 'Street Light', 4.0, 'GARIAMAL', true, NULL, now(), now()),
  ('813413021313', 'TP02', 'LT', 'SR-E-EM-EB-112-215', 'HIGHWAY', 'RED', 'Street Light', 1.0, 'BADGAON SUBWAY', true, NULL, now(), now()),
  ('813413052467', 'TP02', 'LT', 'SR-E-EM-EB-99-000', 'HIGHWAY', 'RED', 'Street Light', 2.0, '98 VMS', true, NULL, now(), now()),
  ('813001070050', 'TP03', 'LT', 'SR-E-EM-EB-113-800', 'HIGHWAY', 'RED', 'Street Light', 23.0, 'KANTAMURA', true, NULL, now(), now()),
  ('813001070064', 'TP03', 'LT', 'SR-E-EM-EB-128-750', 'HIGHWAY', 'RED', 'Street Light', 7.0, 'KUTRA TLB', true, NULL, now(), now()),
  ('813001070057', 'TP03', 'LT', 'SR-E-EM-EB-130-000', 'HIGHWAY', 'RED', 'Street Light', 18.0, 'KUTRA', true, NULL, now(), now()),
  ('813414012506', 'TP03', 'LT', 'SR-E-EM-EB-128-000', 'HIGHWAY', 'RED', 'Street Light', 3.0, '128 VMS', true, NULL, now(), now()),
  ('813001070058', 'TP03', 'LT', 'SR-E-EM-EB-136-700', 'HIGHWAY', 'RED', 'Street Light', 14.0, 'JHAREBEDA', true, NULL, now(), now()),
  ('813001070045', 'TP03', 'LT', 'SR-E-EM-EB-144-500', 'HIGHWAY', 'RED', 'Street Light', 6.0, 'RANIBANDA', true, NULL, now(), now()),
  ('813001070047', 'TP03', 'LT', 'SR-E-EM-EB-144-950', 'HIGHWAY', 'RED', 'Street Light', 26.0, 'RANIBANDH', true, NULL, now(), now()),
  ('813001070053', 'TP03', 'LT', 'SR-E-EM-EB-152-650', 'HIGHWAY', 'RED', 'Street Light', 16.0, 'LAING', true, NULL, now(), now()),
  ('813001070054', 'TP03', 'LT', 'SR-E-EM-EB-154-150', 'HIGHWAY', 'RED', 'Street Light', 21.0, 'DHELUA', true, NULL, now(), now()),
  ('813001070055', 'TP03', 'LT', 'SR-E-EM-EB-157-600', 'HIGHWAY', 'RED', 'Street Light', 26.0, 'CHUNGIMATI', true, NULL, now(), now()),
  ('813001070046', 'TP03', 'LT', 'SR-E-EM-EB-159-200', 'HIGHWAY', 'RED', 'Street Light', 6.0, 'MANDIAKUDAR I', true, NULL, now(), now()),
  ('813001070056', 'TP03', 'LT', 'SR-E-EM-EB-160-000', 'HIGHWAY', 'RED', 'Street Light', 18.0, 'MANDIAKUDAR II', true, NULL, now(), now()),
  ('813001070065', 'TP03', 'LT', 'SR-E-EM-EB-166-170', 'HIGHWAY', 'RED', 'Street Light', 19.0, 'VEDVYAS', true, NULL, now(), now())
ON CONFLICT (consumer_account_no) DO UPDATE SET
  toll_plaza_id = EXCLUDED.toll_plaza_id,
  bill_type = EXCLUDED.bill_type,
  asset_code = EXCLUDED.asset_code,
  consumer_scope = EXCLUDED.consumer_scope,
  division_name = EXCLUDED.division_name,
  usage_type = EXCLUDED.usage_type,
  sanctioned_load_kw = EXCLUDED.sanctioned_load_kw,
  location = EXCLUDED.location,
  is_active = EXCLUDED.is_active,
  updated_at = now();

-- 6. Reload PostgREST schema cache
NOTIFY pgrst, 'reload schema';

-- 7. Verification Query (Expected count: 60)
SELECT 
  'energy_master.consumer_account' AS table_name,
  bill_type,
  consumer_scope,
  COUNT(*) AS total_accounts
FROM energy_master.consumer_account
GROUP BY bill_type, consumer_scope
ORDER BY bill_type, consumer_scope;
