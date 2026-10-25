from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


KPI_SPECS = [
    ("SOL-GEN-D", "Solar Daily Generation", "kWh"),
    ("SOL-AVAIL-D", "Solar Reporting Availability", "%"),
]


def _batch_rows(db: Any, batch_id: str) -> list[dict[str, Any]]:
    files = (
        db.schema("energy_import")
        .table("import_file")
        .select("import_file_id")
        .eq("import_batch_id", batch_id)
        .execute()
        .data
    )
    ids = [x["import_file_id"] for x in files]
    if not ids:
        return []
    return (
        db.schema("energy_import")
        .table("import_row")
        .select("import_row_id")
        .in_("import_file_id", ids)
        .execute()
        .data
    )


def calculate_solar_kpis_from_normalized(
    readings: list[dict[str, Any]], batch_id: str = "LOCAL", calculation_version: str = "5.5.0"
) -> dict[str, Any]:
    """Calculate Solar KPIs purely in-memory from normalized reading dicts for audit and speed."""
    valid = [r for r in readings if r.get("data_quality_status") == "VALID"]
    excluded = [r for r in readings if r.get("data_quality_status") != "VALID"]
    source_ids = [str(r.get("reading_id", r.get("import_row_id", ""))) for r in valid]

    generation = sum(
        float(r["interval_kwh"]) for r in valid if r.get("interval_kwh") is not None
    )
    availability = (len(valid) / len(readings) * 100.0) if readings else 0.0

    values = {
        "SOL-GEN-D": (generation, "kWh"),
        "SOL-AVAIL-D": (availability, "%"),
    }

    period_start = readings[0].get("reading_datetime") if readings else datetime.now(timezone.utc).isoformat()
    period_end = readings[-1].get("reading_datetime") if readings else datetime.now(timezone.utc).isoformat()

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
        "period_start": period_start,
        "period_end": period_end,
        "results": results,
        "source_reading_ids": source_ids,
        "calculation_version": calculation_version,
    }


def calculate_solar_kpis(db: Any, batch_id: str, calculation_version: str = "5.5.0") -> dict[str, Any]:
    """Calculate and persist Solar KPIs for a given import batch in Supabase."""
    rows = _batch_rows(db, batch_id)
    ids = [r["import_row_id"] for r in rows]
    if not ids:
        raise ValueError("No import rows found for batch.")

    readings = (
        db.schema("energy_readings")
        .table("solar")
        .select("*")
        .in_("import_row_id", ids)
        .order("reading_datetime")
        .execute()
        .data
    )
    if not readings:
        raise ValueError("No normalized Solar readings found for batch.")

    summary = calculate_solar_kpis_from_normalized(readings, batch_id, calculation_version)
    valid = [r for r in readings if r.get("data_quality_status") == "VALID"]
    source_ids = summary["source_reading_ids"]
    period_start = summary["period_start"]
    period_end = summary["period_end"]

    values = {r["kpi_code"]: (r["value"], r["unit"]) for r in summary["results"]}

    masters = (
        db.schema("energy_analytics")
        .table("kpi_master")
        .select("kpi_id,kpi_code,kpi_version")
        .in_("kpi_code", list(values))
        .execute()
        .data
    )
    master_by_code = {m["kpi_code"]: m for m in masters}

    inserted = []
    for code, (value, unit) in values.items():
        master = master_by_code.get(code)
        master_id = master["kpi_id"] if master else None
        master_ver = master.get("kpi_version", "1.0") if master else "1.0"

        trace = {
            "phase": "5.5",
            "batch_id": batch_id,
            "source_type": "SOLAR",
            "source_rule": {
                "SOL-GEN-D": "SUM validated energy_readings.solar.interval_kwh; EXCEPTION rows excluded",
                "SOL-AVAIL-D": "COUNT(VALID) / COUNT(TOTAL) * 100",
            }.get(code, ""),
            "normalized_row_count": len(readings),
            "valid_source_reading_ids": source_ids,
            "excluded_exception_reading_ids": [
                str(r["reading_id"]) for r in readings if r.get("data_quality_status") != "VALID"
            ],
        }

        row = {
            "kpi_id": master_id,
            "kpi_code": code,
            "kpi_version": master_ver,
            "period_start": period_start,
            "period_end": period_end,
            "value": value,
            "unit": unit,
            "status": "OK" if value is not None else "INSUFFICIENT_DATA",
            "calculation_version": calculation_version,
            "source_reading_count": len(valid),
            "source_reading_ids": source_ids,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
            "reason": str(trace),
        }

        if master_id:
            existing = (
                db.schema("energy_analytics")
                .table("kpi_result")
                .select("kpi_result_id")
                .eq("kpi_id", master_id)
                .eq("period_start", period_start)
                .eq("period_end", period_end)
                .limit(1)
                .execute()
                .data
            )
            if existing:
                db.schema("energy_analytics").table("kpi_result").update(row).eq(
                    "kpi_result_id", existing[0]["kpi_result_id"]
                ).execute()
                row["kpi_result_id"] = existing[0]["kpi_result_id"]
                action = "UPDATED"
            else:
                res = db.schema("energy_analytics").table("kpi_result").insert(row).execute().data[0]
                row["kpi_result_id"] = res["kpi_result_id"]
                action = "INSERTED"
        else:
            action = "CALCULATED_LOCAL"
            row["kpi_result_id"] = None

        inserted.append({
            "kpi_code": code,
            "result_id": row.get("kpi_result_id"),
            "action": action,
            "value": value,
            "unit": unit,
        })

    summary["results"] = inserted
    return summary
