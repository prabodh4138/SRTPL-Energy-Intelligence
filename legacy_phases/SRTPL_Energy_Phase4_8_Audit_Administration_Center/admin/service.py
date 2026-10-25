from .permissions import has_permission
from .workflow import can_transition, ALLOWED_CHANGE_TRANSITIONS, ALLOWED_REPROCESS_TRANSITIONS
from .audit import AuditService

class AdminService:
    def __init__(self):
        self.audit = AuditService()

    def authorize(self, role, permission):
        if not has_permission(role, permission):
            raise PermissionError(f"Role {role} is not authorized for {permission}.")

    def change_status(self, current, target):
        if not can_transition(ALLOWED_CHANGE_TRANSITIONS, current, target):
            raise ValueError(f"Invalid change-request transition: {current} -> {target}")

    def reprocess_status(self, current, target):
        if not can_transition(ALLOWED_REPROCESS_TRANSITIONS, current, target):
            raise ValueError(f"Invalid reprocess transition: {current} -> {target}")
