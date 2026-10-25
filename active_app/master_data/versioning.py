from dataclasses import dataclass
from typing import Optional

@dataclass
class ConfigVersion:
    config_version_id: Optional[str]
    domain: str
    entity_id: str
    version_no: int
    effective_from: str
    effective_to: Optional[str]
    active: bool

def next_version(existing_versions):
    if not existing_versions:
        return 1
    return max(v.version_no for v in existing_versions) + 1
