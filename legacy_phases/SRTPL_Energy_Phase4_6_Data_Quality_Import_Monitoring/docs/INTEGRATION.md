# Phase 4.6 Integration

Data flow:

JUNO
→ Phase 4.4 Import Center
→ Phase 3.1 Import Pipeline
→ Phase 3.2 Validation/Normalization
→ Phase 3.3 KPI Engine
→ Phase 4.5 Exception Center
→ Phase 4.6 Data Quality Monitoring

The dashboard should query read models/views rather than repeatedly scanning large raw tables from Streamlit.

Recommended refresh:
- manual refresh button
- automatic refresh optional
- no aggressive polling that overloads Supabase

Production requirements:
1. RLS-safe read access.
2. No service-role key in browser.
3. Date/plaza/source filters.
4. Configurable expected-reading schedules.
5. Consistent metric definitions between dashboard and KPI engine.
