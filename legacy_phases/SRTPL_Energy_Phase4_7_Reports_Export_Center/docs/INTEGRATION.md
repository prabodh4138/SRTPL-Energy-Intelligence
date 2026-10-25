# Phase 4.7 Integration

Pipeline:

JUNO → Import → Validation → Normalization → KPI → Read Models → Reports

Integrate report sources with:
- Phase 3.3 KPI results
- Phase 4.1 Executive Dashboard views
- Phase 4.2 Plaza views
- Phase 4.3 Equipment views
- Phase 4.5 Exception Center
- Phase 4.6 Data Quality views

Security:
- Browser users must not receive Supabase service-role credentials.
- Report queries should be RLS-safe.
- Prefer server-side/read-model queries.
- Report history should be auditable.

TPWODL Bill remains a future report source and must be added through a new catalog entry rather than redesigning the reporting engine.
