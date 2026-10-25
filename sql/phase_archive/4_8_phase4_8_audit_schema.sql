create table if not exists energy_audit.audit_log (
    audit_id uuid primary key default gen_random_uuid(),
    actor_user_id uuid null,
    action text not null,
    entity_type text null,
    entity_id text null,
    old_value jsonb null,
    new_value jsonb null,
    reason text null,
    request_id uuid null,
    ip_address inet null,
    user_agent text null,
    created_at timestamptz not null default now()
);

create index if not exists idx_audit_created_at
on energy_audit.audit_log(created_at desc);

create index if not exists idx_audit_actor
on energy_audit.audit_log(actor_user_id, created_at desc);

create index if not exists idx_audit_entity
on energy_audit.audit_log(entity_type, entity_id, created_at desc);

-- Audit records should be append-only in production.
-- Browser users must not receive direct INSERT/UPDATE/DELETE rights.
