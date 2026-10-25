# SRTPL Energy Analytics — Phase 3.3
KPI & Energy Analytics Engine.

Purpose:
- Convert validated/normalized JUNO readings into configurable KPI results.
- Preserve NULL vs zero.
- Reject cumulative decreases instead of creating negative generation/consumption.
- Maintain KPI calculation version and source traceability.
- Support Solar, DG, EB, Transformer and UPS.
- Provide energy balance, cost and data-quality calculation foundations.

Engineering safeguards:
- Transformer loss/efficiency remains disabled until CT/PT, meter boundaries and rating are confirmed.
- EB MD interpretation remains SOURCE_VALUE_UNCONFIRMED until meter/TPWODL documentation confirms its unit.
- TPWODL Bill is a future extension.
