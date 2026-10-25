from .hash import sha256_bytes
from .detector import detect_report_type
from .checks import file_checks, checks_pass
from .models import FileMetadata, ImportResult

class JunoImportService:
    def precheck(self, filename, data, duplicate_file=False):
        sha = sha256_bytes(data)
        detected = detect_report_type(filename, data.decode("utf-8-sig", errors="replace"))
        checks = file_checks(filename, data, detected, duplicate_file)
        return FileMetadata(
            filename=filename,
            size_bytes=len(data),
            sha256=sha,
            report_type=detected,
        ), checks

    def start_import(self, metadata, checks):
        if not checks_pass(checks):
            return ImportResult(
                batch_id=None,
                status="BLOCKED",
                report_type=metadata.report_type,
                file_hash=metadata.sha256,
                checks=checks,
                message="Import blocked by pre-check."
            )

        # Final integration delegates here to Phase 3.1 ImportPipeline,
        # then Phase 3.2 validation/normalization and Phase 3.3 KPI engine.
        return ImportResult(
            batch_id=None,
            status="READY_FOR_PIPELINE",
            report_type=metadata.report_type,
            file_hash=metadata.sha256,
            checks=checks,
            message="Pre-check passed. Connect production import pipeline."
        )
