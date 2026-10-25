from pathlib import Path

REPORT_NAMES = {
    "SOLAR": ["solar", "plant"],
    "DG": ["dg", "diesel", "generator"],
    "EB": ["eb", "daily log"],
    "TRANSFORMER": ["transformer"],
    "UPS": ["ups"],
}

def detect_report_type(filename: str, text: str = ""):
    haystack = f"{Path(filename).name} {text[:5000]}".lower()
    matches = []
    for report_type, words in REPORT_NAMES.items():
        score = sum(word in haystack for word in words)
        if score:
            matches.append((score, report_type))
    if not matches:
        return None
    matches.sort(reverse=True)
    return matches[0][1]
