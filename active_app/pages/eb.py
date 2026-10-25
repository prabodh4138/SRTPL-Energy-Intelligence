from __future__ import annotations

from pathlib import Path
import sys

ACTIVE_APP = Path(__file__).resolve().parents[1]
if str(ACTIVE_APP) not in sys.path:
    sys.path.insert(0, str(ACTIVE_APP))

import streamlit as st


def render():
    st.title("⚡ EB Analytics & Grid Consumption")
    st.caption("Phase 5.4 • Electricity board billing meter, cumulative & interval daily logs, and power factor analysis.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active EB Meters", "2 Log Formats", "Cumulative & Interval Daily")
    c2.metric("Daily Consumption", "EB-CONS-D", "Validated kWh")
    c3.metric("KVAH Consumption", "EB-KVAH-D", "Validated kVAh")
    c4.metric("Average PF", "EB-PF-D", "Active/Apparent Ratio")

    st.subheader("Governing Validation Rules")
    st.markdown("""
    - **VAL-EB-001**: Non-decreasing cumulative active energy (kWh).
    - **VAL-EB-002**: Non-decreasing cumulative apparent energy (kVAh).
    - **VAL-EB-003**: Power factor bounds validation (`0.0 <= PF <= 1.0`).
    - **VAL-EB-004**: Non-decreasing cumulative reactive energy (kVARh).
    - **Interval Preservation**: Detailed daily consumption files are handled as interval data without artificial subtraction.
    """)

    st.subheader("Tested EB Formats & Meter Sources")
    meters = [
        {"Meter / Source": "SRTPL_Test_JUNO_EB.csv", "Mode": "Cumulative Test Log", "Records": "7", "Status": "VALIDATED"},
        {"Meter / Source": "SR-E-EM-EB-130-000", "Mode": "Cumulative EB Log", "Records": "23", "Status": "OPERATIONAL"},
        {"Meter / Source": "SR-E-EM-EB-000TP01", "Mode": "Detailed Daily Interval", "Records": "767", "Status": "OPERATIONAL"},
    ]
    st.table(meters)

    st.info("To process fresh EB CSV files, navigate to **EB JUNO Import** in the sidebar.")


if __name__ == "__main__":
    render()
