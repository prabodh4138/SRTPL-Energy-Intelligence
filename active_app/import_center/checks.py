from .models import ImportCheck

def file_checks(filename, data, detected_type, duplicate_file=False):
    checks = []
    checks.append(ImportCheck(
        "FILE_PRESENT", "PASS" if data else "FAIL",
        "CSV file received." if data else "Empty file."
    ))
    checks.append(ImportCheck(
        "CSV_EXTENSION", "PASS" if filename.lower().endswith(".csv") else "FAIL",
        "JUNO source format is CSV."
    ))
    checks.append(ImportCheck(
        "REPORT_DETECTED", "PASS" if detected_type else "REVIEW",
        detected_type or "Report type could not be confidently detected."
    ))
    checks.append(ImportCheck(
        "FILE_DUPLICATE", "BLOCK" if duplicate_file else "PASS",
        "Exact file hash already exists." if duplicate_file else "No exact file duplicate detected."
    ))
    return checks

def checks_pass(checks):
    return not any(c.status == "FAIL" or c.status == "BLOCK" for c in checks)
