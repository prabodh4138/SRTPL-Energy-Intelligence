import pandas as pd

class DQRepository:
    def summary(self, start_date=None, end_date=None, plaza=None):
        # Production integration: query energy_dashboard read models.
        return {}

    def source_health(self, start_date=None, end_date=None, plaza=None):
        return pd.DataFrame(columns=[
            "Source", "Last Import", "Status", "Records",
            "Valid %", "Exceptions", "Coverage %"
        ])

    def import_health(self, start_date=None, end_date=None):
        return pd.DataFrame(columns=[
            "Date", "Received", "Imported", "Invalid",
            "Duplicate", "Failed", "Completed"
        ])

    def exception_ageing(self):
        return pd.DataFrame(columns=[
            "Age Bucket", "INFO", "WARNING", "ERROR", "CRITICAL"
        ])
