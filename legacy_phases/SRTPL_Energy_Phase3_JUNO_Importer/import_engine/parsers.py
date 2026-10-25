from datetime import datetime
from .csv_reader import read_csv_rows, clean_cell
from .detector import detect_report_type, detect_metadata
from .header_parser import find_header_rows, flatten_headers
from .models import ParsedReport, ParsedRecord

PARSER_VERSION = "0.1.0"

def _normalize_key(name: str) -> str:
    return (
        name.lower()
        .replace("|", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "_")
        .replace(" ", "_")
        .replace("-", "_")
    )

def parse_file(path: str) -> ParsedReport:
    rows = read_csv_rows(path)
    if not rows:
        raise ValueError("CSV is empty.")

    report_type = detect_report_type(rows)
    metadata = detect_metadata(rows, report_type)

    header_index, header_rows = find_header_rows(rows, report_type)
    headers = flatten_headers(header_rows)

    # Data starts after the grouped header rows. Usually 1-3 rows.
    data_start = header_index + len(header_rows)

    records = []
    for row_no, row in enumerate(rows[data_start:], start=data_start + 1):
        if not any(clean_cell(c) is not None for c in row):
            continue

        values = {}
        raw = {}
        for i, header in enumerate(headers):
            value = clean_cell(row[i]) if i < len(row) else None
            raw[header] = value
            values[_normalize_key(header)] = value

        # Ignore accidental footer rows if they have no date/time identity.
        if not values.get("date") and not values.get("date_time"):
            continue

        records.append(
            ParsedRecord(
                source_row_number=row_no,
                values=values,
                raw_payload=raw,
            )
        )

    return ParsedReport(
        metadata=metadata,
        headers=headers,
        records=records,
        report_type=report_type,
        parser_version=PARSER_VERSION,
    )
