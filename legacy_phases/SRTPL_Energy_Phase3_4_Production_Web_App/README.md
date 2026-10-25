# SRTPL Power Consumption Analytics — Phase 3.4
## Production Web Application Architecture

This is the browser-based application shell for the SRTPL Energy Intelligence system.

### Final user model
Office laptop/mobile:
- Browser only
- Login
- Download JUNO CSV
- Upload CSV
- Review import/validation result
- View dashboards/reports

Development machine:
- Python/VS Code
- Testing
- Supabase migrations
- Deployment

### Included application areas
1. Login/security foundation
2. Executive Dashboard
3. Plaza Dashboard
4. JUNO CSV Import
5. Import History
6. Validation & Exceptions
7. Solar
8. DG
9. EB
10. Transformer
11. UPS
12. Reports foundation
13. Audit foundation
14. Master Data/Admin foundation
15. Health check

### Integration rule
This package is the application shell. Phase 3, 3.1, 3.2 and 3.3 engines are integrated through stable interfaces. During final assembly, their production implementations replace the fallback service adapters.

### Not yet production-ready
Actual Supabase credentials, RLS policies, migrations, real JUNO files, role assignments and end-to-end deployment/UAT must be completed before production.
