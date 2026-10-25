# Phase 3 Implementation Checklist

## Completed in this starter
- File SHA-256 utility
- JUNO report auto-detection
- Metadata extraction boundary
- Multi-row header flattening
- NULL preservation
- Generic raw payload retention
- Record hashing
- Business-key generation
- Versioned parser boundary
- Local inspection service

## Database integration next
1. Create private Supabase Storage bucket `energy-original-files`.
2. Upload original CSV exactly as received.
3. Insert import_batch.
4. Insert import_file with SHA-256.
5. Reject exact duplicate SHA-256.
6. Parse and insert import_row.
7. Insert into source-specific energy_raw table.
8. Run source-specific validation.
9. Resolve asset_id from energy_master.asset.
10. Populate energy_readings.
11. Calculate interval values using ordered previous valid reading.
12. Calculate KPIs.
13. Create exceptions.
14. Update import counts/status.
15. Write audit_log.

## Important engineering rules
- Never overwrite the original JUNO CSV.
- Never convert NULL to zero.
- Never silently discard invalid records.
- Cumulative meter resets/replacements must be detected separately from ordinary decreases.
- KPI calculations must carry calculation_version.
- Any manual correction must create a change_request and audit event.
