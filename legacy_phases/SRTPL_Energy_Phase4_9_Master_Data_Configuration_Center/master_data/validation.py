def require_text(value, field):
    if value is None or not str(value).strip():
        raise ValueError(f"{field} is required.")

def validate_plaza(code, name):
    require_text(code, "Plaza code")
    require_text(name, "Plaza name")

def validate_asset(asset_code, asset_type):
    require_text(asset_code, "Asset code")
    require_text(asset_type, "Asset type")

def validate_effective_dates(start, end=None):
    require_text(start, "Effective from")
    if end is not None and str(end) < str(start):
        raise ValueError("Effective-to cannot be before effective-from.")

def validate_threshold(warning, critical):
    if warning is not None and critical is not None and float(critical) < float(warning):
        raise ValueError("Critical threshold cannot be below warning threshold.")
