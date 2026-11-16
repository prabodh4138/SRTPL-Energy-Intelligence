"""Read-only Module 7 analytics API backed by the versioned SQL views."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any
import os
import sys

ACTIVE_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "active_app"))
if ACTIVE_APP_DIR not in sys.path:
    sys.path.insert(0, ACTIVE_APP_DIR)

from core.supabase_manager import get_supabase_client
from backend.services.module7_baseline import fetch_in_memory_rows

PAGE_SIZE = 1000
MAX_SUMMARY_ROWS = 50000
MAX_DETAIL_ROWS = 10000
MAX_EXCEPTION_ROWS = 250
MAX_LATEST_ROWS = 500

MODULES: dict[str, dict[str, Any]] = {
    "DG": {
        "source_type": "DG",
        "daily": "vw_dg71_daily_summary",
        "trend_field": "confirmed_generation_kwh",
        "trend_label": "Confirmed generation (kWh)",
        "sum_fields": (
            "confirmed_generation_kwh", "validated_runtime_minutes",
            "efficiency_runtime_minutes", "efficiency_generation_kwh",
            "confirmed_diesel_consumption_l", "reported_diesel_topup_l",
            "net_calculated_fuel_movement_l", "eligible_entry_delay_sum_seconds",
        ),
        "weighted_fields": {
            "average_pf": ("valid_pf_sum", "valid_pf_count"),
            "average_voltage_imbalance_pct": ("valid_voltage_imbalance_sum", "valid_voltage_imbalance_count"),
            "average_current_imbalance_pct": ("valid_current_imbalance_sum", "valid_current_imbalance_count"),
        },
    },
    "EB": {
        "source_type": "EB",
        "daily": "vw_eb71_daily_summary",
        "trend_field": "valid_interval_kwh",
        "trend_label": "Valid interval energy (kWh)",
        "sum_fields": ("valid_interval_kwh", "valid_interval_kvah", "valid_interval_kvarh"),
        "weighted_fields": {"average_pf": ("valid_pf_sum", "valid_pf_count")},
    },
    "SOLAR": {
        "source_type": "SOLAR",
        "daily": "vw_sol71_daily_summary",
        "trend_field": "valid_generation_kwh",
        "trend_label": "Valid generation (kWh)",
        "sum_fields": (
            "valid_generation_kwh", "valid_generation_interval_count",
            "reported_vs_cumulative_delta_sum_kwh",
        ),
        "weighted_fields": {
            "average_generation_interval_kwh": ("valid_generation_kwh", "valid_generation_interval_count"),
        },
    },
    "TRANSFORMER": {
        "source_type": "TRANSFORMER",
        "daily": "vw_trf71_daily_summary",
        "trend_field": "average_primary_voltage_imbalance_pct",
        "trend_label": "Primary voltage imbalance (%)",
        "sum_fields": (),
        "weighted_fields": {
            "average_pf": ("valid_pf_sum", "valid_pf_count"),
            "average_frequency_hz": ("valid_frequency_sum", "valid_frequency_count"),
            "average_oil_temperature_c": ("valid_oil_temperature_sum", "valid_oil_temperature_count"),
            "average_winding_temperature_c": ("valid_winding_temperature_sum", "valid_winding_temperature_count"),
            "average_primary_voltage_imbalance_pct": ("valid_primary_voltage_imbalance_sum", "valid_primary_voltage_imbalance_count"),
            "average_secondary_voltage_imbalance_pct": ("valid_secondary_voltage_imbalance_sum", "valid_secondary_voltage_imbalance_count"),
            "average_primary_current_imbalance_pct": ("valid_primary_current_imbalance_sum", "valid_primary_current_imbalance_count"),
            "average_secondary_current_imbalance_pct": ("valid_secondary_current_imbalance_sum", "valid_secondary_current_imbalance_count"),
        },
    },
    "UPS": {
        "source_type": "UPS",
        "daily": "vw_ups71_daily_summary",
        "trend_field": "average_output_voltage",
        "trend_label": "Average output voltage (V)",
        "sum_fields": (),
        "weighted_fields": {
            "average_output_voltage": ("valid_output_voltage_sum", "valid_output_voltage_count"),
            "average_output_current": ("valid_output_current_sum", "valid_output_current_count"),
            "average_output_frequency": ("valid_output_frequency_sum", "valid_output_frequency_count"),
            "average_battery_vdc": ("valid_battery_vdc_sum", "valid_battery_vdc_count"),
            "average_battery_temperature": ("valid_battery_temperature_sum", "valid_battery_temperature_count"),
            "average_rectifier_voltage": ("valid_rectifier_voltage_sum", "valid_rectifier_voltage_count"),
        },
    },
}

SHARED_VIEWS = (
    "vw_m7_entry_audit",
    "vw_m7_exception_register",
    "vw_m7_asset_latest_reading",
)


def _number(value: Any) -> float:
    try:
        return float(value) if value is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def _is_production_runtime() -> bool:
    """Prevent production analytics from presenting a stale local SQLite mirror."""
    return (
        os.getenv("APP_ENV", "").strip().lower() in {"prod", "production"}
        or os.getenv("RENDER", "").strip().lower() == "true"
        or bool(os.getenv("RENDER_SERVICE_ID", "").strip())
    )


def _views_unavailable(module_name: str, required: list[str], *, exc: Exception | None = None,
                       reason: str | None = None) -> dict[str, Any]:
    code = getattr(exc, "code", None) if exc is not None else None
    return {
        "module": module_name,
        "status": "SQL_VIEWS_UNAVAILABLE",
        "message": (
            "Module 7 could not read the live analytics views. No stale local fallback was used. "
            "Run the read-only preflight, deploy the five submodule view files, then deploy the unified views."
        ),
        "required_views": required,
        "database_error_code": str(code or reason or "SUPABASE_QUERY_FAILED"),
        "has_data": False,
    }


def _query(client: Any, view: str, module: dict[str, Any], plaza_id: str,
           date_from: date | None, date_to: date | None, order_by: str | None,
           descending: bool) -> Any:
    query = client.table(view).select("*")
    if view in SHARED_VIEWS:
        query = query.eq("source_type", module["source_type"])
    if plaza_id != "ALL":
        query = query.eq("plaza_id", plaza_id)
    if date_from:
        query = query.gte("operational_date", date_from.isoformat())
    if date_to:
        query = query.lte("operational_date", date_to.isoformat())
    if order_by:
        query = query.order(order_by, desc=descending)
    return query


def _fetch_rows(client: Any, view: str, module: dict[str, Any], plaza_id: str,
                date_from: date | None, date_to: date | None, *, max_rows: int,
                order_by: str | None = None, descending: bool = False) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    for offset in range(0, max_rows, PAGE_SIZE):
        batch_size = min(PAGE_SIZE, max_rows - offset)
        response = _query(client, view, module, plaza_id, date_from, date_to,
                          order_by, descending).range(offset, offset + batch_size - 1).execute()
        page = response.data or []
        rows.extend(page)
        if len(page) < batch_size:
            return rows, False
    return rows, True


def _sum(rows: list[dict[str, Any]], key: str) -> float:
    return sum(_number(row.get(key)) for row in rows)


def _weighted(rows: list[dict[str, Any]], sum_key: str, count_key: str) -> float | None:
    count = _sum(rows, count_key)
    return _sum(rows, sum_key) / count if count else None


def _period_label(row: dict[str, Any], period: str) -> str:
    if period == "daily":
        value = row.get("operational_date")
    elif period == "monthly":
        value = row.get("operational_month")
        if value is None and row.get("operational_date"):
            value = str(row["operational_date"])[:7]
    else:
        value = row.get("operational_year")
        if value is None and row.get("operational_date"):
            value = str(row["operational_date"])[:4]
    return str(value) if value is not None else "Unknown"


def _aggregate_trends(rows: list[dict[str, Any]], module: dict[str, Any],
                      period: str) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[_period_label(row, period)].append(row)
    output = []
    for label in sorted(buckets):
        group = buckets[label]
        total = int(_sum(group, "total_records"))
        valid = int(_sum(group, "valid_records"))
        exception = int(_sum(group, "exception_records"))
        field = module["trend_field"]
        if field in module["weighted_fields"]:
            sum_key, count_key = module["weighted_fields"][field]
            value = _weighted(group, sum_key, count_key)
        else:
            value = _sum(group, field)
        output.append({
            "period": label,
            "total_records": total,
            "valid_records": valid,
            "exception_records": exception,
            "reconciliation_difference": total - valid - exception,
            "metric_value": value,
            "metric_label": module["trend_label"],
        })
    return output


def _build_summary(rows: list[dict[str, Any]], module: dict[str, Any]) -> dict[str, Any]:
    total = int(_sum(rows, "total_records"))
    valid = int(_sum(rows, "valid_records"))
    exception = int(_sum(rows, "exception_records"))
    counts: dict[str, int] = {}
    for row in rows:
        for key, value in row.items():
            if key.endswith("_count") and value is not None:
                counts[key] = counts.get(key, 0) + int(_number(value))

    metrics: dict[str, Any] = {key: _sum(rows, key) for key in module["sum_fields"]}
    for key, (sum_key, count_key) in module["weighted_fields"].items():
        metrics[key] = _weighted(rows, sum_key, count_key)

    if module["source_type"] == "DG":
        runtime = _sum(rows, "efficiency_runtime_minutes")
        generation = _sum(rows, "efficiency_generation_kwh")
        diesel = _sum(rows, "confirmed_diesel_consumption_l")
        metrics["diesel_l_per_runtime_hour"] = diesel / (runtime / 60.0) if runtime else None
        metrics["diesel_l_per_kwh"] = diesel / generation if generation else None
        metrics["generation_kwh_per_l"] = generation / diesel if diesel else None
        voltage_max = [row.get("max_voltage_imbalance_pct") for row in rows if row.get("max_voltage_imbalance_pct") is not None]
        current_max = [row.get("max_current_imbalance_pct") for row in rows if row.get("max_current_imbalance_pct") is not None]
        metrics["maximum_voltage_imbalance_pct"] = max((_number(value) for value in voltage_max), default=None)
        metrics["maximum_current_imbalance_pct"] = max((_number(value) for value in current_max), default=None)
    elif module["source_type"] == "EB":
        kvah = _sum(rows, "valid_interval_kvah")
        metrics["kwh_to_kvah_ratio"] = _sum(rows, "valid_interval_kwh") / kvah if kvah else None
        demands = [_number(row["maximum_recorded_demand"]) for row in rows if row.get("maximum_recorded_demand") is not None]
        metrics["maximum_recorded_demand"] = max(demands) if demands else None
    elif module["source_type"] == "UPS":
        metrics["observed_record_availability_pct"] = 100.0 * valid / total if total else None

    metrics.update(counts)
    return {
        "total_records": total,
        "valid_records": valid,
        "exception_records": exception,
        "reconciliation_difference": total - valid - exception,
        "observed_record_availability_pct": 100.0 * valid / total if total else None,
        "exception_percentage": 100.0 * exception / total if total else None,
        "delayed_entry_count": counts.get("delayed_entry_count", 0),
        "entry_delay_eligible_count": counts.get("entry_delay_eligible_count", 0),
        "night_reading_count": counts.get("night_reading_count", 0),
        "night_entry_count": counts.get("night_entry_count", 0),
        "negative_entry_delay_timestamp_anomaly_count": counts.get("negative_entry_delay_timestamp_anomaly_count", 0),
        "quality_counts": counts,
        "kpis": metrics,
    }


def _fetch_correction_rows(client: Any, module: dict[str, Any], plaza_id: str,
                           date_from: date | None, date_to: date | None) -> list[dict[str, Any]]:
    query = client.table("vw_m7_correction_audit").select("*")
    query = query.eq("source_type", module["source_type"])
    if plaza_id != "ALL":
        query = query.eq("plaza_id", plaza_id)
    if date_from:
        query = query.gte("audit_timestamp", date_from.isoformat())
    if date_to:
        query = query.lte("audit_timestamp", date_to.isoformat() + "T23:59:59.999999")
    response = query.order("audit_timestamp", desc=True).limit(MAX_EXCEPTION_ROWS).execute()
    return response.data or []


def _technician_summary(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in entries:
        name = (row.get("created_by") or "").strip() or "Unassigned"
        item = grouped.setdefault(name, {
            "technician_name": name, "total_records": 0, "valid_records": 0,
            "exception_records": 0, "delayed_entry_count": 0,
            "night_reading_count": 0, "night_entry_count": 0,
        })
        item["total_records"] += 1
        quality = str(row.get("analytics_quality_class") or "").upper()
        item["valid_records"] += int(quality == "VALID")
        item["exception_records"] += int(quality == "EXCEPTION")
        item["delayed_entry_count"] += int(row.get("delayed_entry_24h_or_more") is True)
        item["night_reading_count"] += int(row.get("reading_datetime_night_indicator") is True)
        item["night_entry_count"] += int(row.get("created_on_night_indicator") is True)
    return sorted(grouped.values(), key=lambda item: item["total_records"], reverse=True)


def get_module7_analytics(module_name: str, plaza_id: str = "ALL", period: str = "daily",
                         date_from: str | None = None, date_to: str | None = None) -> dict[str, Any]:
    """Fetch filtered Module 7 summaries and detail from SQL views only."""
    name = module_name.strip().upper()
    if name not in MODULES:
        raise ValueError("module_name must be DG, EB, SOLAR, TRANSFORMER, or UPS")
    if period not in ("daily", "monthly", "yearly"):
        raise ValueError("period must be daily, monthly, or yearly")
    if plaza_id != "ALL" and not plaza_id.strip():
        raise ValueError("plaza_id must be ALL or a plaza identifier")
    start = date.fromisoformat(date_from) if date_from else None
    end = date.fromisoformat(date_to) if date_to else None
    if start and end and start > end:
        raise ValueError("date_from must be on or before date_to")

    module = MODULES[name]
    required = [module["daily"], *SHARED_VIEWS]
    client = get_supabase_client()
    if client:
        try:
            summary_rows, summary_truncated = _fetch_rows(
                client, module["daily"], module, plaza_id, start, end,
                max_rows=MAX_SUMMARY_ROWS, order_by="operational_date",
            )
            latest_rows, latest_truncated = _fetch_rows(
                client, "vw_m7_asset_latest_reading", module, plaza_id, None, None,
                max_rows=MAX_LATEST_ROWS, order_by="reading_datetime", descending=True,
            )
            entry_rows, entries_truncated = _fetch_rows(
                client, "vw_m7_entry_audit", module, plaza_id, start, end,
                max_rows=MAX_DETAIL_ROWS, order_by="reading_datetime", descending=True,
            )
            exception_rows, exceptions_truncated = _fetch_rows(
                client, "vw_m7_exception_register", module, plaza_id, start, end,
                max_rows=MAX_EXCEPTION_ROWS, order_by="reading_datetime", descending=True,
            )
            try:
                corrections = _fetch_correction_rows(client, module, plaza_id, start, end)
                correction_audit_available = True
            except Exception:
                corrections = []
                correction_audit_available = False
        except Exception as exc:
            # A configured Supabase source that fails must not be hidden by older local data.
            return _views_unavailable(name, required, exc=exc)
    else:
        # In-memory baseline provider (zero SQLite database reliance)
        try:
            summary_rows, summary_truncated = fetch_in_memory_rows(
                name, module["daily"], plaza_id, start, end,
                max_rows=MAX_SUMMARY_ROWS, order_by="operational_date",
            )
            latest_rows, latest_truncated = fetch_in_memory_rows(
                name, "vw_m7_asset_latest_reading", plaza_id, None, None,
                max_rows=MAX_LATEST_ROWS, order_by="reading_datetime", descending=True,
            )
            entry_rows, entries_truncated = fetch_in_memory_rows(
                name, "vw_m7_entry_audit", plaza_id, start, end,
                max_rows=MAX_DETAIL_ROWS, order_by="reading_datetime", descending=True,
            )
            exception_rows, exceptions_truncated = fetch_in_memory_rows(
                name, "vw_m7_exception_register", plaza_id, start, end,
                max_rows=MAX_EXCEPTION_ROWS, order_by="reading_datetime", descending=True,
            )
            corrections = []
            correction_audit_available = False
        except Exception as exc:
            return _views_unavailable(name, required, exc=exc)

    summary = _build_summary(summary_rows, module)
    total = summary["total_records"]
    return {
        "module": name, "status": "READY",
        "message": None if total else f"No readings found for {name} in the selected filters.",
        "has_data": total > 0, "period": period,
        "filters": {
            "plaza_id": plaza_id,
            "date_from": start.isoformat() if start else None,
            "date_to": end.isoformat() if end else None,
        },
        "summary": summary,
        "daily_trends": _aggregate_trends(summary_rows, module, period),
        "latest_readings": latest_rows,
        "entry_audit": entry_rows[:500],
        "night_entries": [
            row for row in entry_rows
            if row.get("reading_datetime_night_indicator") is True
            or row.get("created_on_night_indicator") is True
        ][:250],
        "exceptions": exception_rows[:MAX_EXCEPTION_ROWS],
        "corrections": corrections,
        "correction_audit_available": correction_audit_available,
        "technicians": _technician_summary(entry_rows),
        "limits": {
            "summary_truncated": summary_truncated,
            "entry_audit_truncated": entries_truncated,
            "exceptions_truncated": exceptions_truncated,
            "latest_readings_truncated": latest_truncated,
        },
        "night_window": {
            "timezone": "Asia/Kolkata", "start_inclusive": "22:00",
            "end_exclusive": "06:00", "classification": "indicator only",
        },
        "required_views": required,
    }
