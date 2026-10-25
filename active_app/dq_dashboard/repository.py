import pandas as pd

class DQRepository:
    def summary(self, start_date=None, end_date=None, plaza=None):
        from core.demo_store import is_demo_mode, get_demo_dq_summary
        if is_demo_mode():
            return get_demo_dq_summary()
        return {}

    def source_health(self, start_date=None, end_date=None, plaza=None):
        from core.demo_store import is_demo_mode, get_demo_source_health
        if is_demo_mode():
            return get_demo_source_health()
        return pd.DataFrame(columns=[
            "Source", "Last Import", "Status", "Records",
            "Valid %", "Exceptions", "Coverage %"
        ])

    def import_health(self, start_date=None, end_date=None):
        from core.demo_store import is_demo_mode, get_demo_import_health
        if is_demo_mode():
            return get_demo_import_health()
        return pd.DataFrame(columns=[
            "Date", "Received", "Imported", "Invalid",
            "Duplicate", "Failed", "Completed"
        ])

    def exception_ageing(self):
        from core.demo_store import is_demo_mode, get_demo_exception_ageing
        if is_demo_mode():
            return get_demo_exception_ageing()
        return pd.DataFrame(columns=[
            "Age Bucket", "INFO", "WARNING", "ERROR", "CRITICAL"
        ])
