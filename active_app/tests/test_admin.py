import pytest
from admin.permissions import has_permission
from admin.workflow import can_transition, ALLOWED_CHANGE_TRANSITIONS, ALLOWED_REPROCESS_TRANSITIONS
from admin.service import AdminService

def test_super_admin():
    assert has_permission("SUPER_ADMIN", "ANYTHING")

def test_viewer_cannot_manage_users():
    assert not has_permission("VIEWER", "MANAGE_USERS")

def test_change_request_transition():
    assert can_transition(ALLOWED_CHANGE_TRANSITIONS, "PENDING", "APPROVED")

def test_reprocess_transition():
    assert can_transition(ALLOWED_REPROCESS_TRANSITIONS, "REQUESTED", "APPROVED")

def test_bad_reprocess_transition():
    assert not can_transition(ALLOWED_REPROCESS_TRANSITIONS, "COMPLETED", "RUNNING")

def test_authorization():
    with pytest.raises(PermissionError):
        AdminService().authorize("VIEWER", "MANAGE_USERS")
