from __future__ import annotations
from datetime import datetime, timezone

KPI_SPECS = [
    ("EB-CONS-D", "EB Consumption", "kWh"),
    ("EB-KVAH-D", "EB KVAH Consumption", "kVAh"),
    ("EB-PF-D", "EB Average PF", "PF"),
    ("EB-KWH-KVAH", "EB kWh/kVAh Ratio", "ratio"),
]


def _batch_rows(db, batch_id):
    try:
        files = db.table("import_file").select("import_file_id").eq("import_batch_id", batch_id).execute().data
    except Exception:
        try:
            files = db.schema("energy_import").table("import_file").select("import_file_id").eq("import_batch_id", batch_id).execute().data
        except Exception:
            files = []
    ids = [x["import_file_id"] for x in files]
    if not ids:
        return []
    try:
        return db.table("import_row").select("import_row_id").in_("import_file_id", ids).order("source_row_number").execute().data
    except Exception:
        try:
            return db.schema("energy_import").table("import_row").select("import_row_id").in_("import_file_id", ids).order("source_row_number").execute().data
        except Exception:
            return []


def calculate_eb_kpis_from_normalized(
    readings: list[dict], batch_id: str = "LOCAL", calculation_version: str = "5.4.0"
) -> dict:
    valid = [r for r in readings if r.get("data_quality_status") == "VALID"]
    excluded = [r for r in readings if r.get("data_quality_status") != "VALID"]
    source_ids = [str(r.get("reading_id", r.get("import_row_id", ""))) for r in valid]

    kwh = sum(float(r["interval_kwh"]) for r in valid if r.get("interval_kwh") is not None)
    kvah = sum(float(r["interval_kvah"]) for r in valid if r.get("interval_kvah") is not None)
    pf_values = [float(r["pf"]) for r in valid if r.get("pf") is not None]
    pf_avg = sum(pf_values) / len(pf_values) if pf_values else None
    ratio = kwh / kvah if kvah else None

    values = {
        "EB-CONS-D": (kwh, "kWh"),
        "EB-KVAH-D": (kvah, "kVAh"),
        "EB-PF-D": (pf_avg, "PF"),
        "EB-KWH-KVAH": (ratio, "ratio"),
    }

    results = []
    for code, (val, unit) in values.items():
        results.append({
            "kpi_code": code,
            "value": val,
            "unit": unit,
            "status": "OK" if val is not None else "INSUFFICIENT_DATA",
        })

    return {
        "batch_id": batch_id,
        "normalized_rows": len(readings),
        "valid_source_rows": len(valid),
        "exception_rows_excluded": len(excluded),
        "results": results,
        "source_reading_ids": source_ids,
        "excluded_exception_reading_ids": [str(r.get("reading_id", "")) for r in excluded],
        "calculation_version": calculation_version,
    }


def calculate_eb_kpis(db, batch_id, calculation_version="5.4.0"):
    rows = _batch_rows(db, batch_id)
    ids = [r["import_row_id"] for r in rows]
    if not ids:
        raise ValueError("No import rows found for batch.")

    readings = (
        db.schema("energy_readings")
        .table("eb")
        .select("*")
        .in_("import_row_id", ids)
        .order("reading_datetime")
        .execute()
        .data
    )
    if not readings:
        raise ValueError("No normalized EB readings found for batch.")

    valid = [r for r in readings if r.get("data_quality_status") == "VALID"]
    excluded = [r for r in readings if r.get("data_quality_status") != "VALID"]
    source_ids = [str(r["reading_id"]) for r in valid]

    kwh = sum(float(r["interval_kwh"]) for r in valid if r.get("interval_kwh") is not None)
    kvah = sum(float(r["interval_kvah"]) for r in valid if r.get("interval_kvah") is not None)
    pf_values = [float(r["pf"]) for r in valid if r.get("pf") is not None]
    pf_avg = sum(pf_values) / len(pf_values) if pf_values else None
    ratio = kwh / kvah if kvah else None

    values = {
        "EB-CONS-D": (kwh, "kWh"),
        "EB-KVAH-D": (kvah, "kVAh"),
        "EB-PF-D": (pf_avg, "PF"),
        "EB-KWH-KVAH": (ratio, "ratio"),
    }

    period_start = readings[0].get("reading_datetime")
    period_end = readings[-1].get("reading_datetime")
    masters = (
        db.schema("energy_analytics")
        .table("kpi_master")
        .select("kpi_id,kpi_code,kpi_version")
        .in_("kpi_code", list(values))
        .eq("is_active", True)
        .execute()
        .data
    )
    master_by_code = {m["kpi_code"]: m for m in masters}
    missing = sorted(set(values) - set(master_by_code))
    if missing:
        raise RuntimeError(f"Missing EB KPI master records: {missing}. Run the EB KPI SQL seed first.")

    inserted = []
    for code, (value, unit) in values.items():
        master = master_by_code[code]
        row = {
            "kpi_id": master["kpi_id"],
            "kpi_code": code,
            "kpi_version": master.get("kpi_version") or "1.0",
            "period_start": period_start,
            "period_end": period_end,
            "value": value,
            "unit": unit,
            "status": "OK" if value is not None else "INSUFFICIENT_DATA",
            "reason": {
                "source_type": "EB",
                "source_rule": {
                    "EB-CONS-D": "SUM validated energy_readings.eb.interval_kwh; EXCEPTION rows excluded",
                    "EB-KVAH-D": "SUM validated energy_readings.eb.interval_kvah; EXCEPTION rows excluded",
                    "EB-PF-D": "AVERAGE validated EB PF; EXCEPTION rows excluded",
                    "EB-KWH-KVAH": "EB-CONS-D / EB-KVAH-D",
                }[code],
                "normalized_row_count": len(readings),
                "valid_source_reading_ids": source_ids,
                "excluded_exception_reading_ids": [str(r["reading_id"]) for r in excluded],
            },
            "calculation_version": calculation_version,
            "source_reading_count": len(valid),
            "source_reading_ids": source_ids,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }

        existing = (
            db.schema("energy_analytics")
            .table("kpi_result")
            .select("kpi_result_id")
            .eq("kpi_id", master["kpi_id"])
            .eq("period_start", period_start)
            .eq("period_end", period_end)
            .limit(1)
            .execute()
            .data
        )
        if existing:
            db.schema("energy_analytics").table("kpi_result").update(row).eq("kpi_result_id", existing[0]["kpi_result_id"]).execute()
            result_id = existing[0]["kpi_result_id"]
            action = "UPDATED"
        else:
            result_id = db.schema("energy_analytics").table("kpi_result").insert(row).execute().data[0]["kpi_result_id"]
            action = "INSERTED"
        inserted.append({"kpi_code": code, "result_id": result_id, "action": action, "value": value, "unit": unit})

    return {
        "batch_id": batch_id,
        "normalized_rows": len(readings),
        "valid_source_rows": len(valid),
        "exception_rows_excluded": len(excluded),
        "results": inserted,
        "source_reading_ids": source_ids,
        "excluded_exception_reading_ids": [str(r["reading_id"]) for r in excluded],
        "calculation_version": calculation_version,
    }
