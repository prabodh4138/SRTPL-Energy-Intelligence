ERROR_POLICY = {
    "BLOCKED": "Do not process further; retain original file and reason.",
    "FAILED": "Rollback incomplete derived writes where possible; permit controlled retry.",
    "PARTIAL": "Retain imported/failed row counts and expose exceptions.",
    "COMPLETED": "All configured stages completed successfully.",
}

def user_message(status):
    return ERROR_POLICY.get(status, "Unexpected application state.")
