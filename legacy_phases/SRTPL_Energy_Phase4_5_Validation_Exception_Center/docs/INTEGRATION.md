# Phase 4.5 Integration

Integrate after Phase 4.4 and before/alongside KPI dashboards.

1. Phase 3.2 validators create validation findings.
2. Map each finding to energy_validation.rule_master.
3. Insert one exception record per rule violation.
4. Preserve source/import-row references.
5. Phase 4.5 displays exceptions.
6. Resolution/acceptance must go through a protected RPC.
7. Every status change creates an energy_audit.audit_log entry.
8. KPI engine reads validation eligibility rather than raw source tables.
9. Dashboard exception counts come from the same read model.

No demo/fake production values should be introduced.
