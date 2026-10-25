# SRTPL Power Consumption Analytics — Phase 4.3
## Equipment Dashboards

Detailed equipment dashboards for:
- Solar
- DG
- EB
- Transformer
- UPS

### Design principles
- Asset master is the source of equipment identity.
- Parameter definitions are database-driven.
- KPI results come from Phase 3.3.
- Validation/exceptions come from Phase 3.2.
- No fake/demo production values.
- NULL remains different from zero.
- UI does not implement engineering formulas.
- Every KPI/reading is intended to be traceable back to the original JUNO CSV.

### Equipment pages
Each equipment page provides:
1. Asset selector
2. Date range
3. KPI summary
4. Latest reading
5. Parameter table
6. Trend chart
7. Abnormal/exception section
8. Source traceability foundation

### Engineering safeguards
Transformer loss/efficiency remains disabled until measurement boundaries are confirmed.
EB MD is displayed as a source parameter until its engineering unit is confirmed.
UPS blank fields remain unavailable, never converted to zero.
