from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class ReportMetadata:
    report_type: str
    report_title: Optional[str] = None
    downloaded_by: Optional[str] = None
    source_from_date: Optional[str] = None
    source_to_date: Optional[str] = None
    organization: Optional[str] = None
    asset_code: Optional[str] = None
    location: Optional[str] = None
    consumer_number: Optional[str] = None
    category: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ParsedRecord:
    source_row_number: int
    values: dict[str, Any]
    raw_payload: dict[str, Any]
    business_key: Optional[str] = None

@dataclass
class ParsedReport:
    metadata: ReportMetadata
    headers: list[str]
    records: list[ParsedRecord]
    report_type: str
    parser_version: str
