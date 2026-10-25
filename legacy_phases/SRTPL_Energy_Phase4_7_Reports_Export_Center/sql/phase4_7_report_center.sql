create schema if not exists energy_audit;

create table if not exists energy_audit.report_run (
    report_id uuid primary key default gen_random_uuid(),
    report_code text not null,
    date_from date not null,
    date_to date not null,
    plaza_id uuid null,
    source_type text null,
    asset_id uuid null,
    output_format text not null,
    requested_by uuid null,
    requested_at timestamptz not null default now(),
    row_count integer not null default 0,
    status text not null,
    file_name text null
);

create index if not exists idx_report_run_requested_at
on energy_audit.report_run(requested_at desc);

create index if not exists idx_report_run_code
on energy_audit.report_run(report_code);

create index if not exists idx_report_run_user
on energy_audit.report_run(requested_by);

-- Recommended: expose only approved dashboard/read models to reporting.
-- Do not expose arbitrary SQL execution to Streamlit/browser users.
