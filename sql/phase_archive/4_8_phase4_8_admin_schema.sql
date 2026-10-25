create schema if not exists energy_admin;
create schema if not exists energy_audit;

create table if not exists energy_admin.role_master (
    role_code text primary key,
    role_name text not null,
    active boolean not null default true
);

create table if not exists energy_admin.user_role (
    user_role_id uuid primary key default gen_random_uuid(),
    user_id uuid not null,
    role_code text not null references energy_admin.role_master(role_code),
    plaza_id uuid null,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    unique(user_id, role_code, plaza_id)
);

create table if not exists energy_admin.change_request (
    request_id uuid primary key default gen_random_uuid(),
    entity_type text not null,
    entity_id text not null,
    change_type text not null,
    old_value jsonb,
    proposed_value jsonb,
    reason text not null,
    requested_by uuid not null,
    requested_at timestamptz not null default now(),
    status text not null default 'PENDING',
    approved_by uuid null,
    approved_at timestamptz null,
    applied_at timestamptz null
);

create table if not exists energy_admin.reprocess_job (
    job_id uuid primary key default gen_random_uuid(),
    batch_id uuid not null,
    requested_by uuid not null,
    requested_at timestamptz not null default now(),
    status text not null default 'REQUESTED',
    approved_by uuid null,
    started_at timestamptz null,
    completed_at timestamptz null,
    result_message text null
);

create index if not exists idx_change_request_status
on energy_admin.change_request(status, requested_at desc);

create index if not exists idx_reprocess_status
on energy_admin.reprocess_job(status, requested_at desc);
