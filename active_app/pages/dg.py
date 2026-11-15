from __future__ import annotations

from pathlib import Path
import sys

ACTIVE_APP = Path(__file__).resolve().parents[1]
if str(ACTIVE_APP) not in sys.path:
    sys.path.insert(0, str(ACTIVE_APP))

from core.reading_view_ui import render_equipment_reading_view


def render():
    sample_gens = [
        {"Generator Code": "SR-E-AP-DGX-000001", "Plaza": "TP01", "Capacity": "250 kVA", "Records": "305", "Status": "STANDBY/READY"},
        {"Generator Code": "SR-E-AP-DGX-000002", "Plaza": "TP01", "Capacity": "250 kVA", "Records": "394", "Status": "STANDBY/READY"},
        {"Generator Code": "SR-E-AP-DGX-000003", "Plaza": "TP02", "Capacity": "250 kVA", "Records": "178", "Status": "STANDBY/READY"},
        {"Generator Code": "SR-E-AP-DGX-000004", "Plaza": "TP02", "Capacity": "250 kVA", "Records": "334", "Status": "STANDBY/READY"},
        {"Generator Code": "SR-E-AP-DGX-000005", "Plaza": "TP03", "Capacity": "250 kVA", "Records": "353", "Status": "STANDBY/READY"},
        {"Generator Code": "SR-E-AP-DGX-000006", "Plaza": "TP03", "Capacity": "250 kVA", "Records": "396", "Status": "STANDBY/READY"},
    ]
    rules = [
        "VAL-DG-001: Non-decreasing run-hour accumulator (runtime hours decrease triggers exception)",
        "VAL-DG-002: Specific fuel consumption bounds (2.8 - 4.2 kWh/L)",
        "VAL-DG-003: Positive net generation during active run hours",
        "VAL-DG-004: Plausible load and generation limits (prevents silent erroneous records)",
        "Traceability: All exception records are preserved with rule codes; only VALID intervals enter KPI totals.",
    ]
    render_equipment_reading_view(
        asset_type="dg",
        title="🛢️ DG Generator & Backup Generation",
        subtitle="Phase 5.3 • Diesel generator run-hours, generation, specific fuel consumption, and PF analysis.",
        unit_label="kWh",
        default_meter="SR-E-AP-DGX-000001",
        sample_assets=sample_gens,
        rules=rules,
    )


if __name__ == "__main__":
    render()
