def import_identity(file_hash, source_type):
    return f"{source_type}:{file_hash}"

def can_retry(status):
    return status in {"FAILED", "PARTIAL", "BLOCKED"}

def duplicate_blocked(existing_hash, new_hash):
    return bool(existing_hash and new_hash and existing_hash == new_hash)
