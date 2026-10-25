from dataclasses import dataclass
from typing import Optional

@dataclass
class DQMetrics:
    records_received: int = 0
    records_valid: int = 0
    records_invalid: int = 0
    records_duplicate: int = 0
    completeness_pct: Optional[float] = None
    validation_pass_pct: Optional[float] = None
    duplicate_rate_pct: Optional[float] = None
    exception_rate_pct: Optional[float] = None
    manual_correction_rate_pct: Optional[float] = None
    audit_traceability_pct: Optional[float] = None

@dataclass
class SourceHealth:
    source_type: str
    last_import_at: Optional[str]
    last_status: Optional[str]
    records_received: int
    valid_pct: Optional[float]
    exception_count: int
    coverage_pct: Optional[float]
