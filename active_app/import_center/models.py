from dataclasses import dataclass, field
from typing import Optional

@dataclass
class FileMetadata:
    filename: str
    size_bytes: int
    sha256: str
    report_type: Optional[str] = None
    report_name: Optional[str] = None
    downloaded_by: Optional[str] = None
    downloaded_at: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    organization: Optional[str] = None
    asset_id: Optional[str] = None
    location: Optional[str] = None
    row_count: Optional[int] = None

@dataclass
class ImportCheck:
    code: str
    status: str
    message: str

@dataclass
class ImportResult:
    batch_id: Optional[str]
    status: str
    report_type: Optional[str]
    file_hash: str
    rows_received: int = 0
    rows_imported: int = 0
    rows_invalid: int = 0
    rows_duplicate: int = 0
    checks: list[ImportCheck] = field(default_factory=list)
    message: str = ""
