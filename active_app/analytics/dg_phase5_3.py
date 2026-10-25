from __future__ import annotations
from datetime import datetime, timezone

KPI_SPECS = [
    ("DG-GEN-D", "Daily DG Generation", "kWh"),
    ("DG-RUN-D", "DG Runtime", "hour"),
    ("DG-KWH-HR", "DG Energy per Runtime Hour", "kWh/hour"),
    ("DG-PF", "DG Average Power Factor", "PF"),
]


def calculate_dg_kpis_from_normalized(
    readings: list[dict], batch_id: str = "LOCAL", calculation_version: str = "5.3.0"
) -> dict:
    """Calculate DG KPIs purely in-memory from normalized reading dicts for audit and speed."""
    valid = [r for r in readings if r.get("data_quality_status") == "VALID"]
    excluded = [r for r in readings if r.get("data_quality_status") != "VALID"]
    source_ids = [str(r.get("reading_id", r.get("import_row_id", ""))) for r in valid]

    generation = sum(float(r["interval_kwh"]) for r in valid if r.get("interval_kwh") is not None)
    runtime = sum(float(r["interval_running_hours"]) for r in valid if r.get("interval_running_hours") is not None)
    pf_values = [float(r["pf"]) for r in valid if r.get("pf") is not None]
    pf_avg = sum(pf_values) / len(pf_values) if pf_values else None

    values = {
        "DG-GEN-D": (generation, "kWh"),
        "DG-RUN-D": (runtime, "hour"),
        "DG-KWH-HR": (generation / runtime if runtime else None, "kWh/hour"),
        "DG-PF": (pf_avg, "PF"),
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
        return db.table("import_row").select("import_row_id").in_("import_file_id", ids).execute().data
    except Exception:
        try:
            return db.schema("energy_import").table("import_row").select("import_row_id").in_("import_file_id", ids).execute().data
        except Exception:
            return []


def calculate_dg_kpis(db, batch_id, calculation_version="5.3"):
    rows = _batch_rows(db, batch_id)
    ids = [r["import_row_id"] for r in rows]
    if not ids:
        raise ValueError("No import rows found for batch.")
    readings = db.schema("energy_readings").table("dg").select("*").in_("import_row_id", ids).order("reading_datetime").execute().data
    valid = [r for r in readings if r.get("data_quality_status") == "VALID"]
    source_ids = [str(r["reading_id"]) for r in valid]
    generation = sum(float(r["interval_kwh"]) for r in valid if r.get("interval_kwh") is not None)
    runtime = sum(float(r["interval_running_hours"]) for r in valid if r.get("interval_running_hours") is not None)
    pf_values = [float(r["pf"]) for r in valid if r.get("pf") is not None]
    pf_avg = sum(pf_values) / len(pf_values) if pf_values else None
    values = {
        "DG-GEN-D": (generation, "kWh"),
        "DG-RUN-D": (runtime, "hour"),
        "DG-KWH-HR": (generation / runtime if runtime else None, "kWh/hour"),
        "DG-PF": (pf_avg, "PF"),
    }
    if readings:
        period_start = readings[0]["reading_datetime"]
        period_end = readings[-1]["reading_datetime"]
    else:
        now = datetime.now(timezone.utc).isoformat()
        period_start = period_end = now

    masters = db.schema("energy_analytics").table("kpi_master").select("kpi_id,kpi_code").in_("kpi_code", list(values)).execute().data
    master_by_code = {m["kpi_code"]: m["kpi_id"] for m in masters}
    if len(master_by_code) != len(values):
        missing = sorted(set(values) - set(master_by_code))
        raise RuntimeError(f"Missing DG KPI master records: {missing}")

    inserted = []
    for code, (value, unit) in values.items():
        trace = {
            "phase": "5.3",
            "batch_id": batch_id,
            "source_type": "DG",
            "source_rule": {
                "DG-GEN-D": "SUM validated interval_kwh",
                "DG-RUN-D": "SUM validated interval_running_hours",
                "DG-KWH-HR": "SUM validated interval_kwh / SUM validated interval_running_hours",
                "DG-PF": "AVERAGE validated PF",
            }[code],
            "normalized_row_count": len(readings),
            "valid_source_reading_ids": source_ids,
            "excluded_exception_reading_ids": [str(r["reading_id"]) for r in readings if r.get("data_quality_status") != "VALID"],
        }
        row = {
            "kpi_id": master_by_code[code],
            "period_start": period_start,
            "period_end": period_end,
            "value": value,
            "unit": unit,
            "status": "OK" if value is not None else "INSUFFICIENT_DATA",
            "calculation_version": calculation_version,
            "source_record_count": len(valid),
            "calculated_at": datetime.now(timezone.utc).isoformat(),
            "trace": trace,
        }
        existing = db.schema("energy_analytics").table("kpi_result").select("kpi_result_id").eq("kpi_id", master_by_code[code]).eq("period_start", period_start).eq("period_end", period_end).limit(1).execute().data
        if existing:
            db.schema("energy_analytics").table("kpi_result").update(row).eq("kpi_result_id", existing[0]["kpi_result_id"]).execute()
            row["kpi_result_id"] = existing[0]["kpi_result_id"]
            action = "UPDATED"
        else:
            result = db.schema("energy_analytics").table("kpi_result").insert(row).execute().data[0]
            row["kpi_result_id"] = result["kpi_result_id"]
            action = "INSERTED"
        inserted.append({"kpi_code": code, "result_id": row["kpi_result_id"], "action": action, "value": value, "unit": unit})
    return {"batch_id": batch_id, "normalized_rows": len(readings), "valid_source_rows": len(valid), "exception_rows_excluded": len(readings)-len(valid), "results": inserted, "source_reading_ids": source_ids, "calculation_version": calculation_version}
