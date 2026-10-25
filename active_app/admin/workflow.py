ALLOWED_CHANGE_TRANSITIONS = {
    "PENDING": {"APPROVED", "REJECTED", "CANCELLED"},
    "APPROVED": {"APPLIED"},
    "REJECTED": set(),
    "CANCELLED": set(),
    "APPLIED": set(),
}

ALLOWED_REPROCESS_TRANSITIONS = {
    "REQUESTED": {"APPROVED", "REJECTED"},
    "APPROVED": {"RUNNING", "CANCELLED"},
    "RUNNING": {"COMPLETED", "FAILED"},
    "REJECTED": set(),
    "CANCELLED": set(),
    "COMPLETED": set(),
    "FAILED": {"REQUESTED"},
}

def can_transition(mapping, current, target):
    return target in mapping.get(current, set())
