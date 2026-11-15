from __future__ import annotations

from pathlib import Path
import sys

ACTIVE_APP = Path(__file__).resolve().parents[1]
if str(ACTIVE_APP) not in sys.path:
    sys.path.insert(0, str(ACTIVE_APP))

from core.reading_view_ui import render_equipment_reading_view


def render():
    sample_ups = [
        {"Asset Code": "SR-E-AP-UPS-000002", "Plaza": "TP01", "Records": "1,673 logs", "Rating": "20 kVA", "Status": "OPERATIONAL"},
        {"Asset Code": "SR-E-AP-UPS-000003", "Plaza": "TP01", "Records": "1,559 logs", "Rating": "20 kVA", "Status": "OPERATIONAL"},
        {"Asset Code": "SR-E-AP-UPS-000004", "Plaza": "TP02", "Records": "1,550 logs", "Rating": "20 kVA", "Status": "OPERATIONAL"},
        {"Asset Code": "SR-E-AP-UPS-000009", "Plaza": "TP02", "Records": "1,459 logs", "Rating": "20 kVA", "Status": "OPERATIONAL"},
        {"Asset Code": "SR-E-AP-UPS-000010", "Plaza": "TP03", "Records": "1,462 logs", "Rating": "20 kVA", "Status": "OPERATIONAL"},
        {"Asset Code": "SR-E-AP-UPS-000012", "Plaza": "TP03", "Records": "1,368 logs", "Rating": "20 kVA", "Status": "OPERATIONAL"},
    ]
    rules = [
        "VAL-UPS-001: DC bus voltage allowable envelope (360V - 435V)",
        "VAL-UPS-002: Inverter input-to-output efficiency bounds (≥ 91%)",
        "VAL-UPS-OUTPUT-V: Output voltage threshold checking (nominal ~230V single phase / 400V 3-phase)",
        "VAL-UPS-OUTPUT-F: Output frequency stability validation (48 to 52 Hz standard window)",
        "VAL-UPS-BYPASS-V & F: Bypass supply integrity check during utility anomalies",
        "VAL-UPS-BATT-V & T: Battery DC bus voltage and temperature health monitoring",
    ]
    render_equipment_reading_view(
        asset_type="ups",
        title="🔋 UPS Analytics & Power Continuity",
        subtitle="Phase 5.7 • Input/output voltage, bypass tracking, battery health, and availability monitoring.",
        unit_label="Volts",
        default_meter="SR-E-AP-UPS-000002",
        sample_assets=sample_ups,
        rules=rules,
    )


if __name__ == "__main__":
    render()
