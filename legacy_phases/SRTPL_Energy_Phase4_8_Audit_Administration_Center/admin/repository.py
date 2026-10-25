import pandas as pd

class AdminRepository:
    def users(self):
        return pd.DataFrame(columns=[
            "User ID", "Email", "Name", "Role", "Plaza", "Active", "Created At"
        ])

    def roles(self):
        return pd.DataFrame(columns=[
            "Role", "Permission", "Scope"
        ])

    def change_requests(self):
        return pd.DataFrame(columns=[
            "Request ID", "Entity", "Change", "Requested By",
            "Requested At", "Status", "Approved By", "Applied At"
        ])

    def audit_log(self):
        return pd.DataFrame(columns=[
            "Audit ID", "Timestamp", "User", "Action",
            "Entity", "Entity ID", "Reason"
        ])

    def reprocess_jobs(self):
        return pd.DataFrame(columns=[
            "Job ID", "Batch ID", "Requested By", "Requested At",
            "Status", "Approved By", "Started", "Completed"
        ])
