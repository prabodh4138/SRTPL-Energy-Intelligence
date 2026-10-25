from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

@dataclass
class Reading:
    source_type: str
    asset_id: str
    plaza_id: Optional[str]
    reading_at: datetime
    values: dict[str, Any]
    validation_status: str = "VALID"
    source_reading_id: Optional[str] = None
    raw_record_id: Optional[str] = None
    import_row_id: Optional[str] = None
    import_file_id: Optional[str] = None

@dataclass
class KPIResult:
    kpi_code: str
    kpi_name: str
    asset_id: Optional[str]
    plaza_id: Optional[str]
    period_start: datetime
    period_end: datetime
    value: Optional[float]
    unit: str
    status: str = "CALCULATED"
    calculation_version: str = "3.3.0"
    source_reading_count: int = 0
    source_reading_ids: list[str] = field(default_factory=list)
    reason: Optional[str] = None
    calculated_at: datetime = field(default_factory=datetime.utcnow)
