# SRTPL Power Consumption Analytics — Phase 4.9
## Master Data & Configuration Center

Phase 4.9 provides the governed configuration layer for the SRTPL Energy Intelligence application.

It removes business relationships and operational thresholds from hard-coded Streamlit logic.

Managed domains:
- Plazas
- Assets/equipment
- Parameters
- Asset-parameter mappings
- Validation thresholds
- Tariffs
- KPI definitions
- Reporting schedules
- Source/report mappings
- Configuration versioning

Supported current equipment:
SOLAR, DG, EB, TRANSFORMER, UPS

Future:
Power Panel and TPWODL Bill can be added through master data and source mapping without redesigning the application.

Important:
Configuration changes are controlled administrative changes. They should follow Phase 4.8 change-request/approval rules and must be audited.
