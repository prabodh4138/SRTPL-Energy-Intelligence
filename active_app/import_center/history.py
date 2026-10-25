import pandas as pd

def empty_import_history():
    return pd.DataFrame(columns=[
        "Batch ID", "Filename", "Report Type", "Imported At",
        "Status", "Rows Received", "Rows Imported",
        "Invalid", "Duplicate", "SHA-256"
    ])

class ImportHistoryRepository:
    def list_recent(self, limit=100):
        from core.demo_store import is_demo_mode, get_demo_import_history
        if is_demo_mode():
            return get_demo_import_history().head(limit)
        return empty_import_history().head(limit)

    def get_batch(self, batch_id):
        return {}
