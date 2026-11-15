"""Reusable, interactive Streamlit Reading View component for Module 2 Equipment Readings.

Supports EB, DG, Solar, Transformer, and UPS.
Provides:
- Live KPI computation directly from authoritative database SQL Views (vw_<module>_reading_kpis)
- Dedicated "📌 Last Reading of Each Asset" view (vw_<module>_asset_latest_reading)
- 100% In-memory data extraction (CSV & Excel) with ZERO temporary files on disk
- Interactive filter bar (Plaza, Date, Search)
- Filterable Historical Validated Meter Readings table
- Inline Manual Reading Logging form with SQLite persistence
- Direct navigation shortcut to corresponding Juno Import Centre
"""
from __future__ import annotations

import datetime
from typing import Any
import pandas as pd
import streamlit as st

from backend.routers.readings import get_readings, add_reading, AddReadingPayload
from core.cloud_views_service import (
    fetch_module_kpis_from_sql_view,
    fetch_asset_latest_readings_from_sql_view,
    extract_equipment_readings_in_memory,
)


def _format_latest_assets_df(df: pd.DataFrame, atype: str) -> pd.DataFrame:
    """Formats raw SQL view columns into crisp, user-friendly dashboard presentation."""
    if df.empty:
        return df

    display_df = df.copy()

    # Fill NA status
    if "data_quality_status" in display_df.columns:
        display_df["data_quality_status"] = display_df.apply(
            lambda row: row["data_quality_status"] if pd.notna(row.get("reading_datetime")) else "AWAITING TELEMETRY",
            axis=1,
        )

    # Base column mappings
    rename_map = {
        "asset_code": "Asset Code",
        "asset_name": "Asset Name",
        "plaza_id": "Toll Plaza",
        "capacity_kva": "Capacity (kVA/kW)",
        "reading_datetime": "Last Reading Time",
        "data_quality_status": "Status",
        "remarks": "Remarks",
    }

    if atype == "eb":
        rename_map.update({
            "latest_cumulative_kwh": "Last Active (kWh)",
            "latest_interval_kwh": "Interval (kWh)",
            "latest_cumulative_kvah": "Last Apparent (kVAh)",
            "latest_pf": "Power Factor",
            "latest_maximum_demand": "Peak Demand (kVA)",
        })
    elif atype == "dg":
        rename_map.update({
            "latest_cumulative_kwh": "Last Generation (kWh)",
            "latest_run_hours": "Cumulative Run Hours",
            "latest_fuel_level": "Fuel Level (L)",
            "latest_load_pct": "Load (%)",
            "latest_pf": "Power Factor",
            "operational_status": "Operational State",
        })
    elif atype == "solar":
        rename_map.update({
            "latest_cumulative_kwh": "Last Clean Generation (kWh)",
            "latest_interval_kwh": "Recent Interval (kWh)",
        })
    elif atype == "transformer":
        rename_map.update({
            "latest_cumulative_kwh": "Throughput Energy (kWh)",
            "latest_oil_temp": "Oil Temp (°C)",
            "latest_winding_temp": "Winding Temp (°C)",
            "latest_pf": "Substation PF",
        })
    elif atype == "ups":
        rename_map.update({
            "latest_output_voltage": "Output Voltage (V)",
            "latest_output_current": "Output Current (A)",
            "latest_output_frequency": "Frequency (Hz)",
            "latest_battery_vdc": "Battery DC Bus (V)",
            "latest_battery_temp": "Battery Temp (°C)",
        })

    cols_to_keep = [c for c in rename_map.keys() if c in display_df.columns]
    formatted = display_df[cols_to_keep].rename(columns=rename_map)

    # Format numeric floats for display
    for col in formatted.columns:
        if formatted[col].dtype in ("float64", "float32"):
            formatted[col] = formatted[col].apply(lambda v: f"{v:,.2f}" if pd.notna(v) else "—")

    return formatted


