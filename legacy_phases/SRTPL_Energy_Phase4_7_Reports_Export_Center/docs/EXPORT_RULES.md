# Export Rules

1. CSV is the machine-friendly export.
2. Excel is the operational/management analysis export.
3. PDF is the controlled presentation/audit export.
4. Exported reports must not modify source data.
5. No report should invent zero values for missing data.
6. Report generation should use approved read models.
7. Report runs must be recorded in energy_audit.report_run.
8. User identity must be recorded.
9. Date/plaza/equipment filters must be recorded.
10. Report version should be recorded once report definitions become versioned.
11. Large exports should use server-side generation rather than loading unlimited rows into browser memory.
