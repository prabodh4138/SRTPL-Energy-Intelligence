import pandas as pd

COLUMNS = [
    "Exception ID", "Batch ID", "Import Row", "Source", "Plaza",
    "Asset", "Rule", "Severity", "Status", "Parameter",
    "Source Value", "Expected", "Message", "Created At",
    "Resolved By", "Resolved At", "Resolution Note"
]

class ExceptionRepository:
    def list_exceptions(self, filters=None, limit=500):
        # Production integration: query energy_validation.exception_master.
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