def render_equipment_reading_view(
    asset_type: str,
    title: str,
    subtitle: str,
    unit_label: str = "kWh",
    default_meter: str = "",
    sample_assets: list[dict[str, Any]] | None = None,
    rules: list[str] | None = None,
) -> None:
    """Renders the complete, interactive reading view for any equipment module."""
    atype = asset_type.lower().strip()
    st.title(title)
    st.caption(subtitle)

    # 1. Top Filter Row: Plaza Selector
    f_col1, f_col2 = st.columns([1, 2])
    plaza_filter = f_col1.segmented_control(
        "Toll Plaza Filter",
        options=["ALL", "TP01", "TP02", "TP03"],
        default="ALL",
        key=f"plz_filter_top_{atype}",
    )
    selected_plaza = plaza_filter if plaza_filter and plaza_filter != "ALL" else None

    # 2. Executive KPIs strictly fetched from authoritative SQL View
    st.subheader(f"📈 Executive KPI Summary (SQL View)")
    kpi_res = fetch_module_kpis_from_sql_view(atype, plaza=selected_plaza)
    kpis = kpi_res.get("cards", [])

    if kpis:
        kpi_cols = st.columns(len(kpis))
        for idx, k in enumerate(kpis):
            kpi_cols[idx].metric(
                label=k.get("label", "Metric"),
                value=k.get("value", "—"),
                delta=k.get("sub", ""),
            )
    st.caption(f"🏛️ Authoritative Executive KPIs strictly sourced from database SQL View: `vw_{atype}_reading_kpis`")

    st.markdown("---")

    # 3. Dedicated Section: Last Reading of Each Asset
    st.subheader(f"📌 Last Reading of Each Asset (SQL View: vw_{atype}_asset_latest_reading)")
    st.caption(f"Real-time operational snapshot of every inventoried {atype.upper()} unit across all toll plazas.")

    latest_raw_df = fetch_asset_latest_readings_from_sql_view(atype, plaza=selected_plaza)

    if not latest_raw_df.empty:
        total_assets = len(latest_raw_df)
        with_telemetry = int(latest_raw_df["reading_datetime"].notna().sum()) if "reading_datetime" in latest_raw_df.columns else 0
        awaiting_telemetry = total_assets - with_telemetry

        s_col1, s_col2, s_col3 = st.columns(3)
        s_col1.metric("Inventoried Assets", f"{total_assets} Units")
        s_col2.metric("Active Telemetry Synced", f"{with_telemetry} Units")
        s_col3.metric("Awaiting Telemetry", f"{awaiting_telemetry} Units")

        formatted_latest = _format_latest_assets_df(latest_raw_df, atype)
        st.dataframe(formatted_latest, width="stretch", hide_index=True)
    else:
        st.info(f"No asset records found in SQL View `vw_{atype}_asset_latest_reading`.")
        if sample_assets:
            st.markdown(f"#### Inventoried Baseline Units")
            st.dataframe(pd.DataFrame(sample_assets), width="stretch", hide_index=True)

    st.markdown("---")

    # 4. Useful Data Extraction (Strictly In-Memory Streaming, Zero Temporary Files)
    with st.container(border=True):
        st.markdown(f"### 💾 Useful Data Extraction (100% In-Memory Streaming)")
        st.caption("Export latest asset statuses and complete telemetry registers directly from database memory with zero temporary files created on disk.")

        # In-memory streaming extraction
        csv_bytes, csv_filename = extract_equipment_readings_in_memory(atype, format_type="csv", plaza=selected_plaza)
        xlsx_bytes, xlsx_filename = extract_equipment_readings_in_memory(atype, format_type="excel", plaza=selected_plaza)

        dl_c1, dl_c2 = st.columns(2)
        dl_c1.download_button(
            label=f"📥 Export {atype.upper()} Readings & Status (CSV)",
            data=csv_bytes,
            file_name=csv_filename,
            mime="text/csv",
            key=f"dl_mem_csv_{atype}",
            width="stretch",
        )
        dl_c2.download_button(
            label=f"📊 Export Full Equipment Dossier (Excel)",
            data=xlsx_bytes,
            file_name=xlsx_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"dl_mem_xlsx_{atype}",
            width="stretch",
        )

    st.markdown("---")

    # 5. Manual Entry Expander
    with st.expander(f"➕ Log Manual {title.split()[0]} Reading", expanded=False):
        st.markdown(f"Record an ad-hoc meter reading for **{title}** directly into local and cloud stores.")
        with st.form(key=f"manual_reading_form_{atype}"):
            col_p, col_m = st.columns(2)
            sel_plaza = col_p.selectbox("Toll Plaza", ["TP01", "TP02", "TP03"], key=f"sel_plz_{atype}")
            meter_val = col_m.text_input("Meter / Asset Code", value=default_meter, key=f"meter_code_{atype}")

            col_val, col_tech = st.columns(2)
            read_val = col_val.number_input(
                f"Reading Value ({unit_label})",
                min_value=0.0,
                step=1.0,
                format="%.2f",
                key=f"read_val_{atype}",
            )
            tech_val = col_tech.text_input(
                "Logged By / Technician",
                value=st.session_state.get("user", "admin@srtpl.com"),
                key=f"tech_val_{atype}",
            )

            notes_val = st.text_input("Remarks / Notes", placeholder="Ad-hoc physical log verification", key=f"notes_{atype}")

            submit_btn = st.form_submit_button("💾 Save Reading", type="primary", width="stretch")
            if submit_btn:
                if not meter_val.strip():
                    st.error("Please provide a valid Meter / Asset code.")
                elif read_val <= 0.0:
                    st.warning("Reading value must be greater than zero.")
                else:
                    try:
                        payload = AddReadingPayload(
                            meter_code=meter_val.strip(),
                            plaza=sel_plaza,
                            reading_value=float(read_val),
                            notes=notes_val.strip() if notes_val else f"Manual log by {tech_val}",
                        )
                        res = add_reading(atype, payload)
                        if res.get("status") == "SUCCESS":
                            st.success(f"✅ Reading for `{meter_val}` ({read_val} {unit_label}) saved successfully!")
                            st.rerun()
                        else:
                            st.error(f"Error saving reading: {res}")
                    except Exception as exc:
                        st.error(f"Could not save reading: {exc}")

    # 6. Governing Validation Rules Expander
    governing_rules = rules
    if governing_rules:
        with st.expander("🛡️ Equipment Governing Validation Protocols", expanded=False):
            for r in governing_rules:
                st.markdown(f"- **{r}**")

    # 7. Validated Historical Logs Table
    st.subheader(f"📊 Validated {title.split()[0]} Historical Telemetry Logs")

    data = get_readings(atype)
    records = data.get("records", [])

    if records:
        df_records = pd.DataFrame(records)

        # Search filter
        search_kw = st.text_input(
            "Filter Telemetry Logs by Meter Code, Technician, or Timestamp",
            placeholder="Search asset, timestamp, or technician...",
            key=f"search_kw_{atype}",
        )

        filtered = df_records.copy()
        if selected_plaza:
            filtered = filtered[filtered["plaza"].astype(str).str.upper() == selected_plaza]

        if search_kw.strip():
            kw = search_kw.strip().lower()
            filtered = filtered[
                filtered.apply(
                    lambda row: any(kw in str(v).lower() for v in row.values),
                    axis=1,
                )
            ]

        display_cols = [
            c for c in [
                "date", "plaza", "meter_code", "curr_kwh", "diff_kwh",
                "curr_kvah", "pf", "power_factor", "run_hours", "status",
                "created_by", "notes"
            ] if c in filtered.columns
        ]

        st.caption(f"Showing **{len(filtered)}** of {len(df_records)} total validated record(s)")
        st.dataframe(filtered[display_cols] if display_cols else filtered, width="stretch", hide_index=True)
    else:
        st.info(
            f"💡 **Live Telemetry Notice**: No JUNO CSV logs have been ingested for {title} yet. "
            f"You can log manual readings above, or import batch CSV logs via **{atype.upper()} JUNO Import** in the sidebar."
        )

    # 8. Sidebar link notice
    st.info(f"📂 To upload untouched vendor JUNO log files, navigate to **{atype.upper()} JUNO Import** in the sidebar.")
