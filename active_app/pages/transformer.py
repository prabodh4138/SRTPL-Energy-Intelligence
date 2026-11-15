from __future__ import annotations

from pathlib import Path
import sys

ACTIVE_APP = Path(__file__).resolve().parents[1]
if str(ACTIVE_APP) not in sys.path:
    sys.path.insert(0, str(ACTIVE_APP))

import streamlit as st
from core.reading_view_ui import render_equipment_reading_view


def render():
    st.warning(
        "**Mandatory Audit Caution**: Transformer loss and efficiency calculations remain "
        "**disabled** until measurement boundaries, CT/PT ratio verification, ratings, "
        "and meter semantics are formally signed off by engineering."
    )

    sample_transformers = [
        {"Asset Code": "SR-E-HT-TFR-000002", "Plaza": "TP01", "Voltage Class": "11kV / 433V", "Primary Readings": "1,300 log points", "Status": "HEALTHY"},
        {"Asset Code": "SR-E-HT-TFR-000003", "Plaza": "TP02", "Voltage Class": "11kV / 433V", "Primary Readings": "252 log points", "Status": "HEALTHY"},
    ]
    rules = [
        "VAL-TRF-001: Power factor verification (0.0 <= PF <= 1.0)",
        "VAL-XFR-001: Balanced 3-phase current variance (≤ 15% imbalance)",
        "VAL-XFR-002: Winding and oil temperature ceilings (≤ 85°C)",
        "VAL-TRF-PV-IMB: Primary voltage phase imbalance warning threshold evaluation",
        "VAL-TRF-SV-IMB: Secondary voltage phase imbalance warning threshold evaluation",
        "Duplicate Detection: Enforces file-level SHA-256 idempotency",
    ]
    render_equipment_reading_view(
        asset_type="transformer",
        title="🔌 Step-Down Transformers & Electrical Health",
        subtitle="Phase 5.6 • Phase voltage/current imbalance, oil & winding temperature tracking, and PF monitoring.",
        unit_label="Units",
        default_meter="SR-E-HT-TFR-000002",
        sample_assets=sample_transformers,
        rules=rules,
    )


if __name__ == "__main__":
    render()
