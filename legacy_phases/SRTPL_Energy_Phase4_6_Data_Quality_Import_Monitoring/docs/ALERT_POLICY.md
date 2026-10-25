# Data Quality Alert Policy

The dashboard is monitoring-focused, not a replacement for the validation engine.

Recommended alert bands:
- GOOD
- REVIEW
- CRITICAL

Thresholds should eventually be stored in the database and versioned.

Examples:
- Completeness below configured threshold → REVIEW
- Critical exceptions present → CRITICAL
- Repeated import failures → CRITICAL
- Duplicate rate above threshold → REVIEW
- Audit traceability below threshold → REVIEW

Do not hard-code final business thresholds permanently in Streamlit.
