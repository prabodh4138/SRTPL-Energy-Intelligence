-- SRTPL POWER ANALYTICS - PHASE 2
-- Supabase PostgreSQL foundation
-- Original JUNO files are preserved in Supabase Storage.
-- This SQL creates the database structures only.

create extension if not exists pgcrypto;

create schema if not exists energy;
create schema if not exists energy_master;
create schema if not exists energy_import;
create schema if not exists energy_raw;
create schema if not exists energy_readings;
create schema if not exists energy_validation;
create schema if not exists energy_analytics;
create schema if not exists energy_audit;

-- =========================================================
-- MASTER DATA
-- =========================================================

create table if not exists energy_master.plaza (
    plaza_id uuid primary key default gen_random_uuid(),
    plaza_code text not null unique,
    plaza_name text not null,
    location text,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists energy_master.asset (
    asset_id uuid primary key default gen_random_uuid(),
    asset_code text not null unique,
    asset_name text,
    asset_type text not null,
    plaza_id uuid references energy_master.plaza(plaza_id),
    parent_asset_id uuid references energy_master.asset(asset_id),
    manufacturer text,
    model text,
    serial_number text,
    capacity numeric(14,3),
    capacity_unit text,
    commissioned_on date,
    decommissioned_on date,
    active boolean not null default true,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_asset_type on energy_master.asset(asset_type);
create index if not exists idx_asset_plaza on energy_master.asset(plaza_id);

create table if not exists energy_master.meter (
    meter_id uuid primary key default gen_random_uuid(),
    meter_code text not null unique,
    meter_name text,
    meter_type text not null,
    asset_id uuid references energy_master.asset(asset_id),
    meter_number text,
    unit text,
    multiplier numeric(18,6) not null default 1,
    ct_ratio numeric(18,6),
    pt_ratio numeric(18,6),
    installed_on date,
    removed_on date,
    active boolean not null default true,
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists energy_master.parameter (
    parameter_id uuid primary key default gen_random_uuid(),
    parameter_code text not null unique,
    parameter_name text not null,
    category text not null,
    unit text,
    data_type text not null default 'numeric',
    description text,
    source_parameter_name text,
    active boolean not null default true,
    created_at timestamptz not null default now()
);

create table if not exists energy_master.threshold (
    threshold_id uuid primary key default gen_random_uuid(),
    asset_type text,
    asset_id uuid references energy_master.asset(asset_id),
    parameter_code text not null,
    warning_min numeric,
    warning_max numeric,
    critical_min numeric,
    critical_max numeric,
    missing_interval_minutes integer,
    effective_from date,
    effective_to date,
    active boolean not null default true,
    remarks text,
    created_at timestamptz not null default now()
);

create index if not exists idx_threshold_parameter
    on energy_master.threshold(parameter_code);

create table if not exists energy_master.tariff (
    tariff_id uuid primary key default gen_random_uuid(),
    tariff_code text not null unique,
    tariff_name text not null,
    provider text,
    effective_from date not null,
    effective_to date,
    energy_rate numeric(14,6),
    demand_rate numeric(14,6),
    fixed_charge numeric(14,6),
    fuel_adjustment numeric(14,6),
    tax_rate numeric(10,6),
    metadata jsonb not null default '{}'::jsonb,
    active boolean not null default true,
    created_at timestamptz not null default now()
);

-- =========================================================
-- IMPORT CONTROL
-- =========================================================

create table if not exists energy_import.import_batch (
    batch_id uuid primary key default gen_random_uuid(),
    source_system text not null default 'JUNO',
    report_type text not null,
    original_file_name text not null,
    file_hash_sha256 text not null unique,
    storage_bucket text,
    storage_path text,
    uploaded_by text,
    uploaded_at timestamptz not null default now(),
    processing_started_at timestamptz,
    processing_completed_at timestamptz,
    total_rows integer not null default 0,
    new_rows integer not null default 0,
    duplicate_rows integer not null default 0,
    invalid_rows integer not null default 0,
    warning_rows integer not null default 0,
    status text not null default 'UPLOADED',
    error_message text,
    parser_version text,
    metadata jsonb not null default '{}'::jsonb,
    constraint chk_import_status check (
        status in ('UPLOADED','PROCESSING','PARTIAL','SUCCESS','FAILED','REJECTED')
    )
);

create index if not exists idx_import_batch_type_date
    on energy_import.import_batch(report_type, uploaded_at desc);

create table if not exists energy_import.import_row (
    import_row_id uuid primary key default gen_random_uuid(),
    batch_id uuid not null references energy_import.import_batch(batch_id) on delete cascade,
    source_row_number integer,
    source_text text,
    normalized_payload jsonb,
    row_hash_sha256 text,
    processing_status text not null default 'PENDING',
    duplicate_of uuid,
    validation_status text,
    error_message text,
    created_at timestamptz not null default now(),
    constraint chk_import_row_status check (
        processing_status in ('PENDING','PROCESSED','DUPLICATE','INVALID','WARNING','SKIPPED')
    )
);

create index if not exists idx_import_row_batch
    on energy_import.import_row(batch_id);

create index if not exists idx_import_row_hash
    on energy_import.import_row(row_hash_sha256);

-- =========================================================
-- RAW JUNO DATA
-- Original source values are preserved here.
-- =========================================================

create table if not exists energy_raw.juno_solar (
    raw_id uuid primary key default gen_random_uuid(),
    batch_id uuid not null references energy_import.import_batch(batch_id),
    import_row_id uuid references energy_import.import_row(import_row_id),
    solar_plant_id text,
    source_date_text text,
    source_generation_text text,
    source_remarks text,
    source_created_by text,
    source_created_on_text text,
    report_metadata jsonb not null default '{}'::jsonb,
    raw_payload jsonb not null,
    source_row_number integer,
    created_at timestamptz not null default now()
);

create index if not exists idx_raw_solar_plant_date
    on energy_raw.juno_solar(solar_plant_id, source_date_text);

create table if not exists energy_raw.juno_dg (
    raw_id uuid primary key default gen_random_uuid(),
    batch_id uuid not null references energy_import.import_batch(batch_id),
    import_row_id uuid references energy_import.import_row(import_row_id),
    generator_id text,
    source_date_text text,
    source_time_text text,
    source_status text,
    source_kva_text text,
    source_kw_text text,
    source_voltage_ry_text text,
    source_voltage_yb_text text,
    source_voltage_br_text text,
    source_current_r_text text,
    source_current_y_text text,
    source_current_b_text text,
    source_pf_text text,
    source_diesel_level_text text,
    source_diesel_topup_text text,
    source_load_text text,
    source_kwh_text text,
    source_running_hours_text text,
    source_rpm_text text,
    source_remarks text,
    source_created_by text,
    source_created_on_text text,
    report_metadata jsonb not null default '{}'::jsonb,
    raw_payload jsonb not null,
    source_row_number integer,
    created_at timestamptz not null default now()
);

create index if not exists idx_raw_dg_generator_date
    on energy_raw.juno_dg(generator_id, source_date_text, source_time_text);

-- =========================================================
-- NORMALIZED READINGS
-- =========================================================

create table if not exists energy_readings.solar (
    reading_id uuid primary key default gen_random_uuid(),
    asset_id uuid references energy_master.asset(asset_id),
    solar_plant_code text not null,
    reading_at timestamptz not null,
    cumulative_kwh numeric(18,3) not null,
    remarks text,
    juno_created_by text,
    juno_created_at timestamptz,
    batch_id uuid not null references energy_import.import_batch(batch_id),
    raw_id uuid references energy_raw.juno_solar(raw_id),
    source_file_name text,
    source_row_number integer,
    source_type text not null default 'JUNO_IMPORT',
    validation_status text not null default 'PENDING',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create unique index if not exists uq_solar_asset_time
    on energy_readings.solar(solar_plant_code, reading_at);

create index if not exists idx_solar_reading_time
    on energy_readings.solar(reading_at desc);

create table if not exists energy_readings.dg (
    reading_id uuid primary key default gen_random_uuid(),
    asset_id uuid references energy_master.asset(asset_id),
    generator_code text not null,
    reading_at timestamptz not null,
    status text,
    kva numeric(18,3),
    kw numeric(18,3),
    voltage_ry numeric(12,3),
    voltage_yb numeric(12,3),
    voltage_br numeric(12,3),
    current_r numeric(12,3),
    current_y numeric(12,3),
    current_b numeric(12,3),
    power_factor numeric(8,5),
    diesel_level numeric(18,3),
    diesel_topup numeric(18,3),
    load_percent numeric(10,3),
    cumulative_kwh numeric(18,3),
    running_hours numeric(18,3),
    rpm numeric(12,3),
    remarks text,
    juno_created_by text,
    juno_created_at timestamptz,
    batch_id uuid not null references energy_import.import_batch(batch_id),
    raw_id uuid references energy_raw.juno_dg(raw_id),
    source_file_name text,
    source_row_number integer,
    source_type text not null default 'JUNO_IMPORT',
    validation_status text not null default 'PENDING',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create unique index if not exists uq_dg_generator_time
    on energy_readings.dg(generator_code, reading_at);

create index if not exists idx_dg_reading_time
    on energy_readings.dg(reading_at desc);

-- Future source tables are intentionally prepared by the architecture:
-- energy_readings.eb
-- energy_readings.ups
-- energy_readings.power_panel
-- billing.tpwodl_bill

create schema if not exists energy_billing;

create table if not exists energy_billing.tpwodl_bill (
    bill_id uuid primary key default gen_random_uuid(),
    plaza_id uuid references energy_master.plaza(plaza_id),
    consumer_number text,
    bill_number text,
    billing_from date,
    billing_to date,
    bill_date date,
    previous_reading numeric(18,3),
    current_reading numeric(18,3),
    billed_units numeric(18,3),
    maximum_demand numeric(18,3),
    power_factor numeric(8,5),
    energy_charges numeric(18,2),
    demand_charges numeric(18,2),
    fixed_charges numeric(18,2),
    fuel_adjustment numeric(18,2),
    electricity_duty numeric(18,2),
    tax_amount numeric(18,2),
    other_charges numeric(18,2),
    arrears numeric(18,2),
    adjustments numeric(18,2),
    total_bill numeric(18,2),
    due_date date,
    paid_amount numeric(18,2),
    payment_date date,
    source_file_name text,
    batch_id uuid references energy_import.import_batch(batch_id),
    raw_payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- =========================================================
-- VALIDATION / EXCEPTIONS
-- =========================================================

create table if not exists energy_validation.rule (
    rule_id uuid primary key default gen_random_uuid(),
    rule_code text not null unique,
    rule_name text not null,
    source_type text,
    parameter_code text,
    severity text not null default 'WARNING',
    rule_expression text,
    description text,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    constraint chk_rule_severity check (
        severity in ('INFO','WARNING','ERROR','CRITICAL')
    )
);

create table if not exists energy_validation.exception (
    exception_id uuid primary key default gen_random_uuid(),
    rule_id uuid references energy_validation.rule(rule_id),
    batch_id uuid references energy_import.import_batch(batch_id),
    reading_id uuid,
    source_type text,
    asset_code text,
    parameter_code text,
    observed_value text,
    expected_value text,
    deviation numeric(18,6),
    severity text not null,
    status text not null default 'OPEN',
    message text not null,
    source_file_name text,
    source_row_number integer,
    detected_at timestamptz not null default now(),
    acknowledged_by text,
    acknowledged_at timestamptz,
    resolution_note text,
    resolved_by text,
    resolved_at timestamptz,
    metadata jsonb not null default '{}'::jsonb,
    constraint chk_exception_severity check (
        severity in ('INFO','WARNING','ERROR','CRITICAL')
    ),
    constraint chk_exception_status check (
        status in ('OPEN','ACKNOWLEDGED','UNDER_REVIEW','RESOLVED','ACCEPTED_EXCEPTION')
    )
);

create index if not exists idx_exception_status
    on energy_validation.exception(status, severity, detected_at desc);

-- =========================================================
-- KPI MASTER + RESULTS
-- =========================================================

create table if not exists energy_analytics.kpi_master (
    kpi_id uuid primary key default gen_random_uuid(),
    kpi_code text not null unique,
    kpi_name text not null,
    category text not null,
    source_type text,
    unit text,
    formula_definition text not null,
    description text,
    frequency text not null default 'DAILY',
    active boolean not null default true,
    created_at timestamptz not null default now()
);

create table if not exists energy_analytics.kpi_result (
    result_id uuid primary key default gen_random_uuid(),
    kpi_id uuid not null references energy_analytics.kpi_master(kpi_id),
    plaza_id uuid references energy_master.plaza(plaza_id),
    asset_id uuid references energy_master.asset(asset_id),
    period_start timestamptz not null,
    period_end timestamptz not null,
    value_numeric numeric(22,6),
    value_text text,
    unit text,
    data_quality_status text default 'VALID',
    source_record_count integer default 0,
    calculation_version text,
    calculated_at timestamptz not null default now(),
    metadata jsonb not null default '{}'::jsonb
);

create index if not exists idx_kpi_result_lookup
    on energy_analytics.kpi_result(kpi_id, period_start desc);

-- =========================================================
-- AUDIT
-- =========================================================

create table if not exists energy_audit.audit_log (
    audit_id uuid primary key default gen_random_uuid(),
    event_time timestamptz not null default now(),
    user_id text,
    user_name text,
    action_type text not null,
    entity_schema text,
    entity_table text,
    entity_id uuid,
    source_type text,
    source_file_name text,
    old_values jsonb,
    new_values jsonb,
    reason text,
    ip_address inet,
    metadata jsonb not null default '{}'::jsonb
);

create index if not exists idx_audit_entity
    on energy_audit.audit_log(entity_schema, entity_table, entity_id, event_time desc);

create index if not exists idx_audit_time
    on energy_audit.audit_log(event_time desc);

-- =========================================================
-- DATA CORRECTIONS / APPROVAL
-- =========================================================

create table if not exists energy_audit.change_request (
    change_request_id uuid primary key default gen_random_uuid(),
    entity_schema text not null,
    entity_table text not null,
    entity_id uuid not null,
    requested_by text not null,
    requested_at timestamptz not null default now(),
    reason text not null,
    old_values jsonb,
    proposed_values jsonb,
    status text not null default 'PENDING',
    reviewed_by text,
    reviewed_at timestamptz,
    review_note text,
    constraint chk_change_status check (
        status in ('PENDING','APPROVED','REJECTED','CANCELLED')
    )
);

-- =========================================================
-- INITIAL KPI DEFINITIONS
-- =========================================================

insert into energy_analytics.kpi_master
(kpi_code, kpi_name, category, source_type, unit, formula_definition, description, frequency)
values
('SOL-GEN-D', 'Solar Daily Generation', 'SOLAR', 'SOLAR', 'kWh',
 'Current cumulative solar kWh minus previous valid cumulative solar kWh',
 'Daily solar energy generation derived from cumulative meter readings',
 'DAILY'),

('SOL-GEN-M', 'Solar Monthly Generation', 'SOLAR', 'SOLAR', 'kWh',
 'Sum of valid daily solar generation for the month',
 'Monthly solar energy generation',
 'MONTHLY'),

('DG-GEN-D', 'DG Daily Generation', 'DG', 'DG', 'kWh',
 'Current cumulative DG kWh minus previous valid cumulative DG kWh',
 'Daily DG generation derived from cumulative KWH',
 'DAILY'),

('DG-RUN-D', 'DG Daily Runtime', 'DG', 'DG', 'hour',
 'Current running hours minus previous valid running hours',
 'Daily DG operating duration',
 'DAILY'),

('DG-KWH-H', 'DG Generation per Running Hour', 'DG', 'DG', 'kWh/hour',
 'DG generation divided by valid runtime',
 'DG generation intensity',
 'DAILY'),

('DG-L-KWH', 'DG Fuel Consumption per kWh', 'DG', 'DG', 'L/kWh',
 'Validated diesel consumption divided by DG generation',
 'DG fuel efficiency',
 'DAILY'),

('DG-KWH-L', 'DG kWh per Litre', 'DG', 'DG', 'kWh/L',
 'DG generation divided by validated diesel consumption',
 'DG energy efficiency',
 'DAILY'),

('DG-PF', 'DG Average Power Factor', 'ELECTRICAL', 'DG', 'ratio',
 'Average of valid DG power factor readings',
 'Average DG power factor',
 'DAILY'),

('DG-VI', 'DG Voltage Imbalance', 'ELECTRICAL', 'DG', '%',
 'Maximum phase voltage deviation from average divided by average voltage times 100',
 'DG voltage imbalance indicator',
 'DAILY'),

('DG-CI', 'DG Current Imbalance', 'ELECTRICAL', 'DG', '%',
 'Maximum phase current deviation from average divided by average current times 100',
 'DG current imbalance indicator',
 'DAILY'),

('DATA-COMP', 'Data Completeness', 'DATA_QUALITY', NULL, '%',
 'Valid received records divided by expected records times 100',
 'Completeness of expected operational readings',
 'DAILY'),

('DATA-VALID', 'Data Validity', 'DATA_QUALITY', NULL, '%',
 'Valid records divided by total received records times 100',
 'Percentage of imported records passing validation',
 'DAILY')

on conflict (kpi_code) do nothing;
