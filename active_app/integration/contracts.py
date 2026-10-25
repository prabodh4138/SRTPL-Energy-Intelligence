SUPPORTED_SOURCES = {
    "SOLAR",
    "DG",
    "EB",
    "TRANSFORMER",
    "UPS",
}

PIPELINE_STAGES = (
    "RECEIVED",
    "HASHED",
    "DUPLICATE_CHECKED",
    "DETECTED",
    "ORIGINAL_STORED",
    "RAW_IMPORTED",
    "VALIDATED",
    "NORMALIZED",
    "KPI_PROCESSED",
    "COMPLETED",
)

TERMINAL_STATES = {
    "COMPLETED",
    "BLOCKED",
    "FAILED",
    "PARTIAL",
}

def source_supported(source_type):
    return source_type in SUPPORTED_SOURCES
