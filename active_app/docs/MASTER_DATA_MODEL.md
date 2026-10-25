# Master Data Model

## Plaza
Defines the operational location.

## Asset
Defines physical/logical equipment such as:
- Solar plant
- DG
- EB meter
- Transformer
- UPS

## Parameter
Defines measurable fields such as:
- kWh
- KVAH
- PF
- voltage
- current
- temperature
- running hours

## Asset Parameter
Connects an asset to the parameters it is expected to report.

This is the key mechanism that makes the system future-proof.

Example:
A new UPS can be added by creating an asset and mapping its parameters. The application does not require new hard-coded UI/database relationships for basic ingestion.

## Threshold
Defines warning/critical conditions.

## Tariff
Defines time-effective energy/demand/fixed-charge rates.

## KPI
Defines calculation identity and version.

## Source Mapping
Maps JUNO report columns to internal parameters.

## Report Schedule
Defines future automated report delivery.
