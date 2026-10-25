# Import Error Handling

## BLOCKED
Used for:
- exact duplicate file
- invalid file type
- empty file
- unresolved report type when policy requires manual review

## FAILED
Technical failure requiring retry.

## PARTIAL
Some rows imported but some records failed validation/import. Original file remains available.

## COMPLETED
Import, validation/normalization and KPI processing completed.

## Retry rule
Retries must reuse the same file hash/import identity and must not create duplicate source records.
