STAGES = [
    "RECEIVED",
    "HASHED",
    "DUPLICATE_CHECKED",
    "REPORT_DETECTED",
    "STORED_ORIGINAL",
    "IMPORTED_RAW",
    "VALIDATED",
    "NORMALIZED",
    "KPI_PROCESSED",
    "COMPLETED",
]

TERMINAL = {"COMPLETED", "BLOCKED", "FAILED", "PARTIAL"}

def valid_stage(stage):
    return stage in STAGES or stage in TERMINAL
