from __future__ import annotations

from pathlib import Path
import sys

ACTIVE_APP = Path(__file__).resolve().parents[1]
if str(ACTIVE_APP) not in sys.path:
    sys.path.insert(0, str(ACTIVE_APP))

from core.reading_view_ui import render_equipment_reading_view


def render():
    sample_meters = [
        {"Meter / Source": "SR-E-EM-EB-000TP01", "Plaza": "TP01", "Mode": "Detailed Daily Interval", "Sanctioned": "120 KVA", "Status": "OPERATIONAL"},
        {"Meter / Source": "SR-E-EM-EB-000TP02", "Plaza": "TP02", "Mode": "Detailed Daily Interval", "Sanctioned": "100 KVA", "Status": "OPERATIONAL"},
        {"Meter / Source": "SR-E-EM-EB-000TP03", "Plaza": "TP03", "Mode": "Detailed Daily Interval", "Sanctioned": "120 KVA", "Status": "OPERATIONAL"},
        {"Meter / Source": "SR-E-EM-EB-130-000", "Plaza": "TP03", "Mode": "Cumulative EB Log", "Sanctioned": "18.0 KW", "Status": "OPERATIONAL"},
        {"Meter / Source": "SRTPL_Test_JUNO_EB.csv", "Plaza": "TP01", "Mode": "Cumulative Test Log", "Sanctioned": "10.0 KW", "Status": "VALIDATED"},
    ]
    rules = [
        "VAL-EB-001: Non-decreasing cumulative active energy (kWh)",
        "VAL-EB-002: Non-decreasing cumulative apparent energy (kVAh)",
        "VAL-EB-003: Power factor bounds validation (0.00 <= PF <= 1.00)",
        "VAL-EB-004: Non-decreasing cumulative reactive energy (kVARh)",
        "Interval Preservation: Detailed daily consumption files are handled as interval data without artificial subtraction.",
    ]
    render_equipment_reading_view(
        asset_type="eb",
        title="⚡ EB Grid Reading & Power Factor",
        subtitle="Phase 5.4 • Electricity board billing meter, cumulative & interval daily logs, and power factor analysis.",
        unit_label="kWh",
        default_meter="SR-E-EM-EB-000TP01",
        sample_assets=sample_meters,
        rules=rules,
    )


if __name__ == "__main__":
    render()
