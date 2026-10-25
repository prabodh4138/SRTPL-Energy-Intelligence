from .csv_reader import clean_cell

def find_header_rows(rows: list[list[str]], report_type: str) -> tuple[int, list[list[str]]]:
    """
    JUNO uses different header depths. Locate the first row containing
    the characteristic data fields rather than relying on fixed row numbers.
    """
    signatures = {
        "SOLAR": ["date", "unit generated in kwh"],
        "DG": ["date", "status", "kva", "kw"],
        "EB": ["date", "kwh", "kvah", "kvarh"],
        "TRANSFORMER": ["date", "primary side", "secondary side"],
        "UPS": ["date", "time", "main(input)", "battery"],
    }

    wanted = signatures[report_type]

    for i, row in enumerate(rows[:30]):
        cells = [(c or "").strip().lower() for c in row]
        joined = " ".join(cells)
        if all(any(s in c or s in joined for c in cells) for s in wanted):
            return i, rows[i:i+3]

    # Some reports have grouped headers. Fall back to the first row
    # containing Date and at least two expected fields.
    for i, row in enumerate(rows[:30]):
        joined = " ".join((c or "").strip().lower() for c in row)
        if "date" in joined:
            return i, rows[i:i+3]

    raise ValueError(f"Could not locate JUNO header for {report_type}")

def flatten_headers(header_rows: list[list[str]]) -> list[str]:
    width = max(len(r) for r in header_rows)
    result = []
    previous = [None] * width

    for col in range(width):
        parts = []
        for row in header_rows:
            value = clean_cell(row[col]) if col < len(row) else None
            if value and value not in parts:
                parts.append(value)

        # Avoid duplicate Created By/Created On group labels.
        name = " | ".join(parts) if parts else f"column_{col+1}"
        result.append(name)

    # Make keys unique without destroying the source meaning.
    seen = {}
    unique = []
    for name in result:
        base = name
        count = seen.get(base, 0) + 1
        seen[base] = count
        unique.append(base if count == 1 else f"{base} [{count}]")
    return unique
