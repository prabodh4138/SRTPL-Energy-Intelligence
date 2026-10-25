import pandas as pd

class AdminRepository:
    def users(self):
        from core.demo_store import is_demo_mode, get_demo_users
        if is_demo_mode():
            return get_demo_users()
        return pd.DataFrame(columns=[
            "User ID", "Email", "Name", "Role", "Plaza", "Active", "Created At"
        ])

    def roles(self):
        return pd.DataFrame(columns=[
            "Role", "Permission", "Scope"
        ])

    def change_requests(self):
        from core.demo_store import is_demo_mode, get_demo_change_requests
        if is_demo_mode():
            return get_demo_change_requests()
        return pd.DataFrame(columns=[
            "Request ID", "Entity", "Change", "Requested By",
            "Requested At", "Status", "Approved By", "Applied At"
        ])

    def audit_log(self):
        from core.demo_store import is_demo_mode, get_demo_audit_log
        if is_demo_mode():
            return get_demo_audit_log()
        return pd.DataFrame(columns=[
            "Audit ID", "Timestamp", "User", "Action",
            "Entity", "Entity ID", "Reason"
        ])

    def reprocess_jobs(self):
        from core.demo_store import is_demo_mode, get_demo_reprocess_jobs
        if is_demo_mode():
            return get_demo_reprocess_jobs()
        return pd.DataFrame(columns=[
            "Job ID", "Batch ID", "Requested By", "Requested At",
            "Status", "Approved By", "Started", "Completed"
        ])
