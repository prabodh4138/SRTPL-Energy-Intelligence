# SRTPL Power Consumption Analytics — Phase 4.1
## Executive Dashboard

Phase 4.1 creates the management-facing dashboard layer on top of Phase 3.4.

### Dashboard objectives
- Three-plaza executive overview: TP01, TP02, TP03
- Energy source overview: EB, DG, Solar
- Cost and savings overview
- Data-quality visibility
- Exception visibility
- Daily/monthly trend foundation
- KPI drill-down foundation
- Date/plaza filtering
- Browser/mobile-friendly layout

### Design principle
The dashboard never becomes the master data store. It reads KPI results, normalized readings, validation/exception records and master data from Supabase.

### Traceability
Management KPI
 -> Plaza
 -> Asset
 -> Parameter
 -> KPI result
 -> Normalized reading
 -> Raw JUNO record
 -> Import row
 -> Original JUNO CSV

### Production note
The dashboard includes safe empty-state behavior. Sample/demo values are disabled by default. Real KPI values will appear after the Phase 3.1/3.2/3.3 services are connected to the production Supabase schema.
