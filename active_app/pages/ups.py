from __future__ import annotations

from pathlib import Path
import sys

ACTIVE_APP = Path(__file__).resolve().parents[1]
if str(ACTIVE_APP) not in sys.path:
    sys.path.insert(0, str(ACTIVE_APP))

import streamlit as st


def render():
    st.title("🔋 UPS Analytics & Power Continuity")
    st.caption("Phase 5.7 • Input/output voltage, bypass tracking, battery health, and availability monitoring.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Inventoried UPS Units", "6 Units", "000002 through 000012")
    c2.metric("Availability KPI", "UPS-AV-01", "% reporting operational")
    c3.metric("Output Voltage", "UPS-V-OUT-AVG", "Average Volts")
    c4.metric("Battery VDC", "UPS-BATT-V-AVG", "DC Bus Voltage")

    st.subheader("Governing Validation Rules")
    st.markdown("""
    - **VAL-UPS-OUTPUT-V**: Output voltage threshold checking (nominal ~230V single phase / 400V 3-phase).
    - **VAL-UPS-OUTPUT-F**: Output frequency stability validation (48 to 52 Hz standard window).
    - **VAL-UPS-BYPASS-V & F**: Bypass supply integrity check during utility anomalies.
    - **VAL-UPS-BATT-V & T**: Battery DC bus voltage and temperature health monitoring.
    - **VAL-UPS-RECTIFIER-V**: Rectifier DC link integrity monitoring.
    """)

    st.subheader("Inventoried UPS Assets")
    units = [
        {"Asset Code": "SR-E-AP-UPS-000002", "Records": "1,673", "Status": "OPERATIONAL"},
        {"Asset Code": "SR-E-AP-UPS-000003", "Records": "1,559", "Status": "OPERATIONAL"},
        {"Asset Code": "SR-E-AP-UPS-000004", "Records": "1,550", "Status": "OPERATIONAL"},
        {"Asset Code": "SR-E-AP-UPS-000009", "Records": "1,459", "Status": "OPERATIONAL"},
        {"Asset Code": "SR-E-AP-UPS-000010", "Records": "1,462", "Status": "OPERATIONAL"},
        {"Asset Code": "SR-E-AP-UPS-000012", "Records": "1,368", "Status": "OPERATIONAL"},
    ]
    st.table(units)

    st.info("To process fresh UPS daily log files, navigate to **UPS JUNO Import** in the sidebar.")


if __name__ == "__main__":
    render()
