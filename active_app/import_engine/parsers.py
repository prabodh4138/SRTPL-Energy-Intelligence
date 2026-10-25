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

        # Normalize the two known JUNO EB layouts without changing the original CSV.
        # Cumulative EB logs expose Date/kWh/KVAH/KVARH; detailed daily reports
        # expose Period/Unit Consumption in kWh/kVAH. The latter is an interval
        # source and is marked in source_payload for downstream normalization.
        if report_type == "EB" and values.get("period") and values.get("unit_consumption_in_kwh") is not None:
            values["date"] = values.get("period")
            values["kwh"] = values.get("unit_consumption_in_kwh")
            values["kvah"] = values.get("unit_consumption_in_kvah")
            values["md"] = values.get("md") or values.get("cmd")
            raw["__source_mode"] = "INTERVAL_CONSUMPTION"
            values["__source_mode"] = "INTERVAL_CONSUMPTION"

        # Carry the report-level asset identifier into every record.
        # JUNO places DG/solar/transformer/UPS identifiers in metadata, not the
        # tabular header, so preserving it here is required for asset linkage.
        asset_key = {
            "DG": "dg_id",
            "SOLAR": "solar_plant_id",
            "EB": "eb_meter_id",
            "TRANSFORMER": "transformer_id",
            "UPS": "ups_id",
        }.get(report_type)
        if asset_key and metadata.asset_code:
            values.setdefault(asset_key, metadata.asset_code)
            raw.setdefault(asset_key, metadata.asset_code)

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
