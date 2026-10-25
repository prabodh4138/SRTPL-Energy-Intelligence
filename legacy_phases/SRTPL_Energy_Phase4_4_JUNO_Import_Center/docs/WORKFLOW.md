# JUNO Import Workflow

## User workflow
1. Login.
2. Open JUNO Import Center.
3. Download report from JUNO.
4. Upload the original CSV.
5. Application calculates SHA-256.
6. Application detects report type.
7. Application extracts metadata.
8. Application performs exact-file duplicate check.
9. Application performs record/business-key duplicate checks during pipeline.
10. Original CSV is stored unchanged in private Storage.
11. Import batch/file/rows are recorded.
12. Raw JUNO records are inserted.
13. Phase 3.2 validation runs.
14. Normalized readings are generated.
15. Phase 3.3 KPI engine runs.
16. Import result is displayed.
17. Import becomes traceable from dashboard to original CSV.

## Important
The user does NOT edit the CSV.

Do not:
- remove multi-row headings
- rename columns
- delete blank cells
- convert blanks to zero
- manually copy rows into another format

The parser handles JUNO's report structure internally.
