from __future__ import annotations

from pathlib import Path
import sys

ACTIVE_APP = Path(__file__).resolve().parents[1]
if str(ACTIVE_APP) not in sys.path:
    sys.path.insert(0, str(ACTIVE_APP))

import streamlit as st


def render():
    st.title("🛢️ DG Analytics & Backup Generation")
    st.caption("Phase 5.3 • Diesel generator run-hours, generation, specific fuel consumption, and PF analysis.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Inventoried DG Sets", "6 Units", "DGX-000001 through 000006")
    c2.metric("Daily Generation", "DG-GEN-D", "Validated kWh")
    c3.metric("Runtime Hours", "DG-RUN-D", "Validated Hours")
    c4.metric("Generation Rate", "DG-KWH-HR", "kWh per Runtime Hour")

    st.subheader("Governing Validation Rules")
    st.markdown("""
    - **VAL-DG-001**: Non-decreasing cumulative generation (cumulative kWh decrease triggers exception).
    - **VAL-DG-002**: Non-decreasing runtime hours (cumulative running hours decrease triggers exception).
    - **VAL-DG-003**: Power factor bounds validation (`0.0 <= PF <= 1.0`).
    - **VAL-DG-004**: Plausible load and generation limits (prevents silent erroneous records).
    - **Traceability**: All exception records are preserved with rule codes; only `VALID` intervals enter KPI totals.
    """)

    st.subheader("Inventoried DG Generators")
    gens = [
        {"Generator Code": "SR-E-AP-DGX-000001", "Records": "305", "Status": "STANDBY/READY"},
        {"Generator Code": "SR-E-AP-DGX-000002", "Records": "394", "Status": "STANDBY/READY"},
        {"Generator Code": "SR-E-AP-DGX-000003", "Records": "178", "Status": "STANDBY/READY"},
        {"Generator Code": "SR-E-AP-DGX-000004", "Records": "334", "Status": "STANDBY/READY"},
        {"Generator Code": "SR-E-AP-DGX-000005", "Records": "353", "Status": "STANDBY/READY"},
        {"Generator Code": "SR-E-AP-DGX-000006", "Records": "396", "Status": "STANDBY/READY"},
    ]
    st.table(gens)

    st.info("To process fresh DG logs, navigate to **DG JUNO Import** in the sidebar.")


if __name__ == "__main__":
    render()
