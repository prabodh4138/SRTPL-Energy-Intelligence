import hashlib
import json

def record_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def make_business_key(report_type: str, values: dict) -> str:
    # Uses source identity + timestamp. Additional fields can be added
    # per report when JUNO proves that timestamps are not unique.
    identity_fields = {
        "SOLAR": ["solarplantid", "date"],
        "DG": ["dg_id", "date", "time"],
        "EB": ["eb_meter_id", "meter_id", "date", "period"],
        "TRANSFORMER": ["transformer_id", "date"],
        "UPS": ["ups_id", "date", "time"],
    }

    selected = {}
    for field in identity_fields.get(report_type, ["date"]):
        selected[field] = values.get(field)

    return record_hash({"report_type": report_type, **selected})
