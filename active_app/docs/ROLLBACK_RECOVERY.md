# Rollback & Recovery

Original JUNO files are immutable source evidence.

If a deployment fails:
1. Roll back application version.
2. Do not delete original files.
3. Preserve import batches.
4. Mark failed derived processing clearly.
5. Retry through controlled reprocessing.
6. Preserve KPI/configuration versions.
7. Verify audit trail after recovery.

Database backup and restore procedures must be validated before production go-live.
