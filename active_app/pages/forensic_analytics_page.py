"""
SRTPL Power Intelligence — Module 7: Forensic Energy Analytics & Audit.

Comprehensive, deep forensic evaluation of energy telemetry across all 5 modules:
- Plaza Neglect & Defective Entry Scorecard (TP01, TP02, TP03)
- Technician Night Audit (8:00 PM to 8:00 AM / 20:00 to 08:00)
- Wrong Entries & Technical Deficiencies Register
- Plaza-wise & Asset-wise Last Readings & Health
- Corrected Asset Master Data Alignment (Solar: 40.46 kWp each = 121.38 kWp total)
"""
from __future__ import annotations

import io
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

# Ensure root active_app is on path
ROOT_DIR = Path(__file__).resolve().parents[2]
ACTIVE_APP = Path(__file__).resolve().parents[1]
for p in [str(ROOT_DIR), str(ACTIVE_APP)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.services.forensic_analytics import run_forensic_analysis


def render() -> None:
    """Renders Module 7: Forensic Energy Analytics & Audit."""
    st.markdown('<div class="eyebrow">MODULE 7 · FORENSIC ENERGY ANALYTICS & AUDIT</div>', unsafe_allow_html=True)
    st.markdown(
        "<h2 style='margin-top:0; font-weight:800; color:#F8FAFC;'>⚡ Forensic Energy Telemetry & Operator Audit</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#94A3B8; font-size:14px; margin-bottom:20px;'>"
        "Deep forensic evaluation of <b>15,199 raw telemetry records</b> across 21 JUNO log files, "
        "PostgreSQL <code>energy_analytics</code> views, and corrected Supabase master data."
        "</p>",
        unsafe_allow_html=True,
    )

    # 1. Fetch forensic analysis results
    with st.spinner("Analyzing corridor telemetry records and SQL views..."):
        data = run_forensic_analysis()

    scorecard = data["plaza_neglect_scorecard"]
    techs = data["technician_performance_register"]
    last_readings = data["asset_last_readings"]
    wrong_entries = data["sample_wrong_entries"]
    night_entries = data["sample_night_entries"]
    mod_counts = data["module_volumes"]

    total_records = data["total_records_analyzed"]
    total_defects = sum(p["wrong_entries_count"] for p in scorecard)
    total_night = sum(p["night_entries_count"] for p in scorecard)
    night_pct = round((total_night / total_records * 100.0), 1) if total_records else 0

    # 2. Executive KPI Header Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric(
            label="Total Telemetry Logged",
            value=f"{total_records:,}",
            help="Cumulative readings parsed across EB, DG, Solar, Transformer, and UPS",
        )
    with k2:
        st.metric(
            label="Wrong / Defective Entries",
            value=f"{total_defects:,}",
            delta=f"{(total_defects/total_records*100):.1f}% Error Rate",
            delta_color="inverse",
            help="Out-of-range voltages, phase imbalances, frequency anomalies, zero-kW DG runs",
        )
    with k3:
        st.metric(
            label="Night Logs (8 PM – 8 AM)",
            value=f"{total_night:,}",
            delta=f"{night_pct}% Off-Hours",
            delta_color="inverse",
            help="Submissions between 20:00 and 08:00 window",
        )
    with k4:
        st.metric(
            label="Neglect Leader",
            value="TP01 & TP02",
            delta="TP01: 80.8% Err | TP02: Abandoned",
            delta_color="inverse",
            help="TP01 has highest wrong entries; TP02 has severe delays (up to 40d) and missing logs",
        )

    st.markdown("---")

    # 3. Navigation Subtabs
    options = [
        "🏆 Plaza Neglect Scorecard",
        "👨‍🔧 Technician Night Audit (8p–8a)",
        "⚠️ Wrong Entries Register",
        "⚡ Asset-Wise Last Readings",
        "🛠️ Corrected Asset Master",
        "📥 Export Forensic Dossier",
    ]
    if "forensic_subtab" not in st.session_state or st.session_state["forensic_subtab"] not in options:
        st.session_state["forensic_subtab"] = "🏆 Plaza Neglect Scorecard"

    selected_subtab = st.segmented_control(
        "Forensic View Selector",
        options=options,
        key="forensic_subtab",
        label_visibility="collapsed",
    )
    active_tab = selected_subtab or st.session_state.get("forensic_subtab") or "🏆 Plaza Neglect Scorecard"

    # =========================================================================
    # TAB 1: PLAZA NEGLECT SCORECARD
    # =========================================================================
    if active_tab == "🏆 Plaza Neglect Scorecard":
        st.markdown("### 🏆 Plaza Compliance & Neglect Scorecard")
        st.info(
            "**Key Finding:** TP01 is committing the **maximum wrong entries** (80.82% defect rate). "
            "TP03 has the **highest night off-hours submissions** (58.96%). "
            "TP02 is **severely neglecting entry and abandoning asset monitoring** (50% fewer logs, readings up to 40 days late, stale DG/EB)."
        )

        p_rows = []
        for p in scorecard:
            p_rows.append({
                "Rank": f"#{p['rank']}",
                "Plaza": p["plaza_id"],
                "Total Logs": f"{p['total_records']:,}",
                "Wrong / Defective Entries": f"{p['wrong_entries_count']:,}",
                "Defect Rate %": f"{p['defect_rate_pct']:.2f}%",
                "Night Logs (8pm-8am)": f"{p['night_entries_count']:,}",
                "Night %": f"{p['night_entry_pct']:.1f}%",
                "Severe Delays (>2d)": f"{p['severe_delays_count']:,}",
                "Assets Reporting": p["assets_reporting_count"],
                "Technicians": p["technicians_count"],
                "Forensic Summary": p["forensic_summary"],
            })
        st.dataframe(pd.DataFrame(p_rows), hide_index=True)

        st.markdown("#### Plaza-by-Plaza In-Depth Forensic Analysis")
        col_tp1, col_tp3, col_tp2 = st.columns(3)

        with col_tp1:
            st.error("#### 🔴 RANK #1: TP01 (Max Wrong Entries)")
            st.markdown(
                """
                - **Total Records:** 6,422
                - **Defect Entries:** **5,190 (80.82%)**
                - **Night Shift Logs:** 3,211 (50.0%)
                - **Severe Delays (>2d):** 501
                - **Primary Failures:**
                  * **1,332 records** with UPS battery DC Bus collapsed to **82.0V – 82.1V** (envelope is 360–435V).
                  * **981 records** with 463.0V overvoltage.
                  * **Counter drops** on EB meter `SR-E-EM-EB-000TP01` (1,380 -> 1,220 -> 1,140 kWh).
                  * **Zero Transformer Monitoring:** TP01 transformer has 0 logs exported in JUNO.
                - **Technicians:** Chandan Meher, Deepak Behera, Kshirod Khadia, Prabodh Rana, Ranjan Khadia.
                """
            )

        with col_tp3:
            st.warning("#### 🟡 RANK #2: TP03 (Max Night Submissions)")
            st.markdown(
                """
                - **Total Records:** 5,465
                - **Defect Entries:** 4,301 (78.70%)
                - **Night Shift Logs:** **3,222 (58.96%) — HIGHEST!**
                - **Severe Delays (>2d):** 90
                - **Primary Failures:**
                  * **Habitual Off-Hours Logging:** 6 out of 10 entries logged between 20:00 and 08:00 (heavy late night 21:00–23:45 and 05:00–06:45).
                  * **1,376 records** at 82.0V DC bus voltage.
                  * **1,770 records** between 463.2V and 464.2V.
                  * DG logged in running status with **0.0 kW active generation**.
                - **Technicians:** Krishna Chandra Patra, Pritam Mahapatra, Sanurjya Roudia, Srikant Sunani.
                """
            )

        with col_tp2:
            st.error("#### 🔴 RANK #3: TP02 (Severe Abandonment)")
            st.markdown(
                """
                - **Total Records:** **3,312** (Almost 50% fewer logs than TP01!)
                - **Defect Entries:** 184 (5.56%)
                - **Night Shift Logs:** 1,858 (56.10%)
                - **Severe Delays (>2d):** **345 incidents (Up to 40 days late!)**
                - **Primary Failures:**
                  * **Abandoned Telemetry:** DG generators stopped logging on **08-Sep-2026**; EB stopped on **14-Sep-2026**.
                  * **Zero UPS Logs:** TP02 UPS is completely unmonitored in JUNO exports!
                  * **Egregious Delays:** Rabi Narayan Singh logged readings **40.0 days late**; Pritam Mahapatra logged 25.5 days late at 23:11.
                - **Technicians:** Rabi Narayan Singh, Rabi Kishan, Rupesh Dhruva, Sunil Kullu.
                """
            )

    # =========================================================================
    # TAB 2: TECHNICIAN NIGHT AUDIT (8:00 PM TO 8:00 AM)
    # =========================================================================
    elif active_tab == "👨‍🔧 Technician Night Audit (8p–8a)":
        st.markdown("### 👨‍🔧 Technician Night Shift & Off-Hours Audit (8:00 PM – 8:00 AM)")
        st.markdown(
            "Audit of all entries submitted during off-hours (**20:00 to 08:00**), identifying habitual night loggers, "
            "severe backdated delays, and responsible technician names."
        )

        c_filt1, c_filt2 = st.columns(2)
        with c_filt1:
            plaza_filter = st.selectbox("Filter by Plaza", ["ALL", "TP01", "TP02", "TP03"])
        with c_filt2:
            tech_search = st.text_input("Search Technician Name", placeholder="e.g. Rabi, Pritam, Prabodh...")

        filtered_techs = techs
        if plaza_filter != "ALL":
            filtered_techs = [t for t in filtered_techs if plaza_filter in t["assigned_plazas"]]
        if tech_search:
            filtered_techs = [t for t in filtered_techs if tech_search.lower() in t["technician_name"].lower()]

        t_rows = []
        for t in filtered_techs:
            t_rows.append({
                "Technician Name": t["technician_name"],
                "Assigned Plazas": ", ".join(t["assigned_plazas"]),
                "Modules": ", ".join(t["modules_handled"]),
                "Total Submissions": f"{t['total_logs']:,}",
                "Night Logs (8p–8a)": f"{t['night_entries_count']:,}",
                "Night %": f"{t['night_entry_pct']:.1f}%",
                "Defects Logged": f"{t['defects_count']:,}",
                "Defect Rate %": f"{t['defect_rate_pct']:.1f}%",
                "Avg Delay (Days)": f"{t['avg_delay_days']:.1f}",
                "Max Delay (Days)": f"{t['max_delay_days']:.1f}",
                "Risk Classification": t["risk_profile"],
            })
        st.dataframe(pd.DataFrame(t_rows), hide_index=True)

        st.markdown("#### Sample Egregious Night & Late Backdated Entries (8:00 PM – 8:00 AM)")
        n_rows = []
        for idx, n in enumerate(night_entries[:25], 1):
            n_rows.append({
                "#": idx,
                "Plaza": n["plaza_id"],
                "Module": n["module"],
                "Asset Code": n["asset_code"],
                "Technician": n["technician"],
                "Entry Hour": f"{n['hour']:02d}:00",
                "Reading Datetime": n["reading_datetime"],
                "Logged At (Created On)": n["created_on"],
                "Delay (Days)": f"{n['delay_days']} days" if n["delay_days"] is not None else "N/A",
            })
        st.dataframe(pd.DataFrame(n_rows), hide_index=True)

    # =========================================================================
    # TAB 3: WRONG ENTRIES & DEFICIENCIES REGISTER
    # =========================================================================
    elif active_tab == "⚠️ Wrong Entries Register":
        st.markdown("### ⚠️ Wrong Entries & Technical Anomaly Register")
        st.markdown(
            "Complete log of technical deficiencies: DC bus voltage out of allowable envelope (360–435V), "
            "frequency anomalies, phase imbalances, zero-kW DG runs, and cumulative counter drops."
        )

        mod_sel = st.selectbox("Filter by Module", ["ALL", "EB", "DG", "Solar", "Transformer", "UPS"])
        w_filtered = wrong_entries
        if mod_sel != "ALL":
            w_filtered = [w for w in w_filtered if w["module"].upper() == mod_sel.upper()]

        w_rows = []
        for idx, w in enumerate(w_filtered, 1):
            w_rows.append({
                "#": idx,
                "Plaza": w["plaza_id"],
                "Module": w["module"],
                "Asset Code": w["asset_code"],
                "Technician": w["technician"],
                "Reading Datetime": w["reading_datetime"],
                "Submission Timestamp": w["created_on"],
                "Defect / Anomaly Message": w["violation"],
            })
        st.dataframe(pd.DataFrame(w_rows), hide_index=True)

    # =========================================================================
    # TAB 4: ASSET-WISE LAST READINGS
    # =========================================================================
    elif active_tab == "⚡ Asset-Wise Last Readings":
        st.markdown("### ⚡ Plaza-Wise & Asset-Wise Last Telemetry Reading")
        st.markdown(
            "Real-time status across all 20 assets reporting across the corridor. "
            "Highlights active telemetry, stale equipment (>7 days without reading), and unmonitored equipment."
        )

        lr_rows = []
        for r in last_readings:
            val_str = f"{r['cumulative_kwh']:,.1f} kWh" if r["cumulative_kwh"] is not None else "Telemetry Active"
            lr_rows.append({
                "Plaza": r["plaza_id"],
                "Module": r["module"],
                "Asset Code": r["asset_code"],
                "Last Reading Datetime": r["reading_datetime"],
                "Cumulative Value": val_str,
                "Last Technician": r["technician"],
                "Submission Timestamp": r["created_on"],
                "Monitoring Status": r["monitoring_status"],
            })
        st.dataframe(pd.DataFrame(lr_rows), hide_index=True)

        st.warning(
            "**Equipment Neglect Warnings:**\n"
            "- **TP01 Substation Transformer (`SR-E-HT-TFR-000001`):** Completely UNMONITORED in JUNO exports.\n"
            "- **TP02 UPS System:** Completely UNMONITORED in JUNO exports.\n"
            "- **TP02 Diesel Generators (`DGX-000003` & `000004`):** STALE — stopped logging on 08-Sep-2026.\n"
            "- **TP02 EB Incomer (`EB-130-000`):** STALE — stopped logging on 14-Sep-2026."
        )

    # =========================================================================
    # TAB 5: CORRECTED ASSET MASTER DATA
    # =========================================================================
    elif active_tab == "🛠️ Corrected Asset Master":
        st.markdown("### 🛠️ Corrected Asset Master Data (Supabase Alignment)")
        st.info(
            "**Root Cause of Master Data Errors:** Legacy seed scripts incorrectly assigned 100 kVA to Solar plants "
            "and mismatched Transformer and UPS locations. Following recent Supabase modifications, the specs are now verified:"
        )

        st.markdown(
            """
            1. **Solar Rating:**
               - **Correct Value:** **40.46 kWp** per plant (**121.38 kWp** corridor total across TP01, TP02, TP03).
               - **Unit:** `kWp` (DC Peak Power), **NOT** kVA.
            2. **Transformer Remapping:**
               - `SR-E-HT-TFR-000001` -> **TP01** (500 kVA HT Incomer).
               - `SR-E-HT-TFR-000002` -> **TP02** (500 kVA, physical tag `TRF-01/TP-02`).
               - `SR-E-HT-TFR-000003` -> **TP03** (500 kVA, physical tag `TRF-01/TP-03`).
            3. **UPS Remapping:**
               - `SR-E-AP-UPS-000002`, `000003`, `000004` -> **TP01** (`UPS-04/TP-01`).
               - `SR-E-AP-UPS-000009`, `000010`, `000012` -> **TP03** (`UPS-01/TP-03`).
            """
        )

        st.markdown("#### Database View: `energy_analytics.vw_asset_master_corrected`")
        master_rows = [
            {"Asset Code": "SR-E-AP-SPX-000001", "Asset Name": "Rooftop Solar Plant TP01", "Plaza": "TP01", "Module": "SOLAR", "Capacity": "40.46 kWp", "Status": "Active"},
            {"Asset Code": "SR-E-AP-SPX-000002", "Asset Name": "Rooftop Solar Plant TP02", "Plaza": "TP02", "Module": "SOLAR", "Capacity": "40.46 kWp", "Status": "Active"},
            {"Asset Code": "SR-E-AP-SPX-000003", "Asset Name": "Rooftop Solar Plant TP03", "Plaza": "TP03", "Module": "SOLAR", "Capacity": "40.46 kWp", "Status": "Active"},
            {"Asset Code": "SR-E-HT-TFR-000001", "Asset Name": "HT Substation Transformer TP01", "Plaza": "TP01", "Module": "TRANSFORMER", "Capacity": "500 kVA", "Status": "Active"},
            {"Asset Code": "SR-E-HT-TFR-000002", "Asset Name": "HT Substation Transformer TP02 (TRF-01/TP-02)", "Plaza": "TP02", "Module": "TRANSFORMER", "Capacity": "500 kVA", "Status": "Active"},
            {"Asset Code": "SR-E-HT-TFR-000003", "Asset Name": "HT Substation Transformer TP03 (TRF-01/TP-03)", "Plaza": "TP03", "Module": "TRANSFORMER", "Capacity": "500 kVA", "Status": "Active"},
            {"Asset Code": "SR-E-AP-UPS-000002", "Asset Name": "Main Toll Plaza UPS 2 (UPS-02/TP-01)", "Plaza": "TP01", "Module": "UPS", "Capacity": "40 kVA", "Status": "Active"},
            {"Asset Code": "SR-E-AP-UPS-000003", "Asset Name": "Main Toll Plaza UPS 3 (UPS-03/TP-01)", "Plaza": "TP01", "Module": "UPS", "Capacity": "40 kVA", "Status": "Active"},
            {"Asset Code": "SR-E-AP-UPS-000004", "Asset Name": "Main Toll Plaza UPS 4 (UPS-04/TP-01)", "Plaza": "TP01", "Module": "UPS", "Capacity": "40 kVA", "Status": "Active"},
            {"Asset Code": "SR-E-AP-UPS-000009", "Asset Name": "Main Toll Plaza UPS 9 (UPS-01/TP-03)", "Plaza": "TP03", "Module": "UPS", "Capacity": "40 kVA", "Status": "Active"},
            {"Asset Code": "SR-E-AP-UPS-000010", "Asset Name": "Main Toll Plaza UPS 10 (UPS-02/TP-03)", "Plaza": "TP03", "Module": "UPS", "Capacity": "40 kVA", "Status": "Active"},
            {"Asset Code": "SR-E-AP-UPS-000012", "Asset Name": "Main Toll Plaza UPS 12 (UPS-04/TP-03)", "Plaza": "TP03", "Module": "UPS", "Capacity": "40 kVA", "Status": "Active"},
        ]
        st.dataframe(pd.DataFrame(master_rows), hide_index=True)

    # =========================================================================
    # TAB 6: EXPORT FORENSIC DOSSIER
    # =========================================================================
    elif active_tab == "📥 Export Forensic Dossier":
        st.markdown("### 📥 Export Forensic Audit Dossier")
        st.markdown("Download full forensic data extracts as Excel or CSV for management reporting and compliance records.")

        export_df = pd.DataFrame(scorecard)
        csv_data = export_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="📥 Download Plaza Neglect Scorecard (CSV)",
            data=csv_data,
            file_name=f"SRTPL_Plaza_Neglect_Scorecard_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

        tech_df = pd.DataFrame(techs)
        tech_csv = tech_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Technician Audit Register (CSV)",
            data=tech_csv,
            file_name=f"SRTPL_Technician_Audit_Register_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
