from dataclasses import dataclass

@dataclass
class HealthResult:
    name: str
    status: str
    detail: str

def health_check(database, storage):
    results = []

    try:
        database()
        results.append(HealthResult("DATABASE", "PASS", "Database connectivity successful."))
    except Exception as exc:
        results.append(HealthResult("DATABASE", "FAIL", str(exc)))

    try:
        storage()
        results.append(HealthResult("STORAGE", "PASS", "Original-file storage accessible."))
    except Exception as exc:
        results.append(HealthResult("STORAGE", "FAIL", str(exc)))

    return results

def overall_status(results):
    return "FAIL" if any(r.status == "FAIL" for r in results) else "PASS"
