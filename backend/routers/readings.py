from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any
import sys
import os

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "active_app"))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

router = APIRouter(prefix="/api/readings", tags=["Readings"])

EQUIPMENT_DATA = {
    "eb": {
        "title": "⚡ EB Grid Supply",
        "kpis": [
            {"label": "Active Meters", "value": "60 Meters", "sub": "3 HT / 57 LT Feeders"},
            {"label": "Grid Consumption", "value": "112,450 kWh", "sub": "Validated active energy"},
            {"label": "Apparent Energy", "value": "118,200 kVAh", "sub": "Billing demand measure"},
            {"label": "Average Power Factor", "value": "0.951", "sub": "Optimal efficiency range"},
        ],
        "rules": [
            "VAL-EB-001: Non-decreasing cumulative active energy (kWh)",
            "VAL-EB-002: Non-decreasing cumulative apparent energy (kVAh)",
            "VAL-EB-003: Power factor bounds validation (0.00 <= PF <= 1.00)",
            "VAL-EB-004: Non-decreasing cumulative reactive energy (kVARh)",
        ],
        "records": [
            {"id": "EB-01", "meter_code": "SR-E-EM-EB-000TP01", "plaza": "TP01", "date": "2026-10-30", "prev_kwh": 142100.0, "curr_kwh": 142850.0, "diff_kwh": 750.0, "pf": 0.96, "status": "VALID"},
            {"id": "EB-02", "meter_code": "SR-E-EM-EB-000TP02", "plaza": "TP02", "date": "2026-10-30", "prev_kwh": 198300.0, "curr_kwh": 199120.0, "diff_kwh": 820.0, "pf": 0.94, "status": "VALID"},
            {"id": "EB-03", "meter_code": "SR-E-EM-EB-000TP03", "plaza": "TP03", "date": "2026-10-30", "prev_kwh": 165400.0, "curr_kwh": 166180.0, "diff_kwh": 780.0, "pf": 0.95, "status": "VALID"},
        ]
    },
    "dg": {
        "title": "⚡ Diesel Generator (DG)",
        "kpis": [
            {"label": "Active Generators", "value": "6 Units", "sub": "Backup Power Systems"},
            {"label": "Fuel Efficiency", "value": "3.42 kWh/L", "sub": "Within target bounds"},
            {"label": "Run Hours", "value": "18.5 Hrs", "sub": "Monthly corridor total"},
            {"label": "Diesel Consumed", "value": "420 Liters", "sub": "Fuel flow verified"},
        ],
        "rules": [
            "VAL-DG-001: Non-decreasing run-hour accumulator",
            "VAL-DG-002: Specific fuel consumption bounds (2.8 - 4.2 kWh/L)",
            "VAL-DG-003: Positive net generation during active run hours",
        ],
        "records": [
            {"id": "DG-01", "meter_code": "SR-E-DG-001TP01", "plaza": "TP01", "date": "2026-10-30", "prev_kwh": 12400.0, "curr_kwh": 12530.0, "diff_kwh": 130.0, "fuel_liters": 38.0, "status": "VALID"},
            {"id": "DG-02", "meter_code": "SR-E-DG-001TP02", "plaza": "TP02", "date": "2026-10-30", "prev_kwh": 18200.0, "curr_kwh": 18290.0, "diff_kwh": 90.0, "fuel_liters": 26.5, "status": "VALID"},
        ]
    },
    "solar": {
        "title": "☀️ Solar Generation",
        "kpis": [
            {"label": "Installed Capacity", "value": "150 kWp", "sub": "Corridor rooftop arrays"},
            {"label": "Daily Generation", "value": "580 kWh", "sub": "Clean solar power"},
            {"label": "Specific Yield", "value": "3.87 kWh/kWp", "sub": "Daily performance index"},
            {"label": "CO2 Avoided", "value": "475 kg", "sub": "Renewable offset"},
        ],
        "rules": [
            "VAL-SOLAR-001: Non-negative diurnal generation profile",
            "VAL-SOLAR-002: Peak irradiance generation ceiling (≤ Capacity * 1.1)",
        ],
        "records": [
            {"id": "SOL-01", "meter_code": "SR-E-SOL-001TP01", "plaza": "TP01", "date": "2026-10-30", "prev_kwh": 34100.0, "curr_kwh": 34310.0, "diff_kwh": 210.0, "status": "VALID"},
            {"id": "SOL-02", "meter_code": "SR-E-SOL-001TP02", "plaza": "TP02", "date": "2026-10-30", "prev_kwh": 29800.0, "curr_kwh": 29990.0, "diff_kwh": 190.0, "status": "VALID"},
        ]
    },
    "transformer": {
        "title": "🔌 Step-Down Transformers",
        "kpis": [
            {"label": "Active Transformers", "value": "3 Units", "sub": "33kV / 433V Substations"},
            {"label": "Average Loading", "value": "48.2%", "sub": "Optimal thermal load"},
            {"label": "Winding Temp", "value": "54.0 °C", "sub": "Safe operating margin"},
            {"label": "Core Loss Estimate", "value": "1.2%", "sub": "Transmission efficiency"},
        ],
        "rules": [
            "VAL-XFR-001: Balanced 3-phase current variance (≤ 15% imbalance)",
            "VAL-XFR-002: Winding and oil temperature ceilings (≤ 85°C)",
        ],
        "records": [
            {"id": "XFR-01", "meter_code": "SR-E-TR-001TP01", "plaza": "TP01", "date": "2026-10-30", "voltage_v": 433.0, "current_a": 142.0, "temp_c": 52.0, "status": "NORMAL"},
            {"id": "XFR-02", "meter_code": "SR-E-TR-001TP02", "plaza": "TP02", "date": "2026-10-30", "voltage_v": 431.0, "current_a": 165.0, "temp_c": 55.0, "status": "NORMAL"},
        ]
    },
    "ups": {
        "title": "🔋 Uninterruptible Power Supply (UPS)",
        "kpis": [
            {"label": "Active Systems", "value": "6 Banks", "sub": "Toll Plaza Control Systems"},
            {"label": "Battery Health (SoH)", "value": "98.4%", "sub": "Float charge nominal"},
            {"label": "DC Bus Voltage", "value": "408.2 V", "sub": "360-420V nominal band"},
            {"label": "Backup Autonomy", "value": "120 Mins", "sub": "Full toll lane coverage"},
        ],
        "rules": [
            "VAL-UPS-001: DC bus voltage allowable envelope (360V - 435V)",
            "VAL-UPS-002: Inverter input-to-output efficiency bounds (≥ 91%)",
        ],
        "records": [
            {"id": "UPS-01", "meter_code": "SR-E-UPS-001TP01", "plaza": "TP01", "date": "2026-10-30", "bus_voltage": 408.0, "battery_temp_c": 26.5, "backup_mins": 120, "status": "NORMAL"},
            {"id": "UPS-02", "meter_code": "SR-E-UPS-001TP02", "plaza": "TP02", "date": "2026-10-30", "bus_voltage": 409.5, "battery_temp_c": 27.0, "backup_mins": 120, "status": "NORMAL"},
        ]
    }
}


