import sqlite3
import os

db_path = os.path.join("active_app", "data", "srtpl_power.db")
conn = sqlite3.connect(db_path)
cur = conn.cursor()

tables = {
    "energy_master_asset": ["asset_id", "asset_code", "asset_name", "plaza_id", "source_type", "capacity_kva"],
    "energy_readings_dg": [
        "reading_id", "asset_id", "asset_code", "reading_datetime", "status", "kva", "kw",
        "voltage_ry", "voltage_yb", "voltage_br", "current_r", "current_y", "current_b",
        "diesel_level", "diesel_topup", "load_percentage", "cumulative_kwh", "cumulative_running_hours",
        "interval_kwh", "interval_running_hours", "rpm", "pf", "created_by", "created_on", "created_at",
        "remarks", "data_quality_status"
    ],
    "energy_readings_eb": [
        "reading_id", "asset_id", "asset_code", "reading_datetime", "cumulative_kwh", "cumulative_kvah",
        "interval_kwh", "interval_kvah", "pf", "maximum_demand", "created_by", "created_on", "created_at",
        "remarks", "location", "data_quality_status"
    ],
    "energy_readings_solar": [
        "reading_id", "asset_id", "asset_code", "reading_datetime", "created_by", "created_on",
        "created_at", "remarks", "location", "data_quality_status"
    ],
    "energy_readings_transformer": [
        "reading_id", "asset_id", "asset_code", "reading_datetime",
        "primary_v_ry", "primary_v_yb", "primary_v_br",
        "secondary_v_ry", "secondary_v_yb", "secondary_v_br",
        "primary_i_r", "primary_i_y", "primary_i_b",
        "secondary_i_r", "secondary_i_y", "secondary_i_b",
        "oil_temperature", "winding_temperature", "pf", "created_by", "created_on", "created_at",
        "remarks", "location", "data_quality_status"
    ],
    "energy_readings_ups": [
        "reading_id", "asset_id", "asset_code", "reading_datetime", "output_voltage", "output_current",
        "output_frequency", "battery_vdc", "battery_temperature", "rectifier_voltage",
        "created_by", "created_on", "created_at", "remarks", "location", "data_quality_status"
    ]
}

print("=== CHECKING REQUIRED SOURCE COLUMNS ===")
all_ok = True
for table_name, req_cols in tables.items():
    cur.execute(f"PRAGMA table_info({table_name})")
    cols = {row[1] for row in cur.fetchall()}
    missing = [c for c in req_cols if c not in cols]
    if missing:
        all_ok = False
        print(f"[FAIL] {table_name} missing columns: {missing}")
    else:
        print(f"[PASS] {table_name} has all {len(req_cols)} required columns.")

# Check HH.MM conversion
sample_val = 16.45
h = int(sample_val)
m = round((sample_val - h) * 100)
tot_min = h * 60 + m
print(f"=== HH.MM RUNTIME CONVERSION CHECK ===")
print(f"16.45 -> {h} hours, {m} minutes = {tot_min} minutes. Expected: 1005. OK: {tot_min == 1005}")

# Check Night window in IST: 22:00 to 06:00
print(f"=== NIGHT WINDOW LOGIC CHECK (22:00 - 06:00) ===")
def is_night(hh, mm):
    return (hh >= 22) or (hh < 6)

test_cases = [
    (21, 59, False),
    (22, 0, True),
    (5, 59, True),
    (6, 0, False)
]
for hh, mm, exp in test_cases:
    res = is_night(hh, mm)
    print(f"Time {hh:02d}:{mm:02d} -> Night: {res} (Expected: {exp}) -> {'PASS' if res == exp else 'FAIL'}")

conn.close()
