import pandas as pd

COLUMNS = [
    "Exception ID", "Batch ID", "Import Row", "Source", "Plaza",
    "Asset", "Rule", "Severity", "Status", "Parameter",
    "Source Value", "Expected", "Message", "Created At",
    "Resolved By", "Resolved At", "Resolution Note"
]

class ExceptionRepository:
    def list_exceptions(self, filters=None, limit=500):
        from core.demo_store import is_demo_mode, get_demo_exceptions
        if is_demo_mode():
            df = get_demo_exceptions()
            if filters:
                if filters.get("source"):
                    df = df[df["Source"] == filters["source"]]
                if filters.get("severity"):
                    df = df[df["Severity"] == filters["severity"]]
                if filters.get("status"):
                    df = df[df["Status"] == filters["status"]]
                if filters.get("plaza"):
                    df = df[df["Plaza"] == filters["plaza"]]
            return df
        return pd.DataFrame(columns=COLUMNS)

    def get_exception(self, exception_id):
        return None

    def update_status(self, exception_id, status, note=None):
        # Production integration: use a transaction/RPC so status change
        # and audit record are atomic.
        return {
            "exception_id": exception_id,
            "status": status,
            "resolution_note": note,
        }
