import pandas as pd

class ReportRepository:
    def fetch(self, report_code, filters):
        # Production integration: query approved energy_dashboard read models.
        # Never query arbitrary raw tables directly from the browser.
        return pd.DataFrame()

    def record_report_run(self, report_request, row_count, status, file_name):
        # Production integration: insert into energy_audit.report_run.
        return {
            "report_code": report_request.report_code,
            "rows": row_count,
            "status": status,
            "file_name": file_name,
        }
