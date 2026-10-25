from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _calc_imbalance(v1: Any, v2: Any, v3: Any) -> float | None:
    try:
        vals = [float(v) for v in (v1, v2, v3) if v is not None]
    except (TypeError, ValueError):
        return None
    if len(vals) != 3:
        return None
    avg = sum(vals) / 3.0
    if avg == 0:
        return 0.0
    return max(abs(v - avg) for v in vals) / avg * 100.0


def calculate_transformer_kpis_from_normalized(
    readings: list[dict[str, Any]], batch_id: str = "LOCAL", calculation_version: str = "5.6.0"
) -> dict[str, Any]:
    """Calculate Transformer KPIs purely in-memory from normalized readings for audit and speed."""
    valid = [r for r in readings if r.get("data_quality_status") == "VALID"]
    excluded = [r for r in readings if r.get("data_quality_status") != "VALID"]
    source_ids = [str(r.get("reading_id", r.get("import_row_id", ""))) for r in valid]

    pv_imbalances = [
        _calc_imbalance(r.get("primary_v_ry"), r.get("primary_v_yb"), r.get("primary_v_br"))
        for r in valid
    ]
    pv_imb_vals = [v for v in pv_imbalances if v is not None]
    max_pv_imb = max(pv_imb_vals) if pv_imb_vals else None

    sv_imbalances = [
        _calc_imbalance(r.get("secondary_v_ry"), r.get("secondary_v_yb"), r.get("secondary_v_br"))
        for r in valid
    ]
    sv_imb_vals = [v for v in sv_imbalances if v is not None]
    max_sv_imb = max(sv_imb_vals) if sv_imb_vals else None

    pi_imbalances = [
        _calc_imbalance(r.get("primary_i_r"), r.get("primary_i_y"), r.get("primary_i_b"))
        for r in valid
    ]
    pi_imb_vals = [v for v in pi_imbalances if v is not None]
    max_pi_imb = max(pi_imb_vals) if pi_imb_vals else None

    si_imbalances = [
        _calc_imbalance(r.get("secondary_i_r"), r.get("secondary_i_y"), r.get("secondary_i_b"))
        for r in valid
    ]
    si_imb_vals = [v for v in si_imbalances if v is not None]
    max_si_imb = max(si_imb_vals) if si_imb_vals else None

    pf_vals = []
    for r in valid:
        try:
            if r.get("pf") is not None:
                pf_vals.append(float(r["pf"]))
        except (TypeError, ValueError):
            pass
    avg_pf = (sum(pf_vals) / len(pf_vals)) if pf_vals else None

    oti_vals = []
    for r in valid:
        try:
            if r.get("oti") is not None:
                oti_vals.append(float(r["oti"]))
        except (TypeError, ValueError):
            pass
    max_oti = max(oti_vals) if oti_vals else None

    wti_vals = []
    for r in valid:
        try:
            if r.get("wti") is not None:
                wti_vals.append(float(r["wti"]))
        except (TypeError, ValueError):
            pass
    max_wti = max(wti_vals) if wti_vals else None

    values = {
        "TR-VI-01": (max_pv_imb, "%"),
        "TR-CI-01": (max_pi_imb, "%"),
        "TRF-SV-IMB": (max_sv_imb, "%"),
        "TRF-SI-IMB": (max_si_imb, "%"),
        "TRF-PF": (avg_pf, "PF"),
        "TRF-MAX-OTI": (max_oti, "°C"),
        "TRF-MAX-WTI": (max_wti, "°C"),
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
        "audit_note": (
            "Transformer loss/efficiency is intentionally disabled until measurement "
            "boundaries, CT/PT ratios, and meter ratings are formally confirmed."
        ),
    }


def calculate_transformer_kpis(
    db: Any, batch_id: str, calculation_version: str = "5.6.0"
) -> dict[str, Any]:
    """Calculate and persist Transformer KPIs in Supabase with full audit traceability."""
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
        return {"batch_id": batch_id, "results": []}

    rows = (
        db.schema("energy_import")
        .table("import_row")
        .select("import_row_id")
        .in_("import_file_id", ids)
        .execute()
        .data
    )
    row_ids = [r["import_row_id"] for r in rows]
    if not row_ids:
        raise ValueError("No import rows found for batch.")

    readings = (
        db.schema("energy_readings")
        .table("transformer")
        .select("*")
        .in_("import_row_id", row_ids)
        .order("reading_datetime")
        .execute()
        .data
    )
    if not readings:
        raise ValueError("No normalized Transformer readings found for batch.")

    summary = calculate_transformer_kpis_from_normalized(readings, batch_id, calculation_version)
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
            "phase": "5.6",
            "batch_id": batch_id,
            "source_type": "TRANSFORMER",
            "source_rule": f"Calculated from valid transformer readings; EXCEPTION rows excluded; code={code}",
            "normalized_row_count": len(readings),
            "valid_source_reading_ids": source_ids,
            "excluded_exception_reading_ids": [
                str(r["reading_id"]) for r in readings if r.get("data_quality_status") != "VALID"
            ],
            "loss_efficiency_status": "DISABLED_PENDING_CONFIRMATION",
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
