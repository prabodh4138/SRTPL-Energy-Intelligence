from .models import ReportMetadata
from .csv_reader import clean_cell

REPORT_SIGNATURES = {
    "SOLAR": ["solar", "unit generated in kwh"],
    "DG": ["dg", "diesel", "running hours"],
    "EB": ["eb daily log report", "consumer number", "kvah", "kvarh"],
    "TRANSFORMER": ["transformer daily log report", "primary side", "secondary side"],
    "UPS": ["ups daily log report", "battery", "by pass"],
}

def detect_report_type(rows: list[list[str]]) -> str:
    text = " ".join(
        (cell or "").strip().lower()
        for row in rows[:20]
        for cell in row
    )
    scores = {}
    for report_type, signatures in REPORT_SIGNATURES.items():
        scores[report_type] = sum(1 for s in signatures if s in text)

    report_type, score = max(scores.items(), key=lambda x: x[1])
    if score == 0:
        raise ValueError("Unable to identify JUNO report type.")
    return report_type

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
    md.asset_code = _find_value(rows, [
        "solar plant id", "dg id", "eb meter id",
        "transformer id", "ups id"
    ])
    md.location = _find_value(rows, ["location"])

    return md
