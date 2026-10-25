from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class ValidationIssue:
    rule_code: str
    severity: str
    message: str
    source_value: Optional[str] = None
    expected_value: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidationResult:
    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def error_count(self):
        return sum(i.severity in ("ERROR", "CRITICAL") for i in self.issues)

    @property
    def warning_count(self):
        return sum(i.severity == "WARNING" for i in self.issues)
