from pathlib import Path
import uuid
from .hash_utils import sha256_file
from .repository import ImportRepository
from .storage import StorageService
from .raw_mapper import RAW_MAPPERS

class ImportPipeline:

    def __init__(self, supabase, settings, parser_service):
        self.repo = ImportRepository(supabase)
        self.storage = StorageService(supabase, settings.storage_bucket)
        self.settings = settings
        self.parser = parser_service

    def run(self, file_path: str, uploaded_by: str):
        path = Path(file_path)
        file_hash = sha256_file(path)

        # Level 1 duplicate prevention.
        if self.repo.file_hash_exists(file_hash):
            return {
                "status": "DUPLICATE_FILE",
                "sha256": file_hash,
                "message": "This exact JUNO file has already been imported."
            }

        inspection = self.parser.inspect(str(path))
        report_type = inspection["report_type"]

        batch_id = str(uuid.uuid4())
        batch = self.repo.create_batch({
            "import_batch_id": batch_id,
            "uploaded_by": uploaded_by,
            "source_system": "JUNO",
            "report_type": report_type,
            "parser_version": inspection["parser_version"],
            "status": "PARSING",
            "total_files": 1,
        })
        batch_id = batch.get("import_batch_id", batch_id)

        # NOTE: Do NOT store raw files into database or cloud storage. Files are processed temporarily and discarded.
        storage_path = ""

        file_id = str(uuid.uuid4())
        file_row = self.repo.create_file({
            "import_file_id": file_id,
            "import_batch_id": batch_id,
            "original_filename": path.name,
            "storage_bucket": self.settings.storage_bucket,
            "storage_path": storage_path,
            "sha256_hash": file_hash,
            "file_size_bytes": path.stat().st_size,
            "report_type": report_type,
            "report_title": inspection["metadata"].report_title,
            "downloaded_by": inspection["metadata"].downloaded_by,
            "source_organization": inspection["metadata"].organization,
            "detected_asset_code": inspection["metadata"].asset_code,
            "detected_location": inspection["metadata"].location,
            "row_count": inspection["record_count"],
            "parsed_row_count": inspection["record_count"],
            "parse_status": "PARSED",
        })
        file_id = file_row.get("import_file_id", file_id)

        import_rows = []
        for rec in inspection["records"]:
            import_rows.append({
                "import_row_id": str(uuid.uuid4()),
                "import_file_id": file_id,
                "source_row_number": rec.source_row_number,
                "source_record_hash": rec.source_record_hash,
                "business_key": rec.business_key,
                "raw_payload": rec.raw_payload,
                "parse_status": "PARSED",
                "validation_status": "PENDING",
            })

        inserted_rows = self.repo.create_rows(import_rows)

        # Attach generated database row IDs back to records.
        for rec, dbrow in zip(inspection["records"], inserted_rows):
            rec.import_row_id = dbrow["import_row_id"]

        table, mapper = RAW_MAPPERS.get(report_type, (None, None))
        raw_rows = [mapper(rec) for rec in inspection["records"]] if mapper else []
        try:
            self.repo.insert_raw("energy_raw", table, raw_rows)
        except Exception:
            pass

        self.repo.update_batch(batch_id, {
            "status": "IMPORTED",
            "total_rows": len(raw_rows),
            "valid_rows": len(raw_rows),
        })

        return {
            "status": "IMPORTED",
            "import_batch_id": batch_id,
            "import_file_id": file_row["import_file_id"],
            "report_type": report_type,
            "sha256": file_hash,
            "rows": len(raw_rows),
        }
