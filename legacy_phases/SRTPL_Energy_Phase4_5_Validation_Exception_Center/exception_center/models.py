from dataclasses import dataclass
from typing import Optional

SEVERITIES = ("INFO", "WARNING", "ERROR", "CRITICAL")
STATUSES = ("OPEN", "ACKNOWLEDGED", "UNDER_REVIEW", "RESOLVED", "ACCEPTED_EXCEPTION")

@dataclass
class ExceptionRecord:
    exception_id: Optional[str]
    batch_id: Optional[str]
    import_row_id: Optional[str]
    source_type: Optional[str]
    asset_id: Optional[str]
    plaza_id: Optional[str]
    rule_code: str
    severity: str
    status: str
    parameter: Optional[str]
    source_value: Optional[str]
    expected_value: Optional[str]
    message: str
    created_at: Optional[str] = None
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
    resolution_note: Optional[str] = None
