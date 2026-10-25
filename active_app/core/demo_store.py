"""Demo & Local Offline Store for SRTPL Energy Intelligence.

Provides realistic baseline data derived from the 21 real JUNO CSV files
under source_data/raw/ across all 5 energy modules (EB, DG, Solar, Transformer, UPS).
Allows immediate end-to-end evaluation of all dashboards, reports, and exception
workflows before staging/production Supabase credentials are wired.
Can be toggled off or cleared with a single click.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]


def is_demo_mode() -> bool:
    """Return True if demo mode is enabled in the active Streamlit session."""
    try:
        return bool(st.session_state.get("demo_mode_active", False))
    except Exception:
        return False


def set_demo_mode(active: bool) -> None:
    st.session_state["demo_mode_active"] = active


def get_sample_csv_path(source_type: str) -> Path | None:
    """Return a real sample JUNO CSV path for the requested source module."""
    raw_dir = ROOT / "source_data" / "raw"
    mapping = {
        "EB": raw_dir / "EB" / "SRTPL_Test_JUNO_EB.csv",
        "DG": raw_dir / "DG" / "DGDailyLogReport_25thSep2026_443_DG Log.csv",
        "SOLAR": raw_dir / "Solar" / "Solar_Plant_Log_25thSep2026_2719_Solar Log.csv",
        "TRANSFORMER": raw_dir / "Transformer" / "TransformerDailyReport_25thSep2026_2116_Transformer Daily Log Report.csv",
        "UPS": raw_dir / "UPS" / "UPSDailyLogReport_25thSep2026_2140_UPS Daily Log Report.csv",
    }
    path = mapping.get(source_type.upper())
    return path if path and path.exists() else None


# ---------------------------------------------------------------------------
# Executive Dashboard Data
# ---------------------------------------------------------------------------

def get_demo_executive_summary(
    from_date: date | None = None,
    to_date: date | None = None,
    plazas: list[str] | None = None,
):
    from dashboard.services import DashboardSummary

    if to_date is None:
        to_date = date.today()
    if from_date is None:
        from_date = to_date - timedelta(days=30)

    num_days = max(1, (to_date - from_date).days + 1)
    scale_factor = num_days / 30.0

    all_demo_exc = get_demo_exceptions()
    def count_plaza_open_exc(plz_code: str) -> int:
        if all_demo_exc.empty:
            return 0
        return len(all_demo_exc[(all_demo_exc["Plaza"] == plz_code) & (all_demo_exc["Status"] == "OPEN")])

    def get_plaza_dq(plz_code: str) -> float:
        open_cnt = count_plaza_open_exc(plz_code)
        if open_cnt == 0:
            return 100.0
        return round(100.0 - (open_cnt * 0.5), 1)

    all_plaza_records = [
        {
            "Plaza": "TP01",
            "EB kWh": round(18200.0 * scale_factor, 1),
            "DG kWh": round(4100.0 * scale_factor, 1),
            "Solar kWh": round(14904.0 * scale_factor, 1),
            "Energy Cost": round(185000.0 * scale_factor, 2),
            "Solar Saving": round(119232.0 * scale_factor, 2),
            "Data Quality %": get_plaza_dq("TP01"),
            "Exceptions": count_plaza_open_exc("TP01"),
        },
        {
            "Plaza": "TP02",
            "EB kWh": round(16500.0 * scale_factor, 1),
            "DG kWh": round(5200.0 * scale_factor, 1),
            "Solar kWh": round(13500.0 * scale_factor, 1),
            "Energy Cost": round(198000.0 * scale_factor, 2),
            "Solar Saving": round(108000.0 * scale_factor, 2),
            "Data Quality %": get_plaza_dq("TP02"),
            "Exceptions": count_plaza_open_exc("TP02"),
        },
        {
            "Plaza": "TP03",
            "EB kWh": round(13550.0 * scale_factor, 1),
            "DG kWh": round(3380.0 * scale_factor, 1),
            "Solar kWh": round(12800.0 * scale_factor, 1),
            "Energy Cost": round(152000.0 * scale_factor, 2),
            "Solar Saving": round(102400.0 * scale_factor, 2),
            "Data Quality %": get_plaza_dq("TP03"),
            "Exceptions": count_plaza_open_exc("TP03"),
        },
    ]

    plaza_df = pd.DataFrame(all_plaza_records)
    if plazas:
        plaza_df = plaza_df[plaza_df["Plaza"].isin(plazas)]

    total_eb = float(plaza_df["EB kWh"].sum()) if not plaza_df.empty else 0.0
    total_dg = float(plaza_df["DG kWh"].sum()) if not plaza_df.empty else 0.0
    total_solar = float(plaza_df["Solar kWh"].sum()) if not plaza_df.empty else 0.0
    total_cost = float(plaza_df["Energy Cost"].sum()) if not plaza_df.empty else 0.0
    total_saving = float(plaza_df["Solar Saving"].sum()) if not plaza_df.empty else 0.0
    total_exc = int(plaza_df["Exceptions"].sum()) if not plaza_df.empty else 0
    avg_dq = float(plaza_df["Data Quality %"].mean()) if not plaza_df.empty else 100.0

    # Generate daily trend matching exact from_date to to_date
    trend_records = []
    curr = from_date
    day_idx = 0
    while curr <= to_date:
        eb_daily = (total_eb / num_days) * (0.9 + 0.2 * ((day_idx % 7) / 7.0))
        dg_daily = (total_dg / num_days) * (0.8 + 0.4 * ((day_idx % 5) / 5.0))
        solar_daily = (total_solar / num_days) * (0.85 + 0.3 * ((day_idx % 4) / 4.0))
        trend_records.append({
            "Date": curr.strftime("%Y-%m-%d"),
            "EB kWh": round(eb_daily, 1),
            "DG kWh": round(dg_daily, 1),
            "Solar kWh": round(solar_daily, 1),
        })
        curr += timedelta(days=1)
        day_idx += 1
    trend_df = pd.DataFrame(trend_records)

    return DashboardSummary(
        total_eb_kwh=round(total_eb, 1),
        total_dg_kwh=round(total_dg, 1),
        total_solar_kwh=round(total_solar, 1),
        eb_cost=round(total_cost, 2),
        dg_cost=round(total_dg * 25.0, 2),
        solar_saving=round(total_saving, 2),
        energy_cost_per_kwh=7.92,
        exception_count=total_exc,
        data_quality_percent=round(avg_dq, 1),
        plaza_rows=plaza_df,
        trend_rows=trend_df,
    )


# ---------------------------------------------------------------------------
# Plaza Dashboard Data
# ---------------------------------------------------------------------------

def get_demo_plaza_dashboard(
    plaza: str,
    from_date: date | None = None,
    to_date: date | None = None,
):
    from plaza.models import PlazaDashboardData

    if to_date is None:
        to_date = date.today()
    if from_date is None:
        from_date = to_date - timedelta(days=30)

    num_days = max(1, (to_date - from_date).days + 1)
    scale_factor = num_days / 30.0

    plaza_metrics = {
        "TP01": {"eb": 18200.0, "dg": 4100.0, "solar": 14904.0, "run": 515.0, "exc": 2, "dq": 99.1},
        "TP02": {"eb": 16500.0, "dg": 5200.0, "solar": 13500.0, "run": 650.0, "exc": 3, "dq": 98.4},
        "TP03": {"eb": 13550.0, "dg": 3380.0, "solar": 12800.0, "run": 420.0, "exc": 2, "dq": 98.3},
    }
    base = plaza_metrics.get(plaza, plaza_metrics["TP01"])
    m = {
        "eb": round(base["eb"] * scale_factor, 1),
        "dg": round(base["dg"] * scale_factor, 1),
        "solar": round(base["solar"] * scale_factor, 1),
        "run": round(base["run"] * scale_factor, 1),
        "exc": max(1, int(round(base["exc"] * scale_factor))),
        "dq": base["dq"],
    }

    # Distinct assets mapped to this specific toll plaza
    asset_mapping = {
        "TP01": [
            ("EB Meter", "SR-E-EM-EB-000TP01", "ONLINE", "Validated interval"),
            ("DG Generator 1", "SR-E-AP-DGX-000001", "STANDBY/READY", "305 logs verified"),
            ("DG Generator 2", "SR-E-AP-DGX-000002", "STANDBY/READY", "394 logs verified"),
            ("Solar Plant 1", "SR-E-AP-SPX-000001", "GENERATING", "4,168 logs verified"),
            ("HT Transformer 2", "SR-E-HT-TFR-000002", "NORMAL", "1,300 logs verified"),
            ("UPS Unit 2", "SR-E-AP-UPS-000002", "ONLINE", "1,673 logs verified"),
            ("UPS Unit 3", "SR-E-AP-UPS-000003", "ONLINE", "1,559 logs verified"),
        ],
        "TP02": [
            ("EB Meter", "SR-E-EM-EB-130-000", "ONLINE", "Validated cumulative"),
            ("DG Generator 3", "SR-E-AP-DGX-000003", "STANDBY/READY", "178 logs verified"),
            ("DG Generator 4", "SR-E-AP-DGX-000004", "STANDBY/READY", "334 logs verified"),
            ("Solar Plant 2", "SR-E-AP-SPX-000002", "GENERATING", "2,719 logs verified"),
            ("HT Transformer 3", "SR-E-HT-TFR-000003", "NORMAL", "252 logs verified"),
            ("UPS Unit 4", "SR-E-AP-UPS-000004", "ONLINE", "1,550 logs verified"),
            ("UPS Unit 9", "SR-E-AP-UPS-000009", "ONLINE", "1,459 logs verified"),
        ],
        "TP03": [
            ("EB Meter", "SRTPL_Test_JUNO_EB", "ONLINE", "Validated test log"),
            ("DG Generator 5", "SR-E-AP-DGX-000005", "STANDBY/READY", "353 logs verified"),
            ("DG Generator 6", "SR-E-AP-DGX-000006", "STANDBY/READY", "396 logs verified"),
            ("Solar Plant 3", "SR-E-AP-SPX-000003", "GENERATING", "2,764 logs verified"),
            ("HT Transformer 1", "SR-E-HT-TFR-000001", "NORMAL", "Verified baseline"),
            ("UPS Unit 10", "SR-E-AP-UPS-000010", "ONLINE", "1,462 logs verified"),
            ("UPS Unit 12", "SR-E-AP-UPS-000012", "ONLINE", "1,368 logs verified"),
        ],
    }

    raw_assets = asset_mapping.get(plaza, asset_mapping["TP01"])
    asset_rows = pd.DataFrame([
        {
            "Asset Type": a[0],
            "Asset": a[1],
            "Status": a[2],
            "Latest Reading": to_date.strftime("%d-%b-%Y 23:59"),
            "Key KPI": a[3],
            "Exceptions": 0,
        }
        for a in raw_assets
    ])

    trend_records = []
    curr = from_date
    day_idx = 0
    while curr <= to_date:
        trend_records.append({
            "Date": curr.strftime("%Y-%m-%d"),
            "EB kWh": round((m['eb'] / num_days) * (0.9 + 0.2 * ((day_idx % 5) / 5.0)), 1),
            "DG kWh": round((m['dg'] / num_days) * (0.8 + 0.4 * ((day_idx % 3) / 3.0)), 1),
            "Solar kWh": round((m['solar'] / num_days) * (0.85 + 0.3 * ((day_idx % 4) / 4.0)), 1),
        })
        curr += timedelta(days=1)
        day_idx += 1
    trend_rows = pd.DataFrame(trend_records)

    all_demo_exc = get_demo_exceptions()
    plaza_open_exc = all_demo_exc[(all_demo_exc["Plaza"] == plaza) & (all_demo_exc["Status"] == "OPEN")]
    if not plaza_open_exc.empty:
        exceptions_df = plaza_open_exc[["Severity", "Rule", "Asset", "Status", "Message"]].copy()
        exceptions_df["Date"] = to_date.strftime("%Y-%m-%d")
        m["exc"] = len(plaza_open_exc)
        m["dq"] = round(100.0 - (len(plaza_open_exc) * 0.5), 1)
    else:
        exceptions_df = pd.DataFrame(columns=["Severity", "Rule", "Asset", "Status", "Message", "Date"])
        m["exc"] = 0
        m["dq"] = 100.0

    return PlazaDashboardData(
        plaza_id=plaza,
        plaza_name=f"Toll Plaza {plaza}",
        eb_kwh=m["eb"],
        dg_kwh=m["dg"],
        solar_kwh=m["solar"],
        eb_cost=round(m["eb"] * 8.0, 2),
        dg_cost=round(m["dg"] * 25.0, 2),
        solar_saving=round(m["solar"] * 8.0, 2),
        energy_cost_per_kwh=7.95,
        dg_runtime=m["run"],
        dg_efficiency=round(m["dg"] / m["run"], 2) if m["run"] else None,
        eb_pf=0.965,
        dg_pf=0.982,
        data_quality=m["dq"],
        exception_count=m["exc"],
        asset_rows=asset_rows,
        trend_rows=trend_rows,
        exceptions=exceptions_df,
    )


# ---------------------------------------------------------------------------
# Equipment Dashboard Data
# ---------------------------------------------------------------------------

ASSETS_BY_TYPE = {
    "EB": ["SR-E-EM-EB-000TP01", "SR-E-EM-EB-130-000", "SRTPL_Test_JUNO_EB"],
    "DG": [
        "SR-E-AP-DGX-000001", "SR-E-AP-DGX-000002", "SR-E-AP-DGX-000003",
        "SR-E-AP-DGX-000004", "SR-E-AP-DGX-000005", "SR-E-AP-DGX-000006"
    ],
    "SOLAR": ["SR-E-AP-SPX-000001", "SR-E-AP-SPX-000002", "SR-E-AP-SPX-000003"],
    "TRANSFORMER": ["SR-E-HT-TFR-000002", "SR-E-HT-TFR-000003"],
    "UPS": [
        "SR-E-AP-UPS-000002", "SR-E-AP-UPS-000003", "SR-E-AP-UPS-000004",
        "SR-E-AP-UPS-000009", "SR-E-AP-UPS-000010", "SR-E-AP-UPS-000012"
    ],
}

ASSET_TO_PLAZA = {
    "SR-E-EM-EB-000TP01": "TP01",
    "SR-E-EM-EB-130-000": "TP02",
    "SRTPL_Test_JUNO_EB": "TP03",
    "SR-E-AP-DGX-000001": "TP01",
    "SR-E-AP-DGX-000002": "TP01",
    "SR-E-AP-DGX-000003": "TP02",
    "SR-E-AP-DGX-000004": "TP02",
    "SR-E-AP-DGX-000005": "TP03",
    "SR-E-AP-DGX-000006": "TP03",
    "SR-E-AP-SPX-000001": "TP01",
    "SR-E-AP-SPX-000002": "TP02",
    "SR-E-AP-SPX-000003": "TP03",
    "SR-E-HT-TFR-000002": "TP01",
    "SR-E-HT-TFR-000003": "TP02",
    "SR-E-AP-UPS-000002": "TP01",
    "SR-E-AP-UPS-000003": "TP01",
    "SR-E-AP-UPS-000004": "TP02",
    "SR-E-AP-UPS-000009": "TP02",
    "SR-E-AP-UPS-000010": "TP03",
    "SR-E-AP-UPS-000012": "TP03",
}


def get_demo_equipment_dashboard(
    source_type: str,
    asset_id: str,
    from_date: date | None = None,
    to_date: date | None = None,
):
    from equipment.models import EquipmentDashboardData

    if to_date is None:
        to_date = date.today()
    if from_date is None:
        from_date = to_date - timedelta(days=30)

    num_days = max(1, (to_date - from_date).days + 1)
    scale = num_days / 30.0

    plaza_id = ASSET_TO_PLAZA.get(asset_id, "TP01")

    kpi_map = {
        "EB": [("EB-CONS-D", round(606.7 * scale, 1), "kWh", "OK"), ("EB-KVAH-D", round(638.6 * scale, 1), "kVAh", "OK"), ("EB-PF-D", 0.95, "PF", "OK")],
        "DG": [("DG-GEN-D", round(683.3 * scale, 1), "kWh", "OK"), ("DG-RUN-D", round(86.0 * scale, 1), "hour", "OK"), ("DG-KWH-HR", 7.95, "kWh/hr", "OK"), ("DG-PF", 0.980, "PF", "OK")],
        "SOLAR": [("SOL-GEN-D", round(496.8 * scale, 1), "kWh", "OK"), ("SOL-AVAIL-D", 100.0, "%", "OK")],
        "TRANSFORMER": [("TR-VI-01", 0.45, "%", "OK"), ("TR-CI-01", 1.82, "%", "OK"), ("TRF-PF", 0.999, "PF", "OK"), ("TRF-MAX-OTI", 24.0, "°C", "OK"), ("TRF-MAX-WTI", 44.0, "°C", "OK")],
        "UPS": [("UPS-AV-01", 100.0, "%", "OK"), ("UPS-V-OUT-AVG", 231.8, "V", "OK"), ("UPS-F-OUT-AVG", 49.97, "Hz", "OK"), ("UPS-BATT-V-AVG", 463.1, "V", "OK")],
    }
    kpi_records = kpi_map.get(source_type.upper(), [("GENERIC-KPI", 100.0, "unit", "OK")])
    kpi_df = pd.DataFrame(kpi_records, columns=["KPI", "Value", "Unit", "Status"])

    latest_df = pd.DataFrame([
        {"Parameter": "Primary Telemetry", "Value": f"{round(100.0 * scale, 1)}", "Unit": "units", "Timestamp": to_date.strftime("%Y-%m-%d 18:00")},
        {"Parameter": "Power Factor", "Value": "0.985", "Unit": "PF", "Timestamp": to_date.strftime("%Y-%m-%d 18:00")},
        {"Parameter": "Operating Status", "Value": "NORMAL / VALIDATED", "Unit": "status", "Timestamp": to_date.strftime("%Y-%m-%d 18:00")},
    ])

    trend_records = []
    curr = from_date
    day_idx = 0
    while curr <= to_date:
        trend_records.append({
            "Timestamp": f"{curr.strftime('%Y-%m-%d')} 12:00",
            "Parameter": "Primary Value",
            "Value": round(100.0 + (day_idx % 6) * 12.0, 1),
        })
        curr += timedelta(days=1)
        day_idx += 1
    trend_df = pd.DataFrame(trend_records)

    exc_df = pd.DataFrame([
        {"Severity": "WARNING", "Rule": f"VAL-{source_type}-001", "Date": to_date.strftime("%Y-%m-%d"), "Status": "OPEN"}
    ])

    param_df = pd.DataFrame([
        {"Parameter": "Active Readings", "Unit": "count", "Source": "JUNO CSV", "Latest Value": f"{num_days * 24} intervals"},
        {"Parameter": "Operating Voltage", "Unit": "V", "Source": "JUNO CSV", "Latest Value": "Verified"},
        {"Parameter": "Power Factor", "Unit": "PF", "Source": "JUNO CSV", "Latest Value": "0.985 (Valid)"},
    ])

    return EquipmentDashboardData(
        source_type=source_type,
        asset_id=asset_id,
        asset_name=f"{asset_id} ({source_type})",
        plaza=f"Toll Plaza {plaza_id}",
        kpis=kpi_df,
        latest=latest_df,
        trend=trend_df,
        exceptions=exc_df,
        parameters=param_df,
    )


# ---------------------------------------------------------------------------
# Data Quality Dashboard Data
# ---------------------------------------------------------------------------

def get_demo_dq_summary():
    all_exc = get_demo_exceptions()
    open_exc = all_exc[all_exc["Status"] == "OPEN"] if not all_exc.empty else pd.DataFrame()
    open_cnt = len(open_exc)
    total_cnt = len(all_exc) if not all_exc.empty else 7

    total_recs = 13895
    invalid_recs = open_cnt
    valid_recs = total_recs - invalid_recs

    if open_cnt == 0:
        overall = 100.0
        comp = 100.0
        time_pct = 100.0
        val_pct = 100.0
    else:
        # Starting with 5 open exceptions = 98.6%
        # Each resolved exception increases quality towards 100.0%
        overall = round(max(90.0, 100.0 - (open_cnt * 0.28)), 1)
        val_pct = round(max(90.0, 100.0 - (open_cnt * 0.24)), 1)
        comp = round(max(92.0, 100.0 - (open_cnt * 0.16)), 1)
        time_pct = round(max(90.0, 99.0 - (open_cnt * 0.24)), 1)

    return {
        "overall_score": overall,
        "completeness": comp,
        "timeliness": time_pct,
        "validity": val_pct,
        "records_received": total_recs,
        "records_valid": valid_recs,
        "records_invalid": invalid_recs,
        "records_duplicate": 0,
        "expected_records": total_recs,
        "exceptions": open_cnt,
        "corrections": total_cnt - open_cnt,
        "traceable": total_recs,
        "unreconciled_kwh": 0.0,
        "open_exceptions": open_cnt,
        "resolved_exceptions": total_cnt - open_cnt,
    }


def get_demo_source_health():
    all_exc = get_demo_exceptions()
    def count_open_source(src):
        if all_exc.empty:
            return 0
        return len(all_exc[(all_exc["Source"].str.upper() == src.upper()) & (all_exc["Status"] == "OPEN")])

    eb_open = count_open_source("EB")
    dg_open = count_open_source("DG")
    sol_open = count_open_source("SOLAR")
    trf_open = count_open_source("TRANSFORMER")
    ups_open = count_open_source("UPS")

    return pd.DataFrame([
        {"Source": "EB", "Last Import": "2026-09-25", "Status": "HEALTHY" if eb_open == 0 else "ATTENTION_REQUIRED", "Records": 797, "Valid %": 100.0 if eb_open == 0 else round(100.0 - (eb_open * 0.3), 1), "Exceptions": eb_open, "Coverage %": 100.0},
        {"Source": "DG", "Last Import": "2026-09-25", "Status": "HEALTHY" if dg_open == 0 else "ATTENTION_REQUIRED", "Records": 1956, "Valid %": 100.0 if dg_open == 0 else round(100.0 - (dg_open * 0.26), 1), "Exceptions": dg_open, "Coverage %": 100.0},
        {"Source": "SOLAR", "Last Import": "2026-09-25", "Status": "HEALTHY" if sol_open == 0 else "ATTENTION_REQUIRED", "Records": 519, "Valid %": 100.0 if sol_open == 0 else 99.5, "Exceptions": sol_open, "Coverage %": 100.0},
        {"Source": "TRANSFORMER", "Last Import": "2026-09-25", "Status": "HEALTHY" if trf_open == 0 else "ATTENTION_REQUIRED", "Records": 1552, "Valid %": 100.0 if trf_open == 0 else 99.2, "Exceptions": trf_open, "Coverage %": 100.0},
        {"Source": "UPS", "Last Import": "2026-09-25", "Status": "HEALTHY" if ups_open == 0 else "ATTENTION_REQUIRED", "Records": 9071, "Valid %": 100.0 if ups_open == 0 else 99.0, "Exceptions": ups_open, "Coverage %": 100.0},
    ])


def get_demo_import_health():
    today = date.today()
    return pd.DataFrame([
        {"Date": (today - timedelta(days=i)).strftime("%Y-%m-%d"), "Received": 5, "Imported": 5, "Invalid": 0, "Duplicate": 1 if i == 2 else 0, "Failed": 0, "Completed": 5}
        for i in range(10, -1, -1)
    ])


def get_demo_exception_ageing():
    all_exc = get_demo_exceptions()
    open_exc = all_exc[all_exc["Status"] == "OPEN"] if not all_exc.empty else pd.DataFrame()
    open_err = len(open_exc[open_exc["Severity"] == "ERROR"])
    open_warn = len(open_exc[open_exc["Severity"] == "WARNING"])

    return pd.DataFrame([
        {"Age Bucket": "< 24 Hours", "INFO": 0, "WARNING": open_warn, "ERROR": open_err, "CRITICAL": 0},
        {"Age Bucket": "1 - 7 Days", "INFO": 1, "WARNING": 0, "ERROR": 0, "CRITICAL": 0},
        {"Age Bucket": "> 7 Days", "INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0},
    ])


# ---------------------------------------------------------------------------
# Exceptions Center Data & Raw Data Diagnostics
# ---------------------------------------------------------------------------

RAW_EXCEPTION_DETAILS = {
    "EXC-1001": {
        "exception_id": "EXC-1001",
        "source_file": "SRTPL_Test_JUNO_EB.csv",
        "row_number": 4,
        "timestamp": "25/09/2026 12:45:00",
        "asset": "SR-E-EM-EB-TEST",
        "plaza": "TP01",
        "rule": "VAL-EB-001",
        "severity": "ERROR",
        "parameter": "cumulative_kwh",
        "source_value": "1295.0",
        "expected_value": ">= 1310.0",
        "message": "EB cumulative kWh decreased from 1310.0 to 1295.0 (-15.0 kWh). Possible meter reset or manual transcription error.",
        "entered_by": "Sunil Kullu (Operator)",
        "operator_id": "OP-TP01-01",
        "shift": "Shift A (06:00 - 14:00)",
        "entry_method": "Manual Control Room Field Log Entry",
        "root_cause": "Transposed digits during manual typing: entered 1295.0 instead of 1325.0 kWh",
        "previous_reading": {"Row": 3, "Timestamp": "25/09/2026 12:30:00", "Cumulative kWh": 1310.0, "Cumulative kVAh": 1380.0, "PF": 0.95, "Status": "VALID"},
        "offending_reading": {"Row": 4, "Timestamp": "25/09/2026 12:45:00", "Cumulative kWh": 1295.0, "Cumulative kVAh": 1365.0, "PF": 0.94, "Status": "EXCEPTION"},
        "next_reading": {"Row": 5, "Timestamp": "25/09/2026 13:00:00", "Cumulative kWh": 1335.0, "Cumulative kVAh": 1405.0, "PF": 0.95, "Status": "VALID"},
        "raw_payload": {
            "source_row": 4,
            "reading_datetime": "25/09/2026 12:45:00",
            "cumulative_kwh": 1295.0,
            "cumulative_kvah": 1365.0,
            "cumulative_kvarh": 438.0,
            "pf": 0.94,
        },
        "modifiable_fields": {
            "cumulative_kwh": {"label": "Cumulative Active Energy (kWh)", "default": 1325.0, "type": "float", "expected": ">= 1310.0"},
        },
        "suggested_fix": "Change cumulative_kwh from 1295.0 to 1325.0 (fits monotonicity between 1310.0 and 1335.0).",
    },
    "EXC-1002": {
        "exception_id": "EXC-1002",
        "source_file": "SRTPL_Test_JUNO_EB.csv",
        "row_number": 4,
        "timestamp": "25/09/2026 12:45:00",
        "asset": "SR-E-EM-EB-TEST",
        "plaza": "TP01",
        "rule": "VAL-EB-002",
        "severity": "ERROR",
        "parameter": "cumulative_kvah",
        "source_value": "1365.0",
        "expected_value": ">= 1380.0",
        "message": "EB cumulative kVAh decreased from 1380.0 to 1365.0 (-15.0 kVAh). Possible manual entry reversal.",
        "entered_by": "Pritam Mahapatra (Technician)",
        "operator_id": "TC-TP01-04",
        "shift": "Shift A (06:00 - 14:00)",
        "entry_method": "Manual Control Room Field Log Entry",
        "root_cause": "Transcribed kVAh backward as 1365.0 instead of 1395.0",
        "previous_reading": {"Row": 3, "Timestamp": "25/09/2026 12:30:00", "Cumulative kWh": 1310.0, "Cumulative kVAh": 1380.0, "PF": 0.95, "Status": "VALID"},
        "offending_reading": {"Row": 4, "Timestamp": "25/09/2026 12:45:00", "Cumulative kWh": 1295.0, "Cumulative kVAh": 1365.0, "PF": 0.94, "Status": "EXCEPTION"},
        "next_reading": {"Row": 5, "Timestamp": "25/09/2026 13:00:00", "Cumulative kWh": 1335.0, "Cumulative kVAh": 1405.0, "PF": 0.95, "Status": "VALID"},
        "raw_payload": {
            "source_row": 4,
            "reading_datetime": "25/09/2026 12:45:00",
            "cumulative_kwh": 1295.0,
            "cumulative_kvah": 1365.0,
            "cumulative_kvarh": 438.0,
            "pf": 0.94,
        },
        "modifiable_fields": {
            "cumulative_kvah": {"label": "Cumulative Apparent Energy (kVAh)", "default": 1395.0, "type": "float", "expected": ">= 1380.0"},
        },
        "suggested_fix": "Change cumulative_kvah from 1365.0 to 1395.0 (fits monotonicity between 1380.0 and 1405.0).",
    },
    "EXC-1003": {
        "exception_id": "EXC-1003",
        "source_file": "DGDailyLogReport_25thSep2026_443_DG Log.csv",
        "row_number": 42,
        "timestamp": "25/09/2026 10:15:00",
        "asset": "SR-E-AP-DGX-000004",
        "plaza": "TP02",
        "rule": "VAL-DG-001",
        "severity": "WARNING",
        "parameter": "cumulative_kwh",
        "source_value": "9590.0",
        "expected_value": ">= 9609.2",
        "message": "DG cumulative kWh dropped from 9609.2 to 9590.0. Possible meter reset or field typo.",
        "entered_by": "Rajesh Swain (Operator)",
        "operator_id": "OP-TP02-02",
        "shift": "Shift B (14:00 - 22:00)",
        "entry_method": "DG Yard Handwritten Log Transcription",
        "root_cause": "Typo on DG meter counter: entered 9590.0 instead of 9618.0",
        "previous_reading": {"Row": 41, "Timestamp": "25/09/2026 10:00:00", "Cumulative kWh": 9609.2, "Run Hours": 1208.0, "PF": 0.98, "Status": "VALID"},
        "offending_reading": {"Row": 42, "Timestamp": "25/09/2026 10:15:00", "Cumulative kWh": 9590.0, "Run Hours": 1208.4, "PF": 0.98, "Status": "EXCEPTION"},
        "next_reading": {"Row": 43, "Timestamp": "25/09/2026 10:30:00", "Cumulative kWh": 9625.5, "Run Hours": 1208.7, "PF": 0.98, "Status": "VALID"},
        "raw_payload": {
            "source_row": 42,
            "reading_datetime": "25/09/2026 10:15:00",
            "cumulative_kwh": 9590.0,
            "cumulative_running_hours": 1208.4,
            "voltage_ry": 415.0,
            "current_r": 28.5,
            "pf": 0.98,
        },
        "modifiable_fields": {
            "cumulative_kwh": {"label": "DG Cumulative kWh", "default": 9618.0, "type": "float", "expected": ">= 9609.2"},
        },
        "suggested_fix": "Change cumulative_kwh from 9590.0 to 9618.0 (corrects typo digit 9 to 1).",
    },
    "EXC-1004": {
        "exception_id": "EXC-1004",
        "source_file": "DGDailyLogReport_25thSep2026_443_DG Log.csv",
        "row_number": 88,
        "timestamp": "25/09/2026 14:00:00",
        "asset": "SR-E-AP-DGX-000004",
        "plaza": "TP02",
        "rule": "VAL-DG-002",
        "severity": "WARNING",
        "parameter": "cumulative_running_hours",
        "source_value": "1210.0",
        "expected_value": ">= 1215.5",
        "message": "DG running hours decreased from 1215.5 to 1210.0 (-5.5 hr). Hour meter cannot run backwards.",
        "entered_by": "Rajesh Swain (Operator)",
        "operator_id": "OP-TP02-02",
        "shift": "Shift B (14:00 - 22:00)",
        "entry_method": "DG Yard Handwritten Log Transcription",
        "root_cause": "DG Running hours written as 1210.0 instead of 1215.8",
        "previous_reading": {"Row": 87, "Timestamp": "25/09/2026 13:45:00", "Cumulative kWh": 9740.0, "Run Hours": 1215.5, "PF": 0.98, "Status": "VALID"},
        "offending_reading": {"Row": 88, "Timestamp": "25/09/2026 14:00:00", "Cumulative kWh": 9755.0, "Run Hours": 1210.0, "PF": 0.98, "Status": "EXCEPTION"},
        "next_reading": {"Row": 89, "Timestamp": "25/09/2026 14:15:00", "Cumulative kWh": 9770.0, "Run Hours": 1216.0, "PF": 0.98, "Status": "VALID"},
        "raw_payload": {
            "source_row": 88,
            "reading_datetime": "25/09/2026 14:00:00",
            "cumulative_kwh": 9755.0,
            "cumulative_running_hours": 1210.0,
            "pf": 0.98,
        },
        "modifiable_fields": {
            "cumulative_running_hours": {"label": "DG Running Hours", "default": 1215.8, "type": "float", "expected": ">= 1215.5"},
        },
        "suggested_fix": "Change cumulative_running_hours to 1215.8.",
    },
    "EXC-1005": {
        "exception_id": "EXC-1005",
        "source_file": "DGDailyLogReport_25thSep2026_443_DG Log.csv",
        "row_number": 112,
        "timestamp": "25/09/2026 16:30:00",
        "asset": "SR-E-AP-DGX-000004",
        "plaza": "TP02",
        "rule": "VAL-DG-004",
        "severity": "ERROR",
        "parameter": "pf",
        "source_value": "98.0",
        "expected_value": "0.0 <= PF <= 1.0",
        "message": "DG Power Factor is 98.0, exceeding standard physical range (0.0 to 1.0). Meter logged percentage instead of ratio.",
        "entered_by": "Rajesh Swain (Operator)",
        "operator_id": "OP-TP02-02",
        "shift": "Shift B (14:00 - 22:00)",
        "entry_method": "DG Yard Handwritten Log Transcription",
        "root_cause": "Omitted decimal point: logged 98.0 instead of 0.98",
        "previous_reading": {"Row": 111, "Timestamp": "25/09/2026 16:15:00", "Cumulative kWh": 9890.0, "Run Hours": 1224.0, "PF": 0.98, "Status": "VALID"},
        "offending_reading": {"Row": 112, "Timestamp": "25/09/2026 16:30:00", "Cumulative kWh": 9905.0, "Run Hours": 1224.2, "PF": 98.0, "Status": "EXCEPTION"},
        "next_reading": {"Row": 113, "Timestamp": "25/09/2026 16:45:00", "Cumulative kWh": 9920.0, "Run Hours": 1224.5, "PF": 0.98, "Status": "VALID"},
        "raw_payload": {
            "source_row": 112,
            "reading_datetime": "25/09/2026 16:30:00",
            "cumulative_kwh": 9905.0,
            "cumulative_running_hours": 1224.2,
            "pf": 98.0,
        },
        "modifiable_fields": {
            "pf": {"label": "Power Factor (0.0 to 1.0)", "default": 0.98, "type": "float", "expected": "0.0 <= PF <= 1.0"},
        },
        "suggested_fix": "Change pf from 98.0 to 0.98 (percentage unit typo).",
    },
    "EXC-1006": {
        "exception_id": "EXC-1006",
        "source_file": "TransformerDailyReport_25thSep2026_2116_Transformer Daily Log Report.csv",
        "row_number": 64,
        "timestamp": "25/09/2026 11:00:00",
        "asset": "SR-E-HT-TFR-000002",
        "plaza": "TP01",
        "rule": "VAL-TRF-001",
        "severity": "WARNING",
        "parameter": "voltage_imbalance",
        "source_value": "2.8%",
        "expected_value": "<= 2.0%",
        "message": "Transformer primary phase voltage imbalance is 2.8%, above 2.0% warning threshold.",
        "entered_by": "Anil Seth (Senior Electrician)",
        "operator_id": "TC-TP01-02",
        "shift": "Shift A (06:00 - 14:00)",
        "entry_method": "Substation Yard PT Test Sheet",
        "root_cause": "Primary tap changer calibration variance during grid load fluctuation",
        "previous_reading": {"Row": 63, "Timestamp": "25/09/2026 10:45:00", "V_RY": 11050.0, "V_YB": 11020.0, "V_BR": 11040.0, "Status": "VALID"},
        "offending_reading": {"Row": 64, "Timestamp": "25/09/2026 11:00:00", "V_RY": 11200.0, "V_YB": 10850.0, "V_BR": 11150.0, "Status": "EXCEPTION"},
        "next_reading": {"Row": 65, "Timestamp": "25/09/2026 11:15:00", "V_RY": 11080.0, "V_YB": 11040.0, "V_BR": 11060.0, "Status": "VALID"},
        "raw_payload": {
            "source_row": 64,
            "reading_datetime": "25/09/2026 11:00:00",
            "primary_v_ry": 11200.0,
            "primary_v_yb": 10850.0,
            "primary_v_br": 11150.0,
        },
        "modifiable_fields": {
            "primary_v_yb": {"label": "Primary Voltage Y-B (V)", "default": 11050.0, "type": "float", "expected": "~ 11000V"},
        },
        "suggested_fix": "Verify V_YB PT reading or calibrate tap changer.",
    },
    "EXC-1007": {
        "exception_id": "EXC-1007",
        "source_file": "UPSDailyLogReport_25thSep2026_2140_UPS Daily Log Report.csv",
        "row_number": 128,
        "timestamp": "25/09/2026 17:15:00",
        "asset": "SR-E-AP-UPS-000009",
        "plaza": "TP03",
        "rule": "VAL-UPS-OUTPUT-V",
        "severity": "WARNING",
        "parameter": "output_voltage",
        "source_value": "195.0 V",
        "expected_value": "207.0 V to 253.0 V",
        "message": "UPS output voltage dipped to 195.0 V, below nominal 230V ± 10% operating standard.",
        "entered_by": "Deepak Patel (Technician)",
        "operator_id": "TC-TP03-03",
        "shift": "Shift B (14:00 - 22:00)",
        "entry_method": "Server Room UPS Panel Logger Sync",
        "root_cause": "Transient grid voltage dip prior to automatic inverter changeover",
        "previous_reading": {"Row": 127, "Timestamp": "25/09/2026 17:00:00", "Output Voltage": 230.5, "Frequency": 50.0, "Battery VDC": 465.0, "Status": "VALID"},
        "offending_reading": {"Row": 128, "Timestamp": "25/09/2026 17:15:00", "Output Voltage": 195.0, "Frequency": 49.8, "Battery VDC": 450.0, "Status": "EXCEPTION"},
        "next_reading": {"Row": 129, "Timestamp": "25/09/2026 17:30:00", "Output Voltage": 231.0, "Frequency": 50.0, "Battery VDC": 462.0, "Status": "VALID"},
        "raw_payload": {
            "source_row": 128,
            "reading_datetime": "25/09/2026 17:15:00",
            "output_voltage": 195.0,
            "output_frequency": 49.8,
            "battery_vdc": 450.0,
        },
        "modifiable_fields": {
            "output_voltage": {"label": "UPS Output Voltage (V)", "default": 230.0, "type": "float", "expected": "207.0 to 253.0 V"},
        },
        "suggested_fix": "Correct sensor glitch or accept transient event with grid changeover note.",
    },
}


def get_demo_exceptions() -> pd.DataFrame:
    if not is_demo_mode():
        try:
            from core.supabase_manager import get_supabase_client
            client = get_supabase_client()
            if client:
                res = client.table("exception_record").select("*").execute()
                if res.data:
                    return pd.DataFrame(res.data)
        except Exception:
            pass
        return pd.DataFrame(columns=[
            "Exception ID", "Source File", "Row", "Timestamp", "Source", "Plaza", "Asset",
            "Rule", "Severity", "Status", "Detected / Corrected Value", "Message",
            "Root Cause & Impact", "Audit Action", "Resolved By", "Resolution Timestamp", "Resolution Note"
        ])

    overrides = st.session_state.get("exception_overrides", {})
    records = []
    for exc_id, d in RAW_EXCEPTION_DETAILS.items():
        override = overrides.get(exc_id, {})
        status = override.get("status", "OPEN" if exc_id not in ("EXC-1006", "EXC-1007") else ("RESOLVED" if exc_id == "EXC-1006" else "ACCEPTED_EXCEPTION"))
        offending_val = override.get("corrected_value", d["source_value"])
        resolved_by = override.get("resolved_by", "-" if status == "OPEN" else "admin@srtpl.com")
        resolved_at = override.get("resolved_at", "-" if status == "OPEN" else "2026-09-25 15:00:00")
        res_note = override.get("note", "-" if status == "OPEN" else "Audit baseline verified")
        records.append({
            "Exception ID": exc_id,
            "Source File": d["source_file"],
            "Row": d["row_number"],
            "Timestamp": d["timestamp"],
            "Source": d["source_file"].split("_")[0] if "_" in d["source_file"] else d["rule"].split("-")[1],
            "Plaza": d["plaza"],
            "Asset": d["asset"],
            "Rule": d["rule"],
            "Severity": d["severity"],
            "Status": status,
            "Offending Value": offending_val,
            "Expected": d["expected_value"],
            "Message": d["message"],
            "Entered By": d.get("entered_by", "Field Operator"),
            "Operator ID": d.get("operator_id", "-"),
            "Shift": d.get("shift", "Shift 1"),
            "Root Cause": d.get("root_cause", d["message"]),
            "Resolved By": resolved_by,
            "Resolved At": resolved_at,
            "Resolution Note": res_note,
        })
    return pd.DataFrame(records)


def get_raw_exception_detail(exception_id: str) -> dict | None:
    return RAW_EXCEPTION_DETAILS.get(exception_id)


def apply_exception_raw_fix(
    exception_id: str,
    field_name: str,
    new_value: Any,
    user: str = "admin@srtpl.com",
    resolution_type: str = "CORRECTED",
    note: str = "",
) -> dict:
    if "exception_overrides" not in st.session_state:
        st.session_state["exception_overrides"] = {}

    status = "RESOLVED" if resolution_type in ("CORRECTED", "RESOLVE") else "ACCEPTED_EXCEPTION"
    st.session_state["exception_overrides"][exception_id] = {
        "status": status,
        "corrected_field": field_name,
        "corrected_value": str(new_value),
        "resolved_by": user,
        "resolved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "resolution_type": resolution_type,
        "note": note,
    }
    try:
        from core.db_sync import update_exception_in_database
        update_exception_in_database(exception_id, status, new_value, note, user)
    except Exception:
        pass
    return st.session_state["exception_overrides"][exception_id]


def reopen_exception(exception_id: str, user: str = "admin@srtpl.com", note: str = "") -> dict:
    if "exception_overrides" not in st.session_state:
        st.session_state["exception_overrides"] = {}
    st.session_state["exception_overrides"][exception_id] = {
        "status": "OPEN",
        "resolved_by": None,
        "resolved_at": None,
        "note": f"Reopened by {user}: {note}" if note else f"Reopened by {user}",
    }
    try:
        from core.db_sync import update_exception_in_database
        update_exception_in_database(exception_id, "OPEN", "", note, user)
    except Exception:
        pass
    return st.session_state["exception_overrides"][exception_id]


def dismiss_exception(exception_id: str, user: str = "admin@srtpl.com", note: str = "") -> dict:
    if "exception_overrides" not in st.session_state:
        st.session_state["exception_overrides"] = {}
    st.session_state["exception_overrides"][exception_id] = {
        "status": "DISMISSED",
        "resolved_by": user,
        "resolved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "resolution_type": "DISMISSED",
        "note": note or f"Dismissed as non-blocking / false positive by {user}",
    }
    try:
        from core.db_sync import update_exception_in_database
        update_exception_in_database(exception_id, "DISMISSED", "", note, user)
    except Exception:
        pass
    return st.session_state["exception_overrides"][exception_id]


def reset_demo_exceptions():
    if "exception_overrides" in st.session_state:
        st.session_state["exception_overrides"] = {}


def export_corrected_raw_csv(exception_id: str) -> str:
    detail = get_raw_exception_detail(exception_id)
    if not detail:
        return "No data"

    overrides = st.session_state.get("exception_overrides", {}).get(exception_id, {})
    row_data = dict(detail["raw_payload"])
    if "corrected_field" in overrides:
        row_data[overrides["corrected_field"]] = overrides["corrected_value"]

    # Generate a clean CSV representation of the corrected data
    df = pd.DataFrame([row_data])
    return df.to_csv(index=False)


# ---------------------------------------------------------------------------
# Import History Data
# ---------------------------------------------------------------------------

def get_demo_import_history():
    return pd.DataFrame([
        {"Batch ID": "BATCH-EB-001", "Filename": "SRTPL_Test_JUNO_EB.csv", "Source": "EB", "Rows": 7, "Valid": 5, "Exceptions": 2, "Status": "IMPORTED", "Timestamp": "2026-09-25 10:15", "SHA-256": "e3b0c44298fc1c14..."},
        {"Batch ID": "BATCH-DG-001", "Filename": "DGDailyLogReport_25thSep2026_443_DG Log.csv", "Source": "DG", "Rows": 334, "Valid": 329, "Exceptions": 5, "Status": "IMPORTED", "Timestamp": "2026-09-25 11:30", "SHA-256": "4a5c689e134b22..."},
        {"Batch ID": "BATCH-SOL-001", "Filename": "Solar_Plant_Log_25thSep2026_2719_Solar Log.csv", "Source": "SOLAR", "Rows": 177, "Valid": 177, "Exceptions": 0, "Status": "IMPORTED", "Timestamp": "2026-09-25 12:45", "SHA-256": "f90123cb88da..."},
        {"Batch ID": "BATCH-TRF-001", "Filename": "TransformerDailyReport_25thSep2026_2116_Transformer Daily Log Report.csv", "Source": "TRANSFORMER", "Rows": 252, "Valid": 252, "Exceptions": 0, "Status": "IMPORTED", "Timestamp": "2026-09-25 14:00", "SHA-256": "cc5e8af03d5e..."},
        {"Batch ID": "BATCH-UPS-001", "Filename": "UPSDailyLogReport_25thSep2026_2140_UPS Daily Log Report.csv", "Source": "UPS", "Rows": 1459, "Valid": 1459, "Exceptions": 0, "Status": "IMPORTED", "Timestamp": "2026-09-25 15:20", "SHA-256": "1283fa7b49cc..."},
    ])


# ---------------------------------------------------------------------------
# Reports Data
# ---------------------------------------------------------------------------

def get_demo_report_df(report_code: str):
    return pd.DataFrame([
        {"Date": "2026-09-25", "Plaza": "TP01", "Source": "EB", "Consumption kWh": 1820.0, "Cost INR": 14560.0, "Status": "VERIFIED"},
        {"Date": "2026-09-25", "Plaza": "TP01", "Source": "DG", "Consumption kWh": 410.0, "Cost INR": 10250.0, "Status": "VERIFIED"},
        {"Date": "2026-09-25", "Plaza": "TP01", "Source": "SOLAR", "Consumption kWh": 1490.4, "Cost INR": 0.0, "Status": "VERIFIED"},
        {"Date": "2026-09-25", "Plaza": "TP02", "Source": "EB", "Consumption kWh": 1650.0, "Cost INR": 13200.0, "Status": "VERIFIED"},
        {"Date": "2026-09-25", "Plaza": "TP02", "Source": "DG", "Consumption kWh": 520.0, "Cost INR": 13000.0, "Status": "VERIFIED"},
        {"Date": "2026-09-25", "Plaza": "TP03", "Source": "SOLAR", "Consumption kWh": 1280.0, "Cost INR": 0.0, "Status": "VERIFIED"},
    ])


# ---------------------------------------------------------------------------
# Audit Log Data
# ---------------------------------------------------------------------------

def get_demo_audit_log():
    return pd.DataFrame([
        {"Audit ID": "AUD-501", "Timestamp": "2026-09-25 15:25", "User": "admin@srtpl.com", "Action": "IMPORT_PIPELINE", "Entity": "import_batch", "Entity ID": "BATCH-UPS-001", "Reason": "Validated 1,459 UPS intervals with 100% availability."},
        {"Audit ID": "AUD-502", "Timestamp": "2026-09-25 14:05", "User": "admin@srtpl.com", "Action": "IMPORT_PIPELINE", "Entity": "import_batch", "Entity ID": "BATCH-TRF-001", "Reason": "Validated 252 Transformer readings; Loss/efficiency disabled per audit guard."},
        {"Audit ID": "AUD-503", "Timestamp": "2026-09-25 12:50", "User": "admin@srtpl.com", "Action": "IMPORT_PIPELINE", "Entity": "import_batch", "Entity ID": "BATCH-SOL-001", "Reason": "Validated 14,904 kWh Solar generation across 177 log records."},
        {"Audit ID": "AUD-504", "Timestamp": "2026-09-25 11:35", "User": "admin@srtpl.com", "Action": "IMPORT_PIPELINE", "Entity": "import_batch", "Entity ID": "BATCH-DG-001", "Reason": "Validated 9,609.2 kWh DG generation; 5 exceptions routed to review."},
        {"Audit ID": "AUD-505", "Timestamp": "2026-09-25 10:20", "User": "admin@srtpl.com", "Action": "IMPORT_PIPELINE", "Entity": "import_batch", "Entity ID": "BATCH-EB-001", "Reason": "Validated 125.0 kWh EB consumption; 2 exception records excluded from KPI."},
    ])


# ---------------------------------------------------------------------------
# Master Data Data
# ---------------------------------------------------------------------------

def get_demo_master_data(domain: str):
    if domain == "PLAZA":
        return pd.DataFrame([
            {"ID": "P-01", "Code": "TP01", "Name": "Toll Plaza 01 (Baragarh)", "Active": True},
            {"ID": "P-02", "Code": "TP02", "Name": "Toll Plaza 02 (Sambalpur)", "Active": True},
            {"ID": "P-03", "Code": "TP03", "Name": "Toll Plaza 03 (Rengali)", "Active": True},
        ])
    elif domain == "ASSET":
        return pd.DataFrame([
            {"ID": "A-01", "Code": "SR-E-EM-EB-000TP01", "Type": "EB", "Plaza": "TP01", "Location": "Main Incomer", "Active": True},
            {"ID": "A-02", "Code": "SR-E-AP-DGX-000001", "Type": "DG", "Plaza": "TP01", "Location": "DG Yard", "Active": True},
            {"ID": "A-03", "Code": "SR-E-AP-SPX-000001", "Type": "SOLAR", "Plaza": "TP01", "Location": "Control Room Rooftop", "Active": True},
            {"ID": "A-04", "Code": "SR-E-HT-TFR-000002", "Type": "TRANSFORMER", "Plaza": "TP01", "Location": "Substation HT Yard", "Active": True},
            {"ID": "A-05", "Code": "SR-E-AP-UPS-000009", "Type": "UPS", "Plaza": "TP01", "Location": "Server Room", "Active": True},
        ])
    elif domain == "THRESHOLD":
        return pd.DataFrame([
            {"ID": "T-01", "Parameter": "Power Factor", "Condition": "MIN", "Warning": "0.95", "Critical": "0.90", "Unit": "PF", "Active": True},
            {"ID": "T-02", "Parameter": "Voltage Imbalance", "Condition": "MAX", "Warning": "3.0", "Critical": "5.0", "Unit": "%", "Active": True},
            {"ID": "T-03", "Parameter": "Current Imbalance", "Condition": "MAX", "Warning": "10.0", "Critical": "15.0", "Unit": "%", "Active": True},
            {"ID": "T-04", "Parameter": "UPS Output Voltage", "Condition": "RANGE", "Warning": "210-245", "Critical": "200-250", "Unit": "V", "Active": True},
        ])
    elif domain == "TARIFF":
        return pd.DataFrame([
            {"ID": "TAR-01", "Code": "TPWODL_HT", "Name": "Grid HT Commercial Tariff", "Energy Rate": 7.85, "Demand Rate": 250.0, "Fixed Charge": 5000.0, "Effective From": "2026-04-01", "Effective To": "2027-03-31", "Active": True},
            {"ID": "TAR-02", "Code": "DIESEL_GEN", "Name": "DG Standard Fuel Benchmark", "Energy Rate": 25.0, "Demand Rate": 0.0, "Fixed Charge": 0.0, "Effective From": "2026-04-01", "Effective To": "2027-03-31", "Active": True},
        ])
    elif domain == "KPI":
        return pd.DataFrame([
            {"ID": "K-01", "Code": "EB-CONS-D", "Name": "EB Daily Consumption", "Formula": "SUM(interval_kwh)", "Unit": "kWh", "Scope": "EB", "Version": "5.4.0", "Active": True},
            {"ID": "K-02", "Code": "DG-GEN-D", "Name": "DG Daily Generation", "Formula": "SUM(interval_kwh)", "Unit": "kWh", "Scope": "DG", "Version": "5.3.1", "Active": True},
            {"ID": "K-03", "Code": "SOL-GEN-D", "Name": "Solar Daily Generation", "Formula": "SUM(interval_kwh)", "Unit": "kWh", "Scope": "SOLAR", "Version": "5.5.0", "Active": True},
            {"ID": "K-04", "Code": "TR-VI-01", "Name": "Transformer Voltage Imbalance", "Formula": "MAX(phase_imbalance)", "Unit": "%", "Scope": "TRANSFORMER", "Version": "5.6.0", "Active": True},
            {"ID": "K-05", "Code": "UPS-AV-01", "Name": "UPS Operational Availability", "Formula": "COUNT(VALID)/COUNT(TOTAL)*100", "Unit": "%", "Scope": "UPS", "Version": "5.7.0", "Active": True},
        ])
    return pd.DataFrame()


# ---------------------------------------------------------------------------
# Admin Center Data
# ---------------------------------------------------------------------------

def get_demo_users():
    return pd.DataFrame([
        {"User ID": "U-1", "Email": "admin@srtpl.com", "Name": "Prabodh Rana", "Role": "SUPER_ADMIN", "Plaza": "ALL", "Active": True, "Created At": "2026-01-01"},
        {"User ID": "U-2", "Email": "operator.tp01@srtpl.com", "Name": "Sunil Kullu", "Role": "OPERATOR", "Plaza": "TP01", "Active": True, "Created At": "2026-01-15"},
        {"User ID": "U-3", "Email": "engineer.tp02@srtpl.com", "Name": "Pritam Mahapatra", "Role": "ENGINEER", "Plaza": "TP02", "Active": True, "Created At": "2026-02-01"},
        {"User ID": "U-4", "Email": "manager.tp03@srtpl.com", "Name": "Ranjan Khadia", "Role": "PLAZA_MANAGER", "Plaza": "TP03", "Active": True, "Created At": "2026-02-15"},
    ])


def get_demo_change_requests():
    return pd.DataFrame([
        {"Request ID": "CR-101", "Entity": "THRESHOLD", "Change": "Adjust UPS Output Voltage warning to 210-245V", "Requested By": "Pritam Mahapatra", "Requested At": "2026-09-20", "Status": "APPLIED", "Approved By": "admin@srtpl.com", "Applied At": "2026-09-21"},
        {"Request ID": "CR-102", "Entity": "TARIFF", "Change": "Update TPWODL HT tariff rate to 7.85/kWh", "Requested By": "Ranjan Khadia", "Requested At": "2026-09-22", "Status": "PENDING", "Approved By": "-", "Applied At": "-"},
    ])


def get_demo_reprocess_jobs():
    return pd.DataFrame([
        {"Job ID": "REP-01", "Batch ID": "BATCH-DG-001", "Requested By": "admin@srtpl.com", "Requested At": "2026-09-25 11:30", "Status": "COMPLETED", "Approved By": "admin@srtpl.com", "Started": "2026-09-25 11:31", "Completed": "2026-09-25 11:32"}
    ])


# ---------------------------------------------------------------------------
# Bills & Receipts / Month-wise EB Consumption Center
# ---------------------------------------------------------------------------

def get_demo_bills():
    if not is_demo_mode():
        try:
            from core.supabase_manager import get_supabase_client
            client = get_supabase_client()
            if client:
                res = client.table("energy_bills").select("*").execute()
                if res.data:
                    rows = []
                    for b in res.data:
                        amt = float(b.get("total_amount_payable") or b.get("current_total") or 0.0)
                        rows.append({
                            "Document ID": str(b.get("bill_number", "")),
                            "Plaza": "TP01",
                            "Type": "Electricity Bill",
                            "Period / Date": str(b.get("bill_month", "")),
                            "Discom": "TPWODL",
                            "Amount": amt,
                            "Paid": amt,
                            "Status": "Verified",
                            "Reference": str(b.get("consumer_account_no", "")),
                            "Due Date": "—",
                            "Meter Rent Count": str(b.get("meter_rent_count", "")),
                            "Security Deposit": str(b.get("security_deposit", "")),
                            "Bill Period": str(b.get("bill_period", "")),
                            "Bill Days/Months": str(b.get("bill_days", "")),
                            "Meter Sl. No.": str(b.get("meter_sl_no", "")),
                            "a. Energy Charges": str(b.get("energy_charges", "")),
                            "Slab Normal - KWH": str(b.get("slab_normal_kwh", "")),
                            "Slab Peak - KWH": str(b.get("slab_peak_kwh", "")),
                            "Slab Solar - KWH": str(b.get("slab_solar_kwh", "")),
                            "DPS(Rs.)": str(b.get("dps_rs", "")),
                            "Tariff Category": str(b.get("tariff_category", "")),
                            "Division": str(b.get("division", "")),
                            "Sub-Division": str(b.get("sub_division", "")),
                            "Section": str(b.get("section", "")),
                        })
                    return pd.DataFrame(rows)
        except Exception:
            pass
        return pd.DataFrame(columns=[
            "Document ID", "Plaza", "Type", "Period / Date", "Discom", "Amount", "Paid", "Status",
            "Reference", "Due Date", "Meter Rent Count", "Security Deposit", "Bill Period",
            "Bill Days/Months", "Meter Sl. No.", "a. Energy Charges", "Slab Normal - KWH",
            "Slab Peak - KWH", "Slab Solar - KWH", "DPS(Rs.)", "Tariff Category", "Division",
            "Sub-Division", "Section"
        ])

    return pd.DataFrame([
        {
            "Document ID": "EB-26-1042",
            "Plaza": "TP01",
            "Type": "Electricity Bill",
            "Period / Date": "Sep 2026",
            "Discom": "TPWODL",
            "Amount": 482600.0,
            "Paid": 482600.0,
            "Status": "Paid",
            "Reference": "BILL-TP01-1042",
            "Due Date": "2026-10-15",
            "Meter Rent Count": "34/60",
            "Security Deposit": "36,360.14",
            "Bill Period": "02/08/2026 - 01/09/2026",
            "Bill Days/Months": "30/1.0000",
            "Meter Sl. No.": "10029454",
            "a. Energy Charges": "16,405.20",
            "Slab Normal - KWH": "2313",
            "Slab Peak - KWH": "1334",
            "Slab Solar - KWH": "25",
            "DPS(Rs.)": "32.99",
            "Tariff Category": "PUBLIC LIGHT",
            "Division": "SED SAMBALPUR",
            "Sub-Division": "SDO-I SAMBALPUR",
            "Section": "ESO RE SECTION",
        },
        {
            "Document ID": "EB-26-1048",
            "Plaza": "TP02",
            "Type": "Electricity Bill",
            "Period / Date": "Sep 2026",
            "Discom": "TPWODL",
            "Amount": 526300.0,
            "Paid": 300000.0,
            "Status": "Partial",
            "Reference": "BILL-TP02-1048",
            "Due Date": "2026-10-15",
            "Meter Rent Count": "47/60",
            "Security Deposit": "64,391.05",
            "Bill Period": "02/08/2026 - 01/09/2026",
            "Bill Days/Months": "30/1.0000",
            "Meter Sl. No.": "TWN20045",
            "a. Energy Charges": "1,34,627.81",
            "Slab Normal - KWH": "9899",
            "Slab Peak - KWH": "8124",
            "Slab Solar - KWH": "4630",
            "DPS(Rs.)": "0.00",
            "Tariff Category": "GENERAL PURPOSE >= 110 kVA",
            "Division": "SEED SAMBALPUR",
            "Sub-Division": "SDO RENGALI",
            "Section": "ESO SASON",
        },
        {
            "Document ID": "EB-26-1053",
            "Plaza": "TP03",
            "Type": "Electricity Bill",
            "Period / Date": "Sep 2026",
            "Discom": "TPWODL",
            "Amount": 398500.0,
            "Paid": 0.0,
            "Status": "Unpaid",
            "Reference": "BILL-TP03-1053",
            "Due Date": "2026-10-20",
            "Meter Rent Count": "34/60",
            "Security Deposit": "1,79,770.00",
            "Bill Period": "02/08/2026 - 01/09/2026",
            "Bill Days/Months": "30/1.0000",
            "Meter Sl. No.": "TWSL12001179",
            "a. Energy Charges": "45,820.50",
            "Slab Normal - KWH": "5420",
            "Slab Peak - KWH": "2424",
            "Slab Solar - KWH": "4",
            "DPS(Rs.)": "54.17",
            "Tariff Category": "PUBLIC LIGHT",
            "Division": "JED JHARSUGUDA",
            "Sub-Division": "SDO-I JHARSUGUDA",
            "Section": "ESO SAHAPADA",
        },
        {
            "Document ID": "RC-26-0841",
            "Plaza": "TP02",
            "Type": "Payment Receipt",
            "Period / Date": "18 Oct 2026",
            "Discom": "TPWODL",
            "Amount": 300000.0,
            "Paid": 300000.0,
            "Status": "Matched",
            "Reference": "UTR-DEMO-841",
            "Due Date": "-",
            "Meter Rent Count": "-",
            "Security Deposit": "-",
            "Bill Period": "-",
            "Bill Days/Months": "-",
            "Meter Sl. No.": "-",
            "a. Energy Charges": "-",
            "Slab Normal - KWH": "-",
            "Slab Peak - KWH": "-",
            "Slab Solar - KWH": "-",
            "DPS(Rs.)": "-",
            "Tariff Category": "PUBLIC LIGHT",
            "Division": "SED SAMBALPUR",
            "Sub-Division": "SDO-I SAMBALPUR",
            "Section": "ESO RE SECTION",
        },
    ])


def get_demo_monthly_eb_consumption():
    if not is_demo_mode():
        return pd.DataFrame(columns=[
            "Month", "Plaza", "Bill No", "Tariff", "Contract Demand (kVA)", "Billed kWh",
            "Metered kWh (JUNO)", "Variance kWh", "Variance %", "PF", "Fixed Charges",
            "Energy Charges", "Total Amount", "Paid", "Balance", "Status", "Meter Rent Count",
            "Security Deposit", "Bill Period", "Bill Days/Months", "Meter Sl. No.",
            "a. Energy Charges", "Slab Normal - KWH", "Slab Peak - KWH", "Slab Solar - KWH",
            "DPS(Rs.)", "Tariff Category", "Division", "Sub-Division", "Section"
        ])

    return pd.DataFrame([
        {
            "Month": "Sep 2026",
            "Plaza": "TP01",
            "Bill No": "TPW-2026-09-01",
            "Tariff": "HT Commercial",
            "Contract Demand (kVA)": 250,
            "Billed kWh": 18420.0,
            "Metered kWh (JUNO)": 18200.0,
            "Variance kWh": 220.0,
            "Variance %": 1.2,
            "PF": 0.98,
            "Fixed Charges": 62500.0,
            "Energy Charges": 144597.0,
            "Total Amount": 248000.0,
            "Paid": 248000.0,
            "Balance": 0.0,
            "Status": "Paid",
            "Meter Rent Count": "34/60",
            "Security Deposit": "36,360.14",
            "Bill Period": "02/08/2026 - 01/09/2026",
            "Bill Days/Months": "30/1.0000",
            "Meter Sl. No.": "10029454",
            "a. Energy Charges": "16,405.20",
            "Slab Normal - KWH": "2313",
            "Slab Peak - KWH": "1334",
            "Slab Solar - KWH": "25",
            "DPS(Rs.)": "32.99",
            "Tariff Category": "PUBLIC LIGHT",
            "Division": "SED SAMBALPUR",
            "Sub-Division": "SDO-I SAMBALPUR",
            "Section": "ESO RE SECTION",
        },
        {
            "Month": "Sep 2026",
            "Plaza": "TP02",
            "Bill No": "TPW-2026-09-02",
            "Tariff": "HT Commercial",
            "Contract Demand (kVA)": 250,
            "Billed kWh": 16750.0,
            "Metered kWh (JUNO)": 16500.0,
            "Variance kWh": 250.0,
            "Variance %": 1.5,
            "PF": 0.96,
            "Fixed Charges": 62500.0,
            "Energy Charges": 131487.0,
            "Total Amount": 228000.0,
            "Paid": 128000.0,
            "Balance": 100000.0,
            "Status": "Partial",
            "Meter Rent Count": "47/60",
            "Security Deposit": "64,391.05",
            "Bill Period": "02/08/2026 - 01/09/2026",
            "Bill Days/Months": "30/1.0000",
            "Meter Sl. No.": "TWN20045",
            "a. Energy Charges": "1,34,627.81",
            "Slab Normal - KWH": "9899",
            "Slab Peak - KWH": "8124",
            "Slab Solar - KWH": "4630",
            "DPS(Rs.)": "0.00",
            "Tariff Category": "GENERAL PURPOSE >= 110 kVA",
            "Division": "SEED SAMBALPUR",
            "Sub-Division": "SDO RENGALI",
            "Section": "ESO SASON",
        },
        {
            "Month": "Sep 2026",
            "Plaza": "TP03",
            "Bill No": "TPW-2026-09-03",
            "Tariff": "HT Commercial",
            "Contract Demand (kVA)": 200,
            "Billed kWh": 13700.0,
            "Metered kWh (JUNO)": 13550.0,
            "Variance kWh": 150.0,
            "Variance %": 1.1,
            "PF": 0.97,
            "Fixed Charges": 50000.0,
            "Energy Charges": 107545.0,
            "Total Amount": 182000.0,
            "Paid": 0.0,
            "Balance": 182000.0,
            "Status": "Unpaid",
            "Meter Rent Count": "34/60",
            "Security Deposit": "1,79,770.00",
            "Bill Period": "02/08/2026 - 01/09/2026",
            "Bill Days/Months": "30/1.0000",
            "Meter Sl. No.": "TWSL12001179",
            "a. Energy Charges": "45,820.50",
            "Slab Normal - KWH": "5420",
            "Slab Peak - KWH": "2424",
            "Slab Solar - KWH": "4",
            "DPS(Rs.)": "54.17",
            "Tariff Category": "PUBLIC LIGHT",
            "Division": "JED JHARSUGUDA",
            "Sub-Division": "SDO-I JHARSUGUDA",
            "Section": "ESO SAHAPADA",
        },
        {
            "Month": "Aug 2026",
            "Plaza": "TP01",
            "Bill No": "TPW-2026-08-01",
            "Tariff": "HT Commercial",
            "Contract Demand (kVA)": 250,
            "Billed kWh": 18150.0,
            "Metered kWh (JUNO)": 18020.0,
            "Variance kWh": 130.0,
            "Variance %": 0.7,
            "PF": 0.98,
            "Fixed Charges": 62500.0,
            "Energy Charges": 142477.0,
            "Total Amount": 245000.0,
            "Paid": 245000.0,
            "Balance": 0.0,
            "Status": "Paid",
            "Meter Rent Count": "33/60",
            "Security Deposit": "36,360.14",
            "Bill Period": "02/07/2026 - 01/08/2026",
            "Bill Days/Months": "31/1.0000",
            "Meter Sl. No.": "10029454",
            "a. Energy Charges": "15,890.10",
            "Slab Normal - KWH": "2280",
            "Slab Peak - KWH": "1290",
            "Slab Solar - KWH": "20",
            "DPS(Rs.)": "0.00",
            "Tariff Category": "PUBLIC LIGHT",
            "Division": "SED SAMBALPUR",
            "Sub-Division": "SDO-I SAMBALPUR",
            "Section": "ESO RE SECTION",
        },
        {
            "Month": "Aug 2026",
            "Plaza": "TP02",
            "Bill No": "TPW-2026-08-02",
            "Tariff": "HT Commercial",
            "Contract Demand (kVA)": 250,
            "Billed kWh": 16900.0,
            "Metered kWh (JUNO)": 16720.0,
            "Variance kWh": 180.0,
            "Variance %": 1.1,
            "PF": 0.97,
            "Fixed Charges": 62500.0,
            "Energy Charges": 132665.0,
            "Total Amount": 230000.0,
            "Paid": 230000.0,
            "Balance": 0.0,
            "Status": "Paid",
            "Meter Rent Count": "46/60",
            "Security Deposit": "64,391.05",
            "Bill Period": "02/07/2026 - 01/08/2026",
            "Bill Days/Months": "31/1.0000",
            "Meter Sl. No.": "TWN20045",
            "a. Energy Charges": "1,31,400.00",
            "Slab Normal - KWH": "9750",
            "Slab Peak - KWH": "8010",
            "Slab Solar - KWH": "4520",
            "DPS(Rs.)": "0.00",
            "Tariff Category": "GENERAL PURPOSE >= 110 kVA",
            "Division": "SEED SAMBALPUR",
            "Sub-Division": "SDO RENGALI",
            "Section": "ESO SASON",
        },
        {
            "Month": "Aug 2026",
            "Plaza": "TP03",
            "Bill No": "TPW-2026-08-03",
            "Tariff": "HT Commercial",
            "Contract Demand (kVA)": 200,
            "Billed kWh": 13400.0,
            "Metered kWh (JUNO)": 13310.0,
            "Variance kWh": 90.0,
            "Variance %": 0.7,
            "PF": 0.98,
            "Fixed Charges": 50000.0,
            "Energy Charges": 105190.0,
            "Total Amount": 178000.0,
            "Paid": 178000.0,
            "Balance": 0.0,
            "Status": "Paid",
            "Meter Rent Count": "33/60",
            "Security Deposit": "1,79,770.00",
            "Bill Period": "02/07/2026 - 01/08/2026",
            "Bill Days/Months": "31/1.0000",
            "Meter Sl. No.": "TWSL12001179",
            "a. Energy Charges": "44,120.00",
            "Slab Normal - KWH": "5310",
            "Slab Peak - KWH": "2380",
            "Slab Solar - KWH": "0",
            "DPS(Rs.)": "0.00",
            "Tariff Category": "PUBLIC LIGHT",
            "Division": "JED JHARSUGUDA",
            "Sub-Division": "SDO-I JHARSUGUDA",
            "Section": "ESO SAHAPADA",
        },
        {
            "Month": "Jul 2026",
            "Plaza": "TP01",
            "Bill No": "TPW-2026-07-01",
            "Tariff": "HT Commercial",
            "Contract Demand (kVA)": 250,
            "Billed kWh": 18600.0,
            "Metered kWh (JUNO)": 18450.0,
            "Variance kWh": 150.0,
            "Variance %": 0.8,
            "PF": 0.97,
            "Fixed Charges": 62500.0,
            "Energy Charges": 146010.0,
            "Total Amount": 250000.0,
            "Paid": 250000.0,
            "Balance": 0.0,
            "Status": "Paid",
            "Meter Rent Count": "32/60",
            "Security Deposit": "36,360.14",
            "Bill Period": "02/06/2026 - 01/07/2026",
            "Bill Days/Months": "30/1.0000",
            "Meter Sl. No.": "10029454",
            "a. Energy Charges": "16,100.00",
            "Slab Normal - KWH": "2300",
            "Slab Peak - KWH": "1310",
            "Slab Solar - KWH": "22",
            "DPS(Rs.)": "0.00",
            "Tariff Category": "PUBLIC LIGHT",
            "Division": "SED SAMBALPUR",
            "Sub-Division": "SDO-I SAMBALPUR",
            "Section": "ESO RE SECTION",
        },
        {
            "Month": "Jul 2026",
            "Plaza": "TP02",
            "Bill No": "TPW-2026-07-02",
            "Tariff": "HT Commercial",
            "Contract Demand (kVA)": 250,
            "Billed kWh": 17100.0,
            "Metered kWh (JUNO)": 16950.0,
            "Variance kWh": 150.0,
            "Variance %": 0.9,
            "PF": 0.97,
            "Fixed Charges": 62500.0,
            "Energy Charges": 134235.0,
            "Total Amount": 232000.0,
            "Paid": 232000.0,
            "Balance": 0.0,
            "Status": "Paid",
            "Meter Rent Count": "45/60",
            "Security Deposit": "64,391.05",
            "Bill Period": "02/06/2026 - 01/07/2026",
            "Bill Days/Months": "30/1.0000",
            "Meter Sl. No.": "TWN20045",
            "a. Energy Charges": "1,33,000.00",
            "Slab Normal - KWH": "9800",
            "Slab Peak - KWH": "8050",
            "Slab Solar - KWH": "4580",
            "DPS(Rs.)": "0.00",
            "Tariff Category": "GENERAL PURPOSE >= 110 kVA",
            "Division": "SEED SAMBALPUR",
            "Sub-Division": "SDO RENGALI",
            "Section": "ESO SASON",
        },
        {
            "Month": "Jul 2026",
            "Plaza": "TP03",
            "Bill No": "TPW-2026-07-03",
            "Tariff": "HT Commercial",
            "Contract Demand (kVA)": 200,
            "Billed kWh": 13600.0,
            "Metered kWh (JUNO)": 13480.0,
            "Variance kWh": 120.0,
            "Variance %": 0.9,
            "PF": 0.98,
            "Fixed Charges": 50000.0,
            "Energy Charges": 106760.0,
            "Total Amount": 180000.0,
            "Paid": 180000.0,
            "Balance": 0.0,
            "Status": "Paid",
            "Meter Rent Count": "32/60",
            "Security Deposit": "1,79,770.00",
            "Bill Period": "02/06/2026 - 01/07/2026",
            "Bill Days/Months": "30/1.0000",
            "Meter Sl. No.": "TWSL12001179",
            "a. Energy Charges": "44,900.00",
            "Slab Normal - KWH": "5390",
            "Slab Peak - KWH": "2400",
            "Slab Solar - KWH": "0",
            "DPS(Rs.)": "0.00",
            "Tariff Category": "PUBLIC LIGHT",
            "Division": "JED JHARSUGUDA",
            "Sub-Division": "SDO-I JHARSUGUDA",
            "Section": "ESO SAHAPADA",
        },
    ])


def get_demo_bill_extraction_result(bill_id: str = "EB-26-1042"):
    return {
        "bill_id": bill_id,
        "discom_name": "TP Western Odisha Distribution Limited (TPWODL)",
        "consumer_number": "042918840192",
        "consumer_name": "Sambalpur Rourkela Tollway Private Limited",
        "toll_plaza": "TP01 (Baragarh)",
        "meter_number": "SR-E-EM-EB-000TP01",
        "billing_period": "01-Sep-2026 to 30-Sep-2026",
        "due_date": "15-Oct-2026",
        "tariff_category": "HT Commercial - 11kV Supply",
        "contract_demand_kva": 250.0,
        "recorded_demand_kva": 218.4,
        "previous_reading_kwh": 41280.0,
        "current_reading_kwh": 59700.0,
        "billed_units_kwh": 18420.0,
        "billed_kvah": 18795.0,
        "power_factor": 0.98,
        "pf_incentive_inr": -3684.0,
        "energy_charges_inr": 144597.0,
        "demand_charges_inr": 62500.0,
        "electricity_duty_inr": 8600.0,
        "fuel_surcharge_inr": 4820.0,
        "total_bill_amount_inr": 248000.0,
        "extraction_confidence": 99.4,
        "extracted_date": "2026-10-02 09:14:22",
        # 14 extracted fields requested by user
        "meter_rent_count": "34/60",
        "security_deposit": "36,360.14",
        "bill_period": "02/08/2026 - 01/09/2026",
        "bill_days_months": "30/1.0000",
        "meter_sl_no": "10029454",
        "energy_charges_a": "16,405.20",
        "slab_normal_kwh": "2313",
        "slab_peak_kwh": "1334",
        "slab_solar_kwh": "25",
        "dps_rs": "32.99",
        "division": "SED SAMBALPUR",
        "sub_division": "SDO-I SAMBALPUR",
        "section": "ESO RE SECTION",
        "meter_reconciliation": {
            "meter_interval_sum_kwh": 18200.0,
            "discom_billed_kwh": 18420.0,
            "variance_kwh": 220.0,
            "variance_pct": 1.2,
            "audit_verdict": "ACCEPTABLE (Within 2% HT distribution transformer loss tolerance)",
        },
    }


# ---------------------------------------------------------------------------
# Operator Tracking & Plaza Compliance Data
# ---------------------------------------------------------------------------

def get_demo_operator_tracking():
    if not is_demo_mode():
        return pd.DataFrame(columns=[
            "Operator ID", "Operator Name", "Role", "Plaza", "Shift", "Total Entries",
            "Flagged Errors", "Active Errors", "Accuracy %", "Error Details", "Status"
        ])

    all_exc = get_demo_exceptions()
    overrides = st.session_state.get("exception_overrides", {})

    def is_exc_open(eid):
        return overrides.get(eid, {}).get("status", "OPEN" if eid not in ("EXC-1006", "EXC-1007") else ("RESOLVED" if eid == "EXC-1006" else "ACCEPTED_EXCEPTION")) == "OPEN"

    return pd.DataFrame([
        {
            "Operator ID": "OP-TP02-02",
            "Operator Name": "Rajesh Swain",
            "Role": "Shift Operator",
            "Plaza": "TP02",
            "Shift": "Shift B (14:00 - 22:00)",
            "Total Entries": 1956,
            "Flagged Errors": 3,
            "Active Errors": sum([is_exc_open("EXC-1003"), is_exc_open("EXC-1004"), is_exc_open("EXC-1005")]),
            "Accuracy %": 98.4,
            "Error Details": "3 typos in DG Log: PF 98.0 omitted decimal, 9590.0 counter, 1210.0 runtime",
            "Status": "NEEDS_ATTENTION" if any([is_exc_open("EXC-1003"), is_exc_open("EXC-1004"), is_exc_open("EXC-1005")]) else "RESOLVED_TRAINED",
        },
        {
            "Operator ID": "OP-TP01-01",
            "Operator Name": "Sunil Kullu",
            "Role": "Station Operator",
            "Plaza": "TP01",
            "Shift": "Shift A (06:00 - 14:00)",
            "Total Entries": 797,
            "Flagged Errors": 1,
            "Active Errors": 1 if is_exc_open("EXC-1001") else 0,
            "Accuracy %": 99.8,
            "Error Details": "EB Incomer counter transposed: 1295.0 instead of 1325.0 kWh",
            "Status": "NEEDS_ATTENTION" if is_exc_open("EXC-1001") else "RESOLVED_TRAINED",
        },
        {
            "Operator ID": "TC-TP01-04",
            "Operator Name": "Pritam Mahapatra",
            "Role": "Electrical Technician",
            "Plaza": "TP01",
            "Shift": "Shift A (06:00 - 14:00)",
            "Total Entries": 797,
            "Flagged Errors": 1,
            "Active Errors": 1 if is_exc_open("EXC-1002") else 0,
            "Accuracy %": 99.8,
            "Error Details": "EB kVAh reversed: 1365.0 instead of 1395.0 kVAh",
            "Status": "NEEDS_ATTENTION" if is_exc_open("EXC-1002") else "RESOLVED_TRAINED",
        },
        {
            "Operator ID": "TC-TP03-03",
            "Operator Name": "Deepak Patel",
            "Role": "UPS Technician",
            "Plaza": "TP03",
            "Shift": "Shift B (14:00 - 22:00)",
            "Total Entries": 1462,
            "Flagged Errors": 1,
            "Active Errors": 1 if is_exc_open("EXC-1007") else 0,
            "Accuracy %": 99.3,
            "Error Details": "UPS battery voltage dip recorded as transient warning (195.0 V)",
            "Status": "NEEDS_ATTENTION" if is_exc_open("EXC-1007") else "VERIFIED_ACCURATE",
        },
        {
            "Operator ID": "TC-TP01-02",
            "Operator Name": "Anil Seth",
            "Role": "Senior Electrician",
            "Plaza": "TP01",
            "Shift": "Shift A (06:00 - 14:00)",
            "Total Entries": 1300,
            "Flagged Errors": 1,
            "Active Errors": 1 if is_exc_open("EXC-1006") else 0,
            "Accuracy %": 99.5,
            "Error Details": "Transformer primary tap voltage imbalance 2.8% logged",
            "Status": "NEEDS_ATTENTION" if is_exc_open("EXC-1006") else "VERIFIED_ACCURATE",
        },
    ])


def get_demo_plaza_monitoring_compliance():
    if not is_demo_mode():
        return pd.DataFrame(columns=[
            "Plaza", "Shift", "Supervisor Name", "Role", "Equipment Inspected",
            "Last Monitored Time", "Inspection Status", "Compliance SLA", "Action Required"
        ])

    # Tracks shift supervisor daily inspection compliance answering "who has not monitored energy consumption in plaza"
    return pd.DataFrame([
        {
            "Plaza": "TP01",
            "Shift": "Shift A (06:00 - 14:00)",
            "Supervisor Name": "Sunil Kullu",
            "Role": "Shift Supervisor",
            "Equipment Inspected": "EB Incomer, DG 1 & 2, Solar 1, HT Transformer 2, UPS 2 & 3",
            "Last Monitored Time": "Today, 13:45",
            "Inspection Status": "VERIFIED & SIGNED OFF",
            "Compliance SLA": "ON TIME (100%)",
            "Action Required": "None",
        },
        {
            "Plaza": "TP01",
            "Shift": "Shift B (14:00 - 22:00)",
            "Supervisor Name": "Prabodh Rana",
            "Role": "Energy Operations Lead",
            "Equipment Inspected": "EB Incomer, DG 1 & 2, Solar 1, HT Transformer 2, UPS 2 & 3",
            "Last Monitored Time": "Today, 21:30",
            "Inspection Status": "VERIFIED & SIGNED OFF",
            "Compliance SLA": "ON TIME (100%)",
            "Action Required": "None",
        },
        {
            "Plaza": "TP01",
            "Shift": "Shift C (22:00 - 06:00)",
            "Supervisor Name": "Anil Seth",
            "Role": "Night Station In-Charge",
            "Equipment Inspected": "EB Incomer, DG Standby, Server Room UPS",
            "Last Monitored Time": "Yesterday, 05:30",
            "Inspection Status": "DUE TODAY",
            "Compliance SLA": "IN PROGRESS (< 2 hrs remaining)",
            "Action Required": "Awaiting end-of-shift telemetry sync",
        },
        {
            "Plaza": "TP02",
            "Shift": "Shift A (06:00 - 14:00)",
            "Supervisor Name": "Pritam Mahapatra",
            "Role": "Shift Supervisor",
            "Equipment Inspected": "EB Meter, DG 3 & 4, Solar 2, Transformer 3, UPS 4 & 9",
            "Last Monitored Time": "Today, 13:15",
            "Inspection Status": "VERIFIED & SIGNED OFF",
            "Compliance SLA": "ON TIME (100%)",
            "Action Required": "None",
        },
        {
            "Plaza": "TP02",
            "Shift": "Shift B (14:00 - 22:00)",
            "Supervisor Name": "Rajesh Swain",
            "Role": "Shift Operator",
            "Equipment Inspected": "EB Meter, DG 3 & 4, Solar 2, Transformer 3, UPS 4 & 9",
            "Last Monitored Time": "Today, 20:45",
            "Inspection Status": "VERIFIED & SIGNED OFF",
            "Compliance SLA": "DELAYED (4-hour delay logged)",
            "Action Required": "Review DG yard transcription typos",
        },
        {
            "Plaza": "TP02",
            "Shift": "Shift C (22:00 - 06:00)",
            "Supervisor Name": "Bikram Das",
            "Role": "Night Operator",
            "Equipment Inspected": "EB Meter, DG Standby, UPS 4 & 9",
            "Last Monitored Time": "Today, 05:15",
            "Inspection Status": "VERIFIED & SIGNED OFF",
            "Compliance SLA": "ON TIME (100%)",
            "Action Required": "None",
        },
        {
            "Plaza": "TP03",
            "Shift": "Shift A (06:00 - 14:00)",
            "Supervisor Name": "Ranjan Khadia",
            "Role": "Plaza Manager",
            "Equipment Inspected": "EB Meter, DG 5 & 6, Solar 3, Transformer 1, UPS 10 & 12",
            "Last Monitored Time": "Today, 12:50",
            "Inspection Status": "VERIFIED & SIGNED OFF",
            "Compliance SLA": "ON TIME (100%)",
            "Action Required": "None",
        },
        {
            "Plaza": "TP03",
            "Shift": "Shift B (14:00 - 22:00)",
            "Supervisor Name": "Deepak Patel",
            "Role": "Shift Supervisor",
            "Equipment Inspected": "EB Meter, DG 5 & 6, Solar 3, Transformer 1, UPS 10 & 12",
            "Last Monitored Time": "Today, 21:00",
            "Inspection Status": "VERIFIED & SIGNED OFF",
            "Compliance SLA": "ON TIME (100%)",
            "Action Required": "None",
        },
        {
            "Plaza": "TP03",
            "Shift": "Shift C (22:00 - 06:00)",
            "Supervisor Name": "Sanjeev Sahu",
            "Role": "Night Technician",
            "Equipment Inspected": "EB Incomer, DG Standby, Server Room UPS",
            "Last Monitored Time": "21 Oct 2026, 05:40 (> 28 hrs ago)",
            "Inspection Status": "MISSED / OVERDUE",
            "Compliance SLA": "VIOLATION (> 28 hrs Unmonitored!)",
            "Action Required": "🚨 ESCALATED: Automated SMS & Email dispatched to Plaza Manager Ranjan Khadia",
        },
    ])
