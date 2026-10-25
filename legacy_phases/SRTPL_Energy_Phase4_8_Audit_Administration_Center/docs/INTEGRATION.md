# Phase 4.8 Integration

Phase 4.8 sits across the entire application.

It governs:
- Phase 4.4 JUNO imports
- Phase 4.5 exception actions
- Phase 4.6 configuration/thresholds
- Phase 4.7 report generation
- Phase 3 master data
- Phase 3.3 KPI/versioning

Recommended architecture:
Browser → Streamlit server → protected service/RPC → PostgreSQL/RLS

Never:
Browser → service-role key → unrestricted database

All important administrative actions should produce energy_audit.audit_log entries.
