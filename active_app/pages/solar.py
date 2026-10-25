from __future__ import annotations

from pathlib import Path
import sys

ACTIVE_APP = Path(__file__).resolve().parents[1]
if str(ACTIVE_APP) not in sys.path:
    sys.path.insert(0, str(ACTIVE_APP))

import streamlit as st


def render():
    st.title("☀️ Solar Analytics & Plant Overview")
    st.caption("Phase 5.5 • Solar generation monitoring, availability scoring, and cumulative delta validation.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Inventoried Plants", "3", help="SR-E-AP-SPX-000001, 000002, 000003")
    c2.metric("Active Standard KPI", "SOL-GEN-D", "Daily Generation (kWh)")
    c3.metric("Availability Metric", "SOL-AVAIL-D", "% reporting uptime")

    st.subheader("Validation Rules")
    st.markdown("""
    - **VAL-SOL-001**: Non-decreasing cumulative generation rule. Any decrease in cumulative kWh is flagged as an anomaly.
    - **Interval Derivation**: Daily generation = `cumulative_kwh(t) - cumulative_kwh(t-1)`.
    - **NULL Preservation**: Missing readings remain `NULL` and are excluded from generation sums.
    """)

    st.subheader("Inventoried Solar Plants")
    plants = [
        {"Plant Code": "SR-E-AP-SPX-000001", "Source File": "Solar_Plant_Log_25thSep2026_4168_Solar Log.csv", "Capacity": "Operational", "Status": "ONLINE"},
        {"Plant Code": "SR-E-AP-SPX-000002", "Source File": "Solar_Plant_Log_25thSep2026_2719_Solar Log.csv", "Capacity": "Operational", "Status": "ONLINE"},
        {"Plant Code": "SR-E-AP-SPX-000003", "Source File": "Solar_Plant_Log_25thSep2026_2764_Solar Log.csv", "Capacity": "Operational", "Status": "ONLINE"},
    ]
    st.table(plants)

    st.info("To process fresh Solar logs, navigate to **Solar JUNO Import** in the sidebar.")


if __name__ == "__main__":
    render()
