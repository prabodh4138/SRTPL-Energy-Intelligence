# Master Integration Map

## Upstream
Phase 3:
- parser
- raw import
- validation
- normalization
- KPI engine

## Application
Phase 3.4:
- authentication
- navigation
- application shell

Phase 4:
- dashboards
- JUNO Import Center
- exception center
- data quality
- reports
- administration
- master data

## Production data flow

Browser
→ Streamlit
→ server-side services
→ Supabase PostgreSQL
→ Supabase Storage

The browser never receives service-role credentials.
