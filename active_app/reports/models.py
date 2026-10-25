from dataclasses import dataclass
from typing import Optional

@dataclass
class ReportFilter:
    date_from: str
    date_to: str
    plaza_id: Optional[str] = None
    source_type: Optional[str] = None
    asset_id: Optional[str] = None
    status: Optional[str] = None

@dataclass
class ReportRequest:
    report_code: str
    filters: ReportFilter
    output_format: str
    requested_by: str

@dataclass
class ReportResult:
    report_id: str
    report_code: str
    output_format: str
    row_count: int
    generated_at: str
    file_name: str
    status: str
