# Equipment Dashboard Design

## Common structure
Equipment Type → Asset → Date Range

Then:
1. KPI Summary
2. Latest Parameters
3. Parameter Catalogue
4. Parameter Trend
5. Exceptions
6. Source Traceability

## Solar
- cumulative generation
- daily generation
- generation trend
- zero-generation/anomaly status
- saving framework

## DG
- status
- KVA/KW
- PF
- diesel level/top-up
- KWH
- running hours
- RPM
- generation/runtime/efficiency
- fuel efficiency/cost
- phase electrical health

## EB
- kWh
- kVAh
- kVARh
- MD
- PF
- consumption trend
- tariff/cost framework

## Transformer
- primary/secondary voltage
- primary/secondary current
- KWH/KVAH
- PF
- frequency
- WTI/OTI
- phase imbalance

Loss/efficiency is disabled until the measurement boundary and CT/PT ratios are confirmed.

## UPS
- input
- rectifier
- bypass
- output
- battery
- frequency
- availability
- anomalies

Blank fields remain NULL/unavailable.

## Traceability
KPI/parameter
→ normalized reading
→ raw JUNO record
→ import row
→ original JUNO CSV.