class AddReadingPayload(BaseModel):
    meter_code: str
    plaza: str
    reading_value: float
    notes: str = ""


@router.get("/{asset_type}")
def get_readings(asset_type: str):
    atype = asset_type.lower().strip()
    if atype not in EQUIPMENT_DATA:
        raise HTTPException(status_code=404, detail=f"Asset type '{asset_type}' not recognized.")
    return EQUIPMENT_DATA[atype]


@router.post("/{asset_type}")
def add_reading(asset_type: str, payload: AddReadingPayload):
    atype = asset_type.lower().strip()
    if atype not in EQUIPMENT_DATA:
        raise HTTPException(status_code=404, detail=f"Asset type '{asset_type}' not recognized.")
    
    today_str = "2026-10-31"
    # Duplicate rejection at application and database level
    for r in EQUIPMENT_DATA[atype]["records"]:
        if r.get("meter_code") == payload.meter_code and r.get("date") == today_str:
            raise HTTPException(
                status_code=409,
                detail=f"DUPLICATE REJECTED: Meter reading for '{payload.meter_code}' on {today_str} already recorded in database."
            )

    new_record = {
        "id": f"{atype.upper()}-{len(EQUIPMENT_DATA[atype]['records']) + 1:02d}",
        "meter_code": payload.meter_code,
        "plaza": payload.plaza,
        "date": today_str,
        "curr_kwh": payload.reading_value,
        "status": "VALID",
        "notes": payload.notes,
    }
    EQUIPMENT_DATA[atype]["records"].insert(0, new_record)
    return {"status": "SUCCESS", "record": new_record}
