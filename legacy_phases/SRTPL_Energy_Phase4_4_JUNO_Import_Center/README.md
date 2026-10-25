# SRTPL Power Consumption Analytics — Phase 4.4
## JUNO Import Center

This module implements the browser workflow:

JUNO → Download CSV → Upload → Pre-check → Detect report → Metadata → SHA-256 duplicate check → Import pipeline → Validation → KPI → Result

### Supported reports
- SOLAR
- DG
- EB
- TRANSFORMER
- UPS

### Critical rules
1. The original JUNO CSV is never edited.
2. Headings are never stripped from the stored original file.
3. Original files belong in a private Supabase Storage bucket.
4. SHA-256 detects exact duplicate files.
5. Record/business-key duplicate checks are a second protection.
6. NULL is never silently converted to zero.
7. Invalid records are retained and routed to validation/exception handling.
8. Import status must be retry-safe.
9. Every import must be traceable to its original file.
10. Power Panel and TPWODL Bill are future extensions.

This package is the UI/workflow layer; final integration will connect the adapters to Phase 3/3.1/3.2/3.3 production services.
