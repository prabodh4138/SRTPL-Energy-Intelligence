from __future__ import annotations

from pathlib import Path
import sys

ACTIVE_APP = Path(__file__).resolve().parents[1]
if str(ACTIVE_APP) not in sys.path:
    sys.path.insert(0, str(ACTIVE_APP))

from core.reading_view_ui import render_equipment_reading_view


def render():
    sample_plants = [
        {"Plant Code": "SR-E-AP-SPX-000001", "Plaza": "TP01", "Capacity": "40.46 kWp", "Records": "217 logs", "Status": "ONLINE"},
        {"Plant Code": "SR-E-AP-SPX-000002", "Plaza": "TP02", "Capacity": "40.46 kWp", "Records": "228 logs", "Status": "ONLINE"},
        {"Plant Code": "SR-E-AP-SPX-000003", "Plaza": "TP03", "Capacity": "40.46 kWp", "Records": "229 logs", "Status": "ONLINE"},
    ]
    rules = [
        "VAL-SOL-001: Non-decreasing cumulative generation rule (cumulative kWh decrease triggers exception)",
        "VAL-SOLAR-001: Non-negative diurnal generation profile",
        "VAL-SOLAR-002: Peak irradiance generation ceiling (≤ Capacity * 1.1)",
        "Interval Derivation: Daily generation = cumulative_kwh(t) - cumulative_kwh(t-1)",
        "NULL Preservation: Missing readings remain NULL and are excluded from generation sums.",
    ]
    render_equipment_reading_view(
        asset_type="solar",
        title="☀️ Solar Analytics & Plant Overview",
        subtitle="Phase 5.5 • Solar generation monitoring, availability scoring, and cumulative delta validation.",
        unit_label="kWh",
        default_meter="SR-E-AP-SPX-000001",
        sample_assets=sample_plants,
        rules=rules,
    )


if __name__ == "__main__":
    render()
