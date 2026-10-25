# Controlled Reprocessing

Reprocessing is used when:
- a parser bug is fixed
- validation rules are corrected
- KPI logic is versioned
- master-data mapping is corrected

Workflow:
REQUESTED → APPROVED → RUNNING → COMPLETED/FAILED

Rules:
1. Never overwrite the original JUNO file.
2. Preserve original import batch.
3. Record parser/rule/KPI versions.
4. Rebuild derived/normalized/KPI outputs deterministically.
5. Record who requested and approved reprocessing.
6. Keep previous calculation results traceable.
7. Prevent concurrent duplicate reprocessing jobs for the same batch/version.
