import csv
import io

def preview_csv(data: bytes, max_rows=10):
    text = data.decode("utf-8-sig", errors="replace")
    lines = text.splitlines()
    rows = list(csv.reader(io.StringIO(text)))
    return {
        "line_count": len(lines),
        "sample_rows": rows[:max_rows],
        "raw_text_prefix": text[:5000],
    }
