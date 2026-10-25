# Plaza Dashboard Design

## Header
Selected plaza + date range.

## KPI block
- EB consumption
- DG generation
- Solar generation
- DG runtime
- Energy cost
- Solar saving
- DG kWh/hour
- EB PF
- DG PF

## Energy mix
EB / DG / Solar.

## Data quality
Completeness, invalid records, duplicates and exceptions.

## Asset status
Current/latest state for:
- EB meter
- DG
- Solar plant
- Transformer
- UPS

Actual asset list comes from master data.

## Trends
Daily EB, DG and Solar.

## Equipment performance
Asset-level KPI table with drill-down.

## Exceptions
Severity, rule, asset, date and status.

## Drill-down
Plaza → Asset → Parameter → KPI → normalized reading → raw JUNO record → original CSV.
