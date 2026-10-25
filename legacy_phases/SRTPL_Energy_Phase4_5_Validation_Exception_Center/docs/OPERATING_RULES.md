# Exception Operating Rules

## 1. Never delete invalid source data
The original JUNO row remains available.

## 2. Exception is not the same as data deletion
An exception explains a problem; it does not erase the source.

## 3. Severity
- INFO: informational
- WARNING: suspicious but potentially usable
- ERROR: invalid for normal KPI processing
- CRITICAL: serious integrity/safety/data issue

## 4. Status
OPEN → ACKNOWLEDGED → UNDER_REVIEW → RESOLVED

An accepted legitimate anomaly may become:
OPEN/UNDER_REVIEW → ACCEPTED_EXCEPTION

Resolved and accepted exceptions remain in history.

## 5. KPI eligibility
A validation failure must not silently enter KPI calculations.
KPI engines should use validated/eligible normalized readings according to rule policy.

## 6. Manual correction
If a source value must be corrected, create a correction/change request with:
- old value
- new value
- reason
- user
- timestamp
- approval where required

Do not overwrite the original JUNO source.

## 7. Safety-related values
Transformer/UPS warnings must remain visible even when management KPI processing excludes the affected reading.
