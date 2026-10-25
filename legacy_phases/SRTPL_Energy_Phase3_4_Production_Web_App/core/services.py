from dataclasses import dataclass
from datetime import datetime

@dataclass
class ImportResult:
    status: str
    report_type: str | None
    rows_received: int
    message: str

class EnergyService:
    def import_juno_csv(self, uploaded_file):
        # Production implementation will delegate to Phase 3/3.1 pipeline.
        data = uploaded_file.getvalue()
        return ImportResult("READY_FOR_PIPELINE", None, 0,
                             "CSV received. Connect Phase 3.1 ImportPipeline during final assembly.")

    def dashboard_summary(self):
        return {
            "EB": "Awaiting production database connection",
            "DG": "Awaiting production database connection",
            "Solar": "Awaiting production database connection",
            "Transformer": "Awaiting production database connection",
            "UPS": "Awaiting production database connection",
        }
