-- Production checklist queries.
-- These are intentionally read-only checks.

-- Verify RLS is enabled for sensitive schemas.
select
    schemaname,
    tablename,
    rowsecurity
from pg_tables
where schemaname in (
    'energy_master',
    'energy_import',
    'energy_validation',
    'energy_analytics',
    'energy_audit',
    'energy_admin'
)
order by schemaname, tablename;

-- Review policies before production deployment.
select
    schemaname,
    tablename,
    policyname,
    cmd
from pg_policies
where schemaname in (
    'energy_master',
    'energy_import',
    'energy_validation',
    'energy_analytics',
    'energy_audit',
    'energy_admin'
)
order by schemaname, tablename, policyname;
