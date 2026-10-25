from __future__ import annotations

from pathlib import Path
import sys

ACTIVE_APP = Path(__file__).resolve().parents[1]
if str(ACTIVE_APP) not in sys.path:
    sys.path.insert(0, str(ACTIVE_APP))

import streamlit as st


def render():
    st.title("🔌 Transformer Analytics & Electrical Health")
    st.caption("Phase 5.6 • Phase voltage/current imbalance, oil & winding temperature tracking, and PF monitoring.")

    st.warning(
        "**Mandatory Audit Caution**: Transformer loss and efficiency calculations remain "
        "**disabled** until measurement boundaries, CT/PT ratio verification, ratings, "
        "and meter semantics are formally signed off by engineering."
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Inventoried Transformers", "2 Active Units", "000002, 000003")
    c2.metric("Primary Voltage Imbalance", "TR-VI-01", "Max % deviation")
    c3.metric("Primary Current Imbalance", "TR-CI-01", "Max % deviation")
    c4.metric("Thermal Indicators", "WTI & OTI", "°C winding/oil temp")

    st.subheader("Governing Validation Rules")
    st.markdown("""
    - **VAL-TRF-001**: Power factor verification (`0.0 <= PF <= 1.0`).
    - **VAL-TRF-PV-IMB**: Primary voltage phase imbalance warning threshold evaluation.
    - **VAL-TRF-SV-IMB**: Secondary voltage phase imbalance warning threshold evaluation.
    - **VAL-TRF-PI-IMB**: Primary current phase imbalance warning threshold evaluation.
    - **VAL-TRF-SI-IMB**: Secondary current phase imbalance warning threshold evaluation.
    - **Duplicate Detection**: Enforces file-level SHA-256 idempotency.
    """)

    st.subheader("Inventoried Transformer Units")
    transformers = [
        {"Asset Code": "SR-E-HT-TFR-000002", "Voltage Class": "11kV / 433V", "Primary Readings": "1,300 log points", "Loss/Eff": "DISABLED"},
        {"Asset Code": "SR-E-HT-TFR-000003", "Voltage Class": "11kV / 433V", "Primary Readings": "252 log points", "Loss/Eff": "DISABLED"},
    ]
    st.table(transformers)

    st.info("To process fresh Transformer daily logs, navigate to **Transformer JUNO Import** in the sidebar.")


if __name__ == "__main__":
    render()
