# SRTPL Power Consumption Analytics — Phase 4.2
## Plaza Dashboard

Phase 4.2 adds the operational dashboard for TP01, TP02 and TP03.

### Main objective
Management can see the overall picture in Phase 4.1. Phase 4.2 lets an authorized user select one plaza and inspect:
- EB
- DG
- Solar
- Transformer
- UPS
- Energy mix
- Cost/savings
- Data quality
- Exceptions
- Daily/monthly trends
- Asset drill-down foundation

### Design
Plaza relationships are database-driven. TP01/TP02/TP03 are current known plazas, but the UI is designed so additional plazas can be added through master data without rewriting business logic.

### Data rule
No sample production values are embedded. Missing data remains missing, not zero.
