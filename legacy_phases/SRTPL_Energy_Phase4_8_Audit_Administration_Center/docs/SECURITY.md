# Administration Security Baseline

1. Supabase service-role credentials stay server-side.
2. RLS must be enabled on administrative tables.
3. Browser users must not directly update audit logs.
4. Audit logs should be append-only.
5. Administrative actions require authentication and authorization.
6. Sensitive configuration values/secrets are never displayed.
7. Role changes are audited.
8. Master-data changes require reason and approval where configured.
9. Reprocessing requires explicit authorization.
10. Export activity is auditable.
11. Failed authorization attempts should be logged where feasible.
12. Session/logout events should be recorded.
