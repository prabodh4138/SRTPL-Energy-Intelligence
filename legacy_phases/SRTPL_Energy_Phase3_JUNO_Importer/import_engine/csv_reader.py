from pathlib import Path
import csv

def read_csv_rows(path: str | Path) -> list[list[str]]:
    # utf-8-sig handles JUNO files that contain a BOM.
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.reader(f))

def clean_cell(value: str | None):
    if value is None:
        return None
    value = value.strip()
    return value if value != "" else None
