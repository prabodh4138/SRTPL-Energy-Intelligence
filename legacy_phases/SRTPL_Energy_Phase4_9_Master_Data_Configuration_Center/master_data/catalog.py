MASTER_DOMAINS = {
    "PLAZA": "Plaza Master",
    "ASSET": "Asset / Equipment Master",
    "PARAMETER": "Parameter Master",
    "ASSET_PARAMETER": "Asset Parameter Mapping",
    "THRESHOLD": "Validation Threshold Master",
    "TARIFF": "Tariff Master",
    "KPI": "KPI Definition Master",
    "SOURCE_MAPPING": "JUNO Source Mapping",
    "REPORT_SCHEDULE": "Report Schedule Master",
}

SOURCE_TYPES = ["SOLAR", "DG", "EB", "TRANSFORMER", "UPS"]

ASSET_TYPES = [
    "SOLAR",
    "DG",
    "EB_METER",
    "TRANSFORMER",
    "UPS",
]

def supported_asset_type(value):
    return value in ASSET_TYPES
