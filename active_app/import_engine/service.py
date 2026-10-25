from pathlib import Path
from .hash_utils import sha256_file
from .parsers import parse_file
from .business_keys import record_hash, make_business_key

class ImportService:
    """
    Phase 3 parser/orchestration boundary.

    Supabase operations are intentionally separated from parsing so the
    parser can be tested locally before database writes are enabled.
    """

    def inspect(self, path: str):
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(path)

        parsed = parse_file(path)

        for record in parsed.records:
            record.source_record_hash = record_hash(record.raw_payload)
            record.business_key = make_business_key(
                parsed.report_type, record.values
            )

        return {
            "filename": path.name,
            "sha256": sha256_file(path),
            "report_type": parsed.report_type,
            "parser_version": parsed.parser_version,
            "metadata": parsed.metadata,
            "headers": parsed.headers,
            "record_count": len(parsed.records),
            "records": parsed.records,
        }
