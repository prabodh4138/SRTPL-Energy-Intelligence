-- RLS baseline design.
-- Exact policies must be aligned with the deployed authentication model.

alter table energy_admin.user_role enable row level security;
alter table energy_admin.change_request enable row level security;
alter table energy_admin.reprocess_job enable row level security;
alter table energy_audit.audit_log enable row level security;

-- Recommended policy model:
-- VIEWER/AUDITOR: read approved audit/report data only.
-- OPERATOR: import and operational actions within permitted scope.
-- PLAZA_MANAGER: own plaza scope.
-- ENERGY_MANAGER: energy operational scope.
-- ADMIN: administration except security-critical ownership changes.
-- SUPER_ADMIN: full application administration.
--
-- Do not implement "allow all authenticated users" as the final policy.
