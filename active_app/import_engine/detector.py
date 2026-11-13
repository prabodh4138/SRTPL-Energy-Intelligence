import re
from .models import ReportMetadata
from .csv_reader import clean_cell

REPORT_SIGNATURES = {
    "SOLAR": ["solar", "unit generated in kwh", "solarplantid", "solar plant id", "solar generation"],
    "DG": ["dg", "diesel", "running hours", "generator no", "diesel top-up", "rpm", "load current"],
    "EB": ["eb", "consumer number", "eb meter id", "kvah", "kvarh", "maximum demand", "power factor"],
    "TRANSFORMER": ["transformer daily log report", "transformer", "primary side", "secondary side", "transformer id", "wti", "oti"],
    "UPS": ["ups daily log report", "ups", "battery", "by pass", "ups id", "rectifier voltage", "vdc", "main(input)"],
}

ASSET_CODE_PATTERNS = [
    (re.compile(r"SR-E-EM-EB-", re.IGNORECASE), "EB"),
    (re.compile(r"SR-E-(?:AP-DGX|DG)-", re.IGNORECASE), "DG"),
    (re.compile(r"SR-E-AP-SPX-", re.IGNORECASE), "SOLAR"),
    (re.compile(r"SR-E-HT-TFR-", re.IGNORECASE), "TRANSFORMER"),
    (re.compile(r"SR-E-AP-UPS-", re.IGNORECASE), "UPS"),
]

def detect_report_type(rows: list[list[str]], filename: str | None = None) -> str:
    # 1. First priority: Check asset code patterns directly in the first 15 rows
    for row in rows[:15]:
        for cell in row:
            val = (cell or "").strip()
            if not val:
                continue
            for pattern, rtype in ASSET_CODE_PATTERNS:
                if pattern.search(val):
                    return rtype

    # 2. Check title or specific equipment headers in rows
    text = " ".join(
        (cell or "").strip().lower()
        for row in rows[:20]
        for cell in row
    )
    scores = {}
    for report_type, signatures in REPORT_SIGNATURES.items():
        scores[report_type] = sum(1 for s in signatures if s in text)

    report_type, score = max(scores.items(), key=lambda x: x[1])
    if score > 0:
        return report_type

    # 3. Fallback: Inspect filename if provided
    if filename:
        fn_lower = filename.lower()
        if "generator" in fn_lower or "dg" in fn_lower:
            return "DG"
        if "solar" in fn_lower:
            return "SOLAR"
        if "transformer" in fn_lower or "tfr" in fn_lower:
            return "TRANSFORMER"
        if "ups" in fn_lower:
            return "UPS"
        if "eb" in fn_lower or "grid" in fn_lower:
            return "EB"

    # 4. Fallback: EB tokens check
    if all(token in text for token in ["date", "kwh", "kvah", "kvarh", "md", "pf"]):
        return "EB"

    raise ValueError("Unable to identify JUNO report type automatically from content or asset code.")

def _find_value(rows, labels):
    for row in rows[:12]:
        joined = " ".join((c or "").strip().lower() for c in row)
        for label in labels:
            if label in joined:
                # Return the cell after a matching label where possible.
                for i, c in enumerate(row):
                    if label in (c or "").strip().lower() and i + 1 < len(row):
                        return clean_cell(row[i + 1])
    return None

def detect_metadata(rows, report_type):
    text = "\n".join(",".join(r) for r in rows[:12])
    md = ReportMetadata(report_type=report_type)
    md.report_title = (rows[0][0].strip() if rows and rows[0] else None)

    md.downloaded_by = _find_value(rows, ["downloaded by"])
    md.organization = _find_value(rows, ["srtl", "organization"])
    md.consumer_number = _find_value(rows, ["consumer number", "consumer no"])
    md.category = _find_value(rows, ["category"])
    md.asset_code = _find_value(rows, [
        "solar plant id", "solarplantid", "dg id", "generator no", "eb meter id",
        "transformer id", "ups id"
    ])
    # Detailed EB reports use a tabular metadata header (EB Meter ID is a
    # column name), so its value lives in the first data row rather than the
    # cell immediately to the right of the label.
    if report_type == "EB":
        for i, row in enumerate(rows[:12]):
            lowered = [(c or "").strip().lower() for c in row]
            if "eb meter id" in lowered and "period" in lowered and "unit consumption in kwh" in lowered:
                col = lowered.index("eb meter id")
                for data_row in rows[i + 1: i + 4]:
                    if col < len(data_row) and clean_cell(data_row[col]):
                        md.asset_code = clean_cell(data_row[col])
                        break
                if "location" in lowered:
                    loc_col = lowered.index("location")
                    for data_row in rows[i + 1: i + 4]:
                        if loc_col < len(data_row) and clean_cell(data_row[loc_col]):
                            md.location = clean_cell(data_row[loc_col])
                            break
                break

    # Fallback asset_code discovery using regex in top rows if label wasn't matched
    if not md.asset_code:
        for row in rows[:15]:
            for cell in row:
                c = (cell or "").strip()
                match = re.search(r"(SR-E-(?:EM-EB|AP-DGX|DG|AP-SPX|HT-TFR|AP-UPS)-[A-Za-z0-9_-]+)", c, re.IGNORECASE)
                if match:
                    md.asset_code = match.group(1).strip()
                    break
            if md.asset_code:
                break

    md.location = md.location or _find_value(rows, ["location"])

    return md
