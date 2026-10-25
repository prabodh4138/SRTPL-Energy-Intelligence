PERMISSIONS = {
    "SUPER_ADMIN": {"*"},
    "ADMIN": {
        "VIEW", "IMPORT", "REPROCESS", "MANAGE_MASTER",
        "VIEW_AUDIT", "MANAGE_USERS", "EXPORT"
    },
    "ENERGY_MANAGER": {
        "VIEW", "IMPORT", "REPROCESS", "VIEW_AUDIT", "EXPORT"
    },
    "PLAZA_MANAGER": {
        "VIEW", "IMPORT", "EXPORT"
    },
    "OPERATOR": {
        "VIEW", "IMPORT", "EXPORT"
    },
    "AUDITOR": {
        "VIEW", "VIEW_AUDIT", "EXPORT"
    },
    "VIEWER": {
        "VIEW", "EXPORT"
    },
}

def has_permission(role_code, permission):
    permissions = PERMISSIONS.get(role_code, set())
    return "*" in permissions or permission in permissions
