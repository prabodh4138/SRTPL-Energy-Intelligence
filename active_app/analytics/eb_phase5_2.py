from __future__ import annotations
from datetime import datetime, timezone

KPI_DEFS = [
    ("EB-CONS-D", "EB Consumption", "kWh"),
    ("EB-KVAH-D", "EB KVAH Consumption", "kVAh"),
    ("EB-KVARH-D", "EB KVARH Consumption", "kVARh"),
    ("EB-PF-AVG-D", "EB Average PF", "PF"),
    ("EB-PF-MIN-D", "EB Minimum PF", "PF"),
    ("EB-MD-MAX-D", "EB Maximum MD", "kW"),
    ("EB-KWH-KVAH-RATIO-D", "EB kWh/kVAh Ratio", "ratio"),
]


def _readings(db, batch_id):
    return db.schema("energy_readings").table("eb").select(
        "reading_id,asset_id,reading_datetime,interval_kwh,interval_kvah,interval_kvarh,md,pf,data_quality_status,import_row_id"
    ).eq("data_quality_status", "VALID").in_("import_row_id", _batch_row_ids(db, batch_id)).order("reading_datetime").execute().data


def _batch_row_ids(db, batch_id):
    files = db.schema("energy_import").table("import_file").select("import_file_id").eq("import_batch_id", batch_id).execute().data
    ids = [x["import_file_id"] for x in files]
    if not ids:
        return [-1]
    rows = db.schema("energy_import").table("import_row").select("import_row_id").in_("import_file_id", ids).execute().data
    return [x["import_row_id"] for x in rows] or [-1]


def _num(v):
    try:
        return None if v is None else float(v)
    except (TypeError, ValueError):
        return None


def calculate_eb_kpis(db, batch_id: str, calculation_version: str = "5.2.6"):
    rows = _readings(db, batch_id)
    valid = [r for r in rows if r.get("data_quality_status") == "VALID"]
    values = {
        "EB-CONS-D": sum(_num(r.get("interval_kwh")) or 0 for r in valid),
        "EB-KVAH-D": sum(_num(r.get("interval_kvah")) or 0 for r in valid),
        "EB-KVARH-D": sum(_num(r.get("interval_kvarh")) or 0 for r in valid),
        "EB-PF-AVG-D": _avg([_num(r.get("pf")) for r in valid]),
        "EB-PF-MIN-D": _min([_num(r.get("pf")) for r in valid]),
        "EB-MD-MAX-D": _max([_num(r.get("md")) for r in valid]),
    }
    values["EB-KWH-KVAH-RATIO-D"] = (
        values["EB-CONS-D"] / values["EB-KVAH-D"]
        if values["EB-KVAH-D"] else None
    )

    kpi_master = db.schema("energy_analytics").table("kpi_master").select("kpi_id,kpi_code,version,unit").in_("kpi_code", [x[0] for x in KPI_DEFS]).eq("is_active", True).execute().data
    master = {(r["kpi_code"], r.get("version", "1.0")): r for r in kpi_master}
    # Prefer the active/latest version returned by Supabase.
    by_code = {}
    for r in kpi_master:
        by_code[r["kpi_code"]] = r

    period_dates = [r.get("reading_datetime") for r in valid if r.get("reading_datetime")]
    start = min(period_dates) if period_dates else datetime.now(timezone.utc).isoformat()
    end = max(period_dates) if period_dates else start
    source_ids = [str(r["reading_id"]) for r in valid]
    results = []
    for code, name, unit in KPI_DEFS:
        km = by_code.get(code)
        if not km:
            continue
        results.append({
            "kpi_id": km["kpi_id"],
            "kpi_code": code,
            "kpi_version": km.get("version", "1.0"),
            "asset_id": valid[0].get("asset_id") if valid else None,
            "period_start": start,
            "period_end": end,
            "value": values[code],
            "unit": unit,
            "status": "OK" if valid else "NO_VALID_SOURCE",
            "calculation_version": calculation_version,
            "source_reading_count": len(valid),
            "source_reading_ids": source_ids,
        })
    if results:
        db.schema("energy_analytics").table("kpi_result").upsert(
            results,
            on_conflict="kpi_code,kpi_version,asset_id,plaza_id,period_start,period_end",
        ).execute()
    return {
        "results": [{"kpi_code": k, "value": values[k], "unit": u} for k, _, u in KPI_DEFS],
        "source_reading_ids": source_ids,
        "source_record_count": len(valid),
        "exception_rows_excluded": len(rows) - len(valid),
        "calculation_version": calculation_version,
    }


def _avg(vals):
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else None


def _min(vals):
    vals = [v for v in vals if v is not None]
    return min(vals) if vals else None


def _max(vals):
    vals = [v for v in vals if v is not None]
    return max(vals) if vals else None
