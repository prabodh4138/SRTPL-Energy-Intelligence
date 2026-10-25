class ReportAudit:
    def build_record(self, request, row_count, file_name, status):
        return {
            "report_code": request.report_code,
            "date_from": request.filters.date_from,
            "date_to": request.filters.date_to,
            "plaza_id": request.filters.plaza_id,
            "source_type": request.filters.source_type,
            "asset_id": request.filters.asset_id,
            "output_format": request.output_format,
            "requested_by": request.requested_by,
            "row_count": row_count,
            "file_name": file_name,
            "status": status,
        }
