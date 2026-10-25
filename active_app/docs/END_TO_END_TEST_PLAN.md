# Phase 5.0 End-to-End Test Plan

## Test 1 — Solar
Upload actual JUNO Solar CSV.
Verify:
- detection
- SHA-256
- original storage
- raw rows
- cumulative handling
- daily generation
- validation
- KPI
- dashboard
- report
- audit trace

## Test 2 — DG
Verify:
- cumulative kWh delta
- running-hour delta
- PF
- KVA/KW
- diesel fields
- exceptions
- KPI

## Test 3 — EB
Verify:
- kWh/KVAH/KVARH
- PF
- MD retained as source field
- no incorrect MD unit assumption

## Test 4 — Transformer
Verify all phase voltage/current fields, KWH/KVAH/PF/frequency/WTI/OTI.
Do NOT enable transformer efficiency/loss until measurement boundaries are confirmed.

## Test 5 — UPS
Verify populated and blank fields.
Blank fields must remain NULL.

## Test 6 — Exact duplicate
Upload same file twice.
Second upload must be blocked by file hash.

## Test 7 — Record duplicate
Use same source records in another file.
Record-level duplicate logic must prevent duplicate normalized readings.

## Test 8 — Invalid data
Inject a controlled invalid test record.
Verify exception creation and KPI exclusion policy.

## Test 9 — Audit
Perform import, exception resolution and report export.
Verify audit records.

## Test 10 — Security
Verify ordinary user cannot:
- modify master data directly
- modify audit log
- access service-role credentials
- bypass plaza scope

## Test 11 — Browser-only
Access deployed URL from office browser/mobile.
Verify no local Python/EXE dependency.
