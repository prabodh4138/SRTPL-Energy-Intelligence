import pandas as pd

class ReportRepository:
    def fetch(self, report_code, filters):
        from core.demo_store import is_demo_mode, get_demo_report_df
        if is_demo_mode():
            return get_demo_report_df(report_code)
        return pd.DataFrame()

    def record_report_run(self, report_request, row_count, status, file_name):
        # Production integration: insert into energy_audit.report_run.
        return {
            "report_code": report_request.report_code,
            "rows": row_count,
            "status": status,
            "file_name": file_name,
        }
