from dataclasses import dataclass
from typing import Optional

ROLES = (
    "SUPER_ADMIN",
    "ADMIN",
    "ENERGY_MANAGER",
    "PLAZA_MANAGER",
    "OPERATOR",
    "AUDITOR",
    "VIEWER",
)

AUDIT_ACTIONS = (
    "LOGIN",
    "LOGOUT",
    "CREATE",
    "UPDATE",
    "DELETE",
    "IMPORT",
    "REPROCESS",
    "APPROVE",
    "REJECT",
    "RESOLVE_EXCEPTION",
    "ACCEPT_EXCEPTION",
    "EXPORT_REPORT",
    "CONFIG_CHANGE",
)

@dataclass
class UserRole:
    user_id: str
    role_code: str
    plaza_id: Optional[str] = None
    active: bool = True

@dataclass
class ChangeRequest:
    request_id: Optional[str]
    entity_type: str
    entity_id: str
    change_type: str
    old_value: Optional[str]
    proposed_value: Optional[str]
    reason: str
    requested_by: str
    status: str = "PENDING"

@dataclass
class AuditEvent:
    audit_id: Optional[str]
    actor_user_id: Optional[str]
    action: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    reason: Optional[str]
    ip_address: Optional[str] = None
    created_at: Optional[str] = None
