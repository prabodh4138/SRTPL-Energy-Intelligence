from .catalog import REPORT_CATALOG

class ReportEngine:
    def validate_request(self, report_code, output_format):
        if report_code not in REPORT_CATALOG:
            raise ValueError("Unknown report.")
        if output_format not in REPORT_CATALOG[report_code]["formats"]:
            raise ValueError("Output format is not supported for this report.")

    def build_query_spec(self, report_code, filters):
        self.validate_request(report_code, filters.output_format if hasattr(filters, "output_format") else "csv")
        return {
            "report_code": report_code,
            "date_from": filters.date_from,
            "date_to": filters.date_to,
            "plaza_id": filters.plaza_id,
            "source_type": filters.source_type,
            "asset_id": filters.asset_id,
            "status": filters.status,
        }
