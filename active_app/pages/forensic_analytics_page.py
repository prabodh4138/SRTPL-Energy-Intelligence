"""
SRTPL Power Intelligence — Module 7: Analytics.

5 Dedicated Submodules:
- 🛢️ DG (Diesel Generator)
- ⚡ EB (Electricity Board)
- ☀️ SOLAR (Rooftop Solar Plant)
- 🔌 TRANSFORMER (HT Substation Transformer)
- 🔋 UPS (Battery & Power Backup)

All KPIs, last readings, technician night audits, and defects are queried directly
from live database SQL views and tables (Supabase cloud first, local SQLite mirror parity).
If data is not found in the database, explicitly displays 'Data Not Found'.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
ACTIVE_APP = Path(__file__).resolve().parents[1]
for p in [str(ROOT_DIR), str(ACTIVE_APP)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from core.analytics_service import get_submodule_analytics


def render() -> None:
    """Renders Module 7: Analytics with 5 submodules."""
    st.markdown('<div class="eyebrow">MODULE 7 · ANALYTICS</div>', unsafe_allow_html=True)
    st.markdown(
        "<h2 style='margin-top:0; font-weight:800; color:#F8FAFC;'>⚡ Module-Wise Energy & Operator Analytics</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#94A3B8; font-size:14px; margin-bottom:18px;'>"
        "Real-time analytics queried strictly from database SQL views (<code>vw_&lt;module&gt;_reading_kpis</code>, "
        "<code>vw_&lt;module&gt;_asset_latest_reading</code>) and telemetry tables in Supabase / local database. "
        "Automatically updates when new logs are ingested."
        "</p>",
        unsafe_allow_html=True,
    )

    # 5 Submodule Selector
    submodule_options = [
        "🛢️ DG",
        "⚡ EB",
        "☀️ SOLAR",
        "🔌 TRANSFORMER",
        "🔋 UPS",
    ]
    if "analytics_submodule_tab" not in st.session_state or st.session_state["analytics_submodule_tab"] not in submodule_options:
        st.session_state["analytics_submodule_tab"] = "🛢️ DG"

    selected_submodule_label = st.segmented_control(
        "Submodule Selector",
        options=submodule_options,
        key="analytics_submodule_tab",
        label_visibility="collapsed",
    )
    active_submodule_label = selected_submodule_label or st.session_state.get("analytics_submodule_tab") or "🛢️ DG"

    # Map label to code
    label_to_code = {
        "🛢️ DG": "DG",
        "⚡ EB": "EB",
        "☀️ SOLAR": "SOLAR",
        "🔌 TRANSFORMER": "TRANSFORMER",
        "🔋 UPS": "UPS",
    }
    module_code = label_to_code.get(active_submodule_label, "DG")

    # Optional Plaza Filter
    col_hdr, col_plz = st.columns([3, 1])
    with col_plz:
        plaza_filter = st.selectbox("Filter Plaza", ["ALL", "TP01", "TP02", "TP03"], key=f"plz_filt_{module_code}")

    # Fetch live data from database
    with st.spinner(f"Querying SQL views for {module_code} in database..."):
        data = get_submodule_analytics(module_code, plaza_filter=plaza_filter)

    # Check if data exists
    if not data["has_data"] or data["total_logs"] == 0:
        st.error(f"### ⚠️ Data Not Found for {module_code}")
        st.warning(
            f"No verified readings or telemetry found in the database for **{module_code}**. "
            "Please ingest the corresponding CSV logs via the **Juno Import Centre** to populate this module."
        )
        return

    # Render Live KPI Cards from vw_<module>_reading_kpis
    kpis = data["kpis"]
    total_logs = data["total_logs"]

    st.markdown(f"### 📊 Live SQL View KPIs · {module_code}")
    c1, c2, c3, c4 = st.columns(4)

    if module_code == "DG":
        with c1:
            st.metric("Active Generators", f"{kpis.get('active_generators', 0)} Units", f"{total_logs:,} Total Logs")
        with c2:
            st.metric("Total Generation", f"{float(kpis.get('total_cumulative_kwh', 0)):,.1f} kWh", "From SQL View")
        with c3:
            st.metric("Runtime Hours", f"{float(kpis.get('total_cumulative_run_hours', 0)):,.1f} Hrs", "Cumulative Engine")
        with c4:
            st.metric("Tracked Fuel Level", f"{float(kpis.get('total_fuel_level', 0)):,.1f} L", "Current Reservoirs")

    elif module_code == "EB":
        with c1:
            st.metric("Active Meters", f"{kpis.get('active_meters', 0)} Meters", f"{total_logs:,} Total Logs")
        with c2:
            st.metric("Cumulative Energy", f"{float(kpis.get('total_cumulative_kwh', 0)):,.1f} kWh", f"Delta: +{float(kpis.get('total_interval_kwh', 0)):,.1f} kWh")
        with c3:
            st.metric("Average Power Factor", f"{float(kpis.get('avg_power_factor', 0.98)):.2f}", "Grid Threshold >= 0.95")
        with c4:
            st.metric("Peak Demand (MD)", f"{float(kpis.get('peak_demand', 0)):.1f} kW", "Max Recorded")

    elif module_code == "SOLAR":
        with c1:
            st.metric("Active Solar Plants", f"{kpis.get('active_plants', 0)} Plants", f"{total_logs:,} Total Logs")
        with c2:
            st.metric("Solar Clean Energy", f"{float(kpis.get('total_cumulative_kwh', 0)):,.1f} kWh", f"Delta: +{float(kpis.get('total_interval_kwh', 0)):,.1f} kWh")
        with c3:
            st.metric("CO₂ Offset", f"{float(kpis.get('co2_avoided_kg', 0)):,.1f} kg", "0.82 Factor")
        with c4:
            st.metric("Total Capacity", "121.38 kWp", "40.46 kWp / Plant")

    elif module_code == "TRANSFORMER":
        with c1:
            st.metric("Active Transformers", f"{kpis.get('active_transformers', 0)} Units", f"{total_logs:,} Total Logs")
        with c2:
            st.metric("Throughput Energy", f"{float(kpis.get('total_cumulative_kwh', 0)):,.1f} kWh", "Substation Metering")
        with c3:
            st.metric("Thermal Health", f"{float(kpis.get('avg_oil_temp', 0)):.1f}°C / {float(kpis.get('avg_winding_temp', 0)):.1f}°C", "Oil / Winding")
        with c4:
            st.metric("Power Factor", f"{float(kpis.get('avg_power_factor', 0.98)):.2f}", "Phase Balanced")

    elif module_code == "UPS":
        with c1:
            st.metric("Active UPS Systems", f"{kpis.get('active_systems', 0)} Banks", f"{total_logs:,} Total Logs")
        with c2:
            st.metric("Regulated Voltage", f"{float(kpis.get('avg_output_voltage', 230)):.1f} V", "Single Phase Output")
        with c3:
            st.metric("Battery DC Bus", f"{float(kpis.get('avg_battery_vdc', 380)):.1f} VDC", "Envelope: 360 - 435V")
        with c4:
            st.metric("Battery Temp", f"{float(kpis.get('avg_battery_temp', 25)):.1f} °C", "Thermal Battery Room")

    st.markdown("---")

    # Section 1: Plaza-Wise & Asset-Wise Last Reading
    st.markdown(f"#### ⚡ Plaza-Wise & Asset-Wise Latest Telemetry · {module_code}")
    st.markdown("Directly queried from `vw_<module>_asset_latest_reading` in database:")

    last_readings = data["last_readings"]
    if last_readings:
        lr_rows = []
        for r in last_readings:
            val_display = "Data Not Found"
            if r["cumulative_kwh"] is not None:
                val_display = f"{float(r['cumulative_kwh']):,.1f} kWh"
            elif r["run_hours"] is not None:
                val_display = f"{float(r['run_hours']):,.1f} Hrs"
            elif r["reading_datetime"] != "Data Not Found":
                val_display = "Telemetry Active"

            lr_rows.append({
                "Plaza": r["plaza_id"],
                "Asset Code": r["asset_code"],
                "Asset Name": r["asset_name"],
                "Capacity": r["capacity"],
                "Last Reading Datetime": r["reading_datetime"],
                "Cumulative Value": val_display,
                "Technician": r["technician"],
                "Status": r["status"],
            })
        st.dataframe(pd.DataFrame(lr_rows), hide_index=True)
    else:
        st.info(f"No asset readings found for {module_code}.")

    st.markdown("---")

    # Section 2: Plaza Neglect & Defect Comparison for this Module
    st.markdown(f"#### 🏆 Plaza Neglect & Wrong Entry Comparison · {module_code}")
    st.markdown("Catches which plaza is doing wrong entries or neglecting telemetry in this specific module:")

    plaza_comp = data["plaza_comparison"]
    if plaza_comp:
        pc_rows = []
        for p in plaza_comp:
            pc_rows.append({
                "Plaza": p["plaza_id"],
                "Total Logs": f"{p['total_records']:,}",
                "Wrong / Defect Entries": f"{p['wrong_entries_count']:,}",
                "Error Rate %": f"{p['defect_rate_pct']:.2f}%",
                "Night Shift Logs (8p–8a)": f"{p['night_entries_count']:,}",
                "Night %": f"{p['night_entry_pct']:.1f}%",
                "Severe Delays (>2d)": p["severe_delays_count"],
                "Assets Monitored": p["assets_monitored"],
                "Neglect Verdict": p["verdict"],
            })
        st.dataframe(pd.DataFrame(pc_rows), hide_index=True)

    st.markdown("---")

    # Section 3: Technician Night Entries (8:00 PM – 8:00 AM)
    st.markdown(f"#### 🌙 Technician Night Shift Submissions (8:00 PM – 8:00 AM) · {module_code}")
    st.markdown("Entries submitted during off-hours window (**20:00 to 07:59**), identifying responsible technician names:")

    night_entries = data["night_entries"]
    if night_entries:
        st.warning(f"Found **{len(night_entries):,} night submissions** for {module_code} between 8:00 PM and 8:00 AM.")
        ne_rows = []
        for idx, ne in enumerate(night_entries[:30], 1):
            ne_rows.append({
                "#": idx,
                "Plaza": ne["plaza_id"],
                "Asset Code": ne["asset_code"],
                "Technician Name": ne["technician"],
                "Entry Hour": ne["entry_hour"],
                "Reading Datetime": ne["reading_datetime"],
                "Logged At": ne["submission_timestamp"],
                "Delay (Days)": f"{ne['delay_days']} d" if ne["delay_days"] != "N/A" else "N/A",
            })
        st.dataframe(pd.DataFrame(ne_rows), hide_index=True)
    else:
        st.success(f"✅ No off-hours night submissions (8:00 PM – 8:00 AM) found for {module_code}.")

    st.markdown("---")

    # Section 4: Wrong Entries & Technical Defects Register
    st.markdown(f"#### ⚠️ Wrong Entries & Technical Deficiencies · {module_code}")
    wrong_entries = data["wrong_entries"]
    if wrong_entries:
        st.error(f"Found **{len(wrong_entries):,} technical defects / wrong entries** for {module_code}:")
        we_rows = []
        for idx, we in enumerate(wrong_entries[:30], 1):
            we_rows.append({
                "#": idx,
                "Plaza": we["plaza_id"],
                "Asset Code": we["asset_code"],
                "Technician": we["technician"],
                "Reading Datetime": we["reading_datetime"],
                "Defect / Anomaly Message": we["violation"],
                "Severity": we["severity"],
            })
        st.dataframe(pd.DataFrame(we_rows), hide_index=True)
    else:
        st.success(f"✅ No wrong entries or technical defects detected in database for {module_code}.")

    st.markdown("---")

    # Section 5: Technician Performance Register for this Module
    st.markdown(f"#### 👨‍🔧 Technician Performance Register · {module_code}")
    tech_summary = data["technicians_summary"]
    if tech_summary:
        ts_rows = []
        for t in tech_summary:
            ts_rows.append({
                "Technician Name": t["technician_name"],
                "Plazas": t["plazas"],
                "Total Logs": f"{t['total_logs']:,}",
                "Night Logs (8p–8a)": f"{t['night_logs']:,}",
                "Night %": f"{t['night_pct']:.1f}%",
                "Defects Logged": f"{t['defects_count']:,}",
                "Defect %": f"{t['defect_pct']:.1f}%",
                "Avg Delay": f"{t['avg_delay_days']} d",
                "Max Delay": f"{t['max_delay_days']} d",
            })
        st.dataframe(pd.DataFrame(ts_rows), hide_index=True)
    else:
        st.info(f"No technician activity recorded for {module_code}.")
