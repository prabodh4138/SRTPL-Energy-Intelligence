create schema if not exists energy_master;

create table if not exists energy_master.config_version (
    config_version_id uuid primary key default gen_random_uuid(),
    domain text not null,
    entity_id text not null,
    version_no integer not null,
    effective_from date not null,
    effective_to date null,
    active boolean not null default true,
    created_by uuid null,
    created_at timestamptz not null default now(),
    unique(domain, entity_id, version_no)
);

create table if not exists energy_master.source_mapping (
    mapping_id uuid primary key default gen_random_uuid(),
    report_type text not null,
    source_column text not null,
    target_parameter_id uuid null,
    transform_code text null,
    required boolean not null default false,
    active boolean not null default true,
    config_version_id uuid null,
    unique(report_type, source_column, config_version_id)
);

create table if not exists energy_master.report_schedule (
    schedule_id uuid primary key default gen_random_uuid(),
    report_code text not null,
    frequency text not null,
    recipient_scope text not null,
    active boolean not null default true,
    last_run_at timestamptz null,
    next_run_at timestamptz null,
    config_version_id uuid null
);

create index if not exists idx_config_version_domain
on energy_master.config_version(domain, entity_id, version_no desc);

create index if not exists idx_source_mapping_type
on energy_master.source_mapping(report_type, active);

create index if not exists idx_report_schedule_next
on energy_master.report_schedule(active, next_run_at);
