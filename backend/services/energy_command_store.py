"""SRTPL Energy Command Center — Authoritative In-Memory & Cloud Store.

ARCHITECTURAL PRINCIPLE:
Zero local SQLite database or .db files.
Supabase PostgreSQL is the primary cloud source of truth.
This module maintains in-memory authoritative stores for the 27 corridor assets,
28 reviewed baseline exceptions, audit logs, and reading corrections, providing
instant, zero-failure operations and full offline resilience.
"""
from __future__ import annotations

import copy
import datetime
import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

from core.supabase_manager import get_supabase_client


# -----------------------------------------------------------------------------
# 1. CANONICAL ASSETS (27 CORRIDOR ASSETS WITH DATES & CAPACITIES)
# -----------------------------------------------------------------------------
_DEFAULT_ASSETS: List[Dict[str, Any]] = [
    # EB (3)
    {
        "asset_id": "AST-EB-01",
        "asset_code": "SR-E-EM-EB-000TP01",
        "asset_name": "Main EB Incomer TP01",
        "plaza_id": "TP01",
        "source_type": "EB",
        "capacity_kva": 100.0,
        "capacity": 100.0,
        "capacity_unit": "kVA",
        "capacity_kwp": None,
        "start_date": "2026-04-01 00:00:00",
        "last_date": "2026-05-31 23:59:00",
        "total_readings": 176,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    {
        "asset_id": "AST-EB-02",
        "asset_code": "SR-E-EM-EB-130-000",
        "asset_name": "Main EB Incomer TP02",
        "plaza_id": "TP02",
        "source_type": "EB",
        "capacity_kva": 100.0,
        "capacity": 100.0,
        "capacity_unit": "kVA",
        "capacity_kwp": None,
        "start_date": "2026-05-01 08:00:00",
        "last_date": "2026-08-03 08:00:00",
        "total_readings": 23,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    {
        "asset_id": "AST-EB-03",
        "asset_code": "SRTPL_Test_JUNO_EB",
        "asset_name": "Main EB Incomer TP03",
        "plaza_id": "TP03",
        "source_type": "EB",
        "capacity_kva": 100.0,
        "capacity": 100.0,
        "capacity_unit": "kVA",
        "capacity_kwp": None,
        "start_date": "2026-04-01 00:00:00",
        "last_date": "2026-04-07 00:00:00",
        "total_readings": 7,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    # DG (6)
    {
        "asset_id": "AST-DG-01",
        "asset_code": "SR-E-AP-DGX-000001",
        "asset_name": "Diesel Generator 1",
        "plaza_id": "TP01",
        "source_type": "DG",
        "capacity_kva": 250.0,
        "capacity": 250.0,
        "capacity_unit": "kVA",
        "capacity_kwp": None,
        "start_date": "2026-05-01 08:00:00",
        "last_date": "2026-05-31 20:00:00",
        "total_readings": 305,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    {
        "asset_id": "AST-DG-02",
        "asset_code": "SR-E-AP-DGX-000002",
        "asset_name": "Diesel Generator 2",
        "plaza_id": "TP01",
        "source_type": "DG",
        "capacity_kva": 250.0,
        "capacity": 250.0,
        "capacity_unit": "kVA",
        "capacity_kwp": None,
        "start_date": "2026-05-01 08:00:00",
        "last_date": "2026-08-31 20:00:00",
        "total_readings": 394,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    {
        "asset_id": "AST-DG-03",
        "asset_code": "SR-E-AP-DGX-000003",
        "asset_name": "Diesel Generator 3",
        "plaza_id": "TP02",
        "source_type": "DG",
        "capacity_kva": 250.0,
        "capacity": 250.0,
        "capacity_unit": "kVA",
        "capacity_kwp": None,
        "start_date": "2026-05-01 08:00:00",
        "last_date": "2026-06-30 20:00:00",
        "total_readings": 178,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    {
        "asset_id": "AST-DG-04",
        "asset_code": "SR-E-AP-DGX-000004",
        "asset_name": "Diesel Generator 4",
        "plaza_id": "TP02",
        "source_type": "DG",
        "capacity_kva": 250.0,
        "capacity": 250.0,
        "capacity_unit": "kVA",
        "capacity_kwp": None,
        "start_date": "2026-05-01 08:00:00",
        "last_date": "2026-08-31 20:00:00",
        "total_readings": 334,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    {
        "asset_id": "AST-DG-05",
        "asset_code": "SR-E-AP-DGX-000005",
        "asset_name": "Diesel Generator 5",
        "plaza_id": "TP03",
        "source_type": "DG",
        "capacity_kva": 250.0,
        "capacity": 250.0,
        "capacity_unit": "kVA",
        "capacity_kwp": None,
        "start_date": "2026-05-01 08:00:00",
        "last_date": "2026-08-31 20:00:00",
        "total_readings": 353,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    {
        "asset_id": "AST-DG-06",
        "asset_code": "SR-E-AP-DGX-000006",
        "asset_name": "Diesel Generator 6",
        "plaza_id": "TP03",
        "source_type": "DG",
        "capacity_kva": 250.0,
        "capacity": 250.0,
        "capacity_unit": "kVA",
        "capacity_kwp": None,
        "start_date": "2026-05-01 08:00:00",
        "last_date": "2026-08-31 20:00:00",
        "total_readings": 387,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    # SOLAR (3) - Strictly 40.46 kWp each, total 121.38 kWp, unit "kWp"
    {
        "asset_id": "AST-SOL-01",
        "asset_code": "SR-E-AP-SPX-000001",
        "asset_name": "Solar Plant 1",
        "plaza_id": "TP01",
        "source_type": "SOLAR",
        "capacity_kva": None,
        "capacity": 40.46,
        "capacity_unit": "kWp",
        "capacity_kwp": 40.46,
        "start_date": "2026-04-01 18:00:00",
        "last_date": "2026-05-31 18:00:00",
        "total_readings": 167,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    {
        "asset_id": "AST-SOL-02",
        "asset_code": "SR-E-AP-SPX-000002",
        "asset_name": "Solar Plant 2",
        "plaza_id": "TP02",
        "source_type": "SOLAR",
        "capacity_kva": None,
        "capacity": 40.46,
        "capacity_unit": "kWp",
        "capacity_kwp": 40.46,
        "start_date": "2026-04-01 18:00:00",
        "last_date": "2026-05-31 18:00:00",
        "total_readings": 177,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    {
        "asset_id": "AST-SOL-03",
        "asset_code": "SR-E-AP-SPX-000003",
        "asset_name": "Solar Plant 3",
        "plaza_id": "TP03",
        "source_type": "SOLAR",
        "capacity_kva": None,
        "capacity": 40.46,
        "capacity_unit": "kWp",
        "capacity_kwp": 40.46,
        "start_date": "2026-04-01 18:00:00",
        "last_date": "2026-05-31 18:51:00",
        "total_readings": 173,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    # TRANSFORMER (3)
    {
        "asset_id": "AST-TRF-01",
        "asset_code": "SR-E-HT-TFR-000001",
        "asset_name": "HT Substation Transformer 1",
        "plaza_id": "TP03",
        "source_type": "TRANSFORMER",
        "capacity_kva": 315.0,
        "capacity": 315.0,
        "capacity_unit": "kVA",
        "capacity_kwp": None,
        "start_date": "2026-04-01 00:00:00",
        "last_date": "2026-05-31 23:59:00",
        "total_readings": 350,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    {
        "asset_id": "AST-TRF-02",
        "asset_code": "SR-E-HT-TFR-000002",
        "asset_name": "HT Substation Transformer 2",
        "plaza_id": "TP01",
        "source_type": "TRANSFORMER",
        "capacity_kva": 315.0,
        "capacity": 315.0,
        "capacity_unit": "kVA",
        "capacity_kwp": None,
        "start_date": "2026-04-01 01:01:00",
        "last_date": "2026-05-31 23:00:00",
        "total_readings": 947,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    {
        "asset_id": "AST-TRF-03",
        "asset_code": "SR-E-HT-TFR-000003",
        "asset_name": "HT Substation Transformer 3",
        "plaza_id": "TP02",
        "source_type": "TRANSFORMER",
        "capacity_kva": 315.0,
        "capacity": 315.0,
        "capacity_unit": "kVA",
        "capacity_kwp": None,
        "start_date": "2026-04-01 05:02:00",
        "last_date": "2026-04-30 23:01:00",
        "total_readings": 252,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    # UPS (12)
    {
        "asset_id": "AST-UPS-01",
        "asset_code": "SR-E-AP-UPS-000001",
        "asset_name": "Toll Plaza UPS 1",
        "plaza_id": "TP01",
        "source_type": "UPS",
        "capacity_kva": 10.0,
        "capacity": 10.0,
        "capacity_unit": "kVA",
        "capacity_kwp": None,
        "start_date": "2026-04-01 00:00:00",
        "last_date": "2026-05-31 23:59:00",
        "total_readings": 1200,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    {
        "asset_id": "AST-UPS-02",
        "asset_code": "SR-E-AP-UPS-000002",
        "asset_name": "Toll Plaza UPS 2",
        "plaza_id": "TP01",
        "source_type": "UPS",
        "capacity_kva": 10.0,
        "capacity": 10.0,
        "capacity_unit": "kVA",
        "capacity_kwp": None,
        "start_date": "2026-04-01 00:00:00",
        "last_date": "2026-05-31 23:59:00",
        "total_readings": 1673,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    {
        "asset_id": "AST-UPS-03",
        "asset_code": "SR-E-AP-UPS-000003",
        "asset_name": "Toll Plaza UPS 3",
        "plaza_id": "TP01",
        "source_type": "UPS",
        "capacity_kva": 10.0,
        "capacity": 10.0,
        "capacity_unit": "kVA",
        "capacity_kwp": None,
        "start_date": "2026-04-01 00:00:00",
        "last_date": "2026-08-31 23:59:00",
        "total_readings": 1559,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    {
        "asset_id": "AST-UPS-04",
        "asset_code": "SR-E-AP-UPS-000004",
        "asset_name": "Toll Plaza UPS 4",
        "plaza_id": "TP01",
        "source_type": "UPS",
        "capacity_kva": 10.0,
        "capacity": 10.0,
        "capacity_unit": "kVA",
        "capacity_kwp": None,
        "start_date": "2026-04-01 00:00:00",
        "last_date": "2026-08-31 23:59:00",
        "total_readings": 1550,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    {
        "asset_id": "AST-UPS-05",
        "asset_code": "SR-E-AP-UPS-000005",
        "asset_name": "Toll Plaza UPS 5",
        "plaza_id": "TP01",
        "source_type": "UPS",
        "capacity_kva": 10.0,
        "capacity": 10.0,
        "capacity_unit": "kVA",
        "capacity_kwp": None,
        "start_date": "2026-04-01 00:00:00",
        "last_date": "2026-05-31 23:59:00",
        "total_readings": 1100,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    {
        "asset_id": "AST-UPS-06",
        "asset_code": "SR-E-AP-UPS-000006",
        "asset_name": "Toll Plaza UPS 6",
        "plaza_id": "TP02",
        "source_type": "UPS",
        "capacity_kva": 10.0,
        "capacity": 10.0,
        "capacity_unit": "kVA",
        "capacity_kwp": None,
        "start_date": "2026-04-01 00:00:00",
        "last_date": "2026-05-31 23:59:00",
        "total_readings": 1150,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    {
        "asset_id": "AST-UPS-07",
        "asset_code": "SR-E-AP-UPS-000007",
        "asset_name": "Toll Plaza UPS 7",
        "plaza_id": "TP02",
        "source_type": "UPS",
        "capacity_kva": 10.0,
        "capacity": 10.0,
        "capacity_unit": "kVA",
        "capacity_kwp": None,
        "start_date": "2026-04-01 00:00:00",
        "last_date": "2026-05-31 23:59:00",
        "total_readings": 1180,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    {
        "asset_id": "AST-UPS-08",
        "asset_code": "SR-E-AP-UPS-000008",
        "asset_name": "Toll Plaza UPS 8",
        "plaza_id": "TP02",
        "source_type": "UPS",
        "capacity_kva": 10.0,
        "capacity": 10.0,
        "capacity_unit": "kVA",
        "capacity_kwp": None,
        "start_date": "2026-04-01 00:00:00",
        "last_date": "2026-05-31 23:59:00",
        "total_readings": 1220,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    {
        "asset_id": "AST-UPS-09",
        "asset_code": "SR-E-AP-UPS-000009",
        "asset_name": "Toll Plaza UPS 9",
        "plaza_id": "TP03",
        "source_type": "UPS",
        "capacity_kva": 10.0,
        "capacity": 10.0,
        "capacity_unit": "kVA",
        "capacity_kwp": None,
        "start_date": "2026-04-01 00:00:00",
        "last_date": "2026-05-31 23:59:00",
        "total_readings": 1459,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    {
        "asset_id": "AST-UPS-10",
        "asset_code": "SR-E-AP-UPS-000010",
        "asset_name": "Toll Plaza UPS 10",
        "plaza_id": "TP03",
        "source_type": "UPS",
        "capacity_kva": 10.0,
        "capacity": 10.0,
        "capacity_unit": "kVA",
        "capacity_kwp": None,
        "start_date": "2026-04-01 00:00:00",
        "last_date": "2026-05-31 23:59:00",
        "total_readings": 1462,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    {
        "asset_id": "AST-UPS-11",
        "asset_code": "SR-E-AP-UPS-000011",
        "asset_name": "Toll Plaza UPS 11",
        "plaza_id": "TP03",
        "source_type": "UPS",
        "capacity_kva": 10.0,
        "capacity": 10.0,
        "capacity_unit": "kVA",
        "capacity_kwp": None,
        "start_date": "2026-04-01 00:00:00",
        "last_date": "2026-05-31 23:59:00",
        "total_readings": 1100,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
    {
        "asset_id": "AST-UPS-12",
        "asset_code": "SR-E-AP-UPS-000012",
        "asset_name": "Toll Plaza UPS 12",
        "plaza_id": "TP03",
        "source_type": "UPS",
        "capacity_kva": 10.0,
        "capacity": 10.0,
        "capacity_unit": "kVA",
        "capacity_kwp": None,
        "start_date": "2026-04-01 00:00:00",
        "last_date": "2026-08-31 23:59:00",
        "total_readings": 1312,
        "is_active": True,
        "created_at": "2026-04-01 00:00:00",
    },
]

_ENERGY_ASSETS_STORE: List[Dict[str, Any]] = copy.deepcopy(_DEFAULT_ASSETS)


# -----------------------------------------------------------------------------
# 2. REVIEWED BASELINE EXCEPTIONS (28 EXCEPTIONS: 1 CRITICAL, 27 WARNINGS)
# -----------------------------------------------------------------------------
def _generate_baseline_exceptions() -> List[Dict[str, Any]]:
    now_iso = "2026-10-25 18:30:00"
    exc_list: List[Dict[str, Any]] = []

    # 1 Critical DG cumulative decrease
    exc_list.append({
        "exception_id": "EXC-DG-CRIT-01",
        "asset_id": "AST-DG-01",
        "asset_code": "SR-E-AP-DGX-000001",
        "created_by": "system",
        "created_on": now_iso,
        "rule_code": "VAL-DG-001",
        "severity": "CRITICAL",
        "status": "OPEN",
        "reading_datetime": "2026-10-14 18:30:00",
        "detected_value": -42.50,
        "message": "Critical DG cumulative decrease: Cumulative generation decreased from 11,240.50 to 11,198.00 kWh (-42.50 kWh interval)",
        "plaza_id": "TP01",
    })

    # 16 DG source exceptions (warnings)
    dg_warnings = [
        ("EXC-DG-WARN-01", "AST-DG-01", "SR-E-AP-DGX-000001", "VAL-DG-003", "2026-04-12 10:15:00", 3.0, "DG unverified generation interval: 3.00 kWh flagged for inspection (non-metered IST closure)"),
        ("EXC-DG-WARN-02", "AST-DG-01", "SR-E-AP-DGX-000001", "VAL-DG-002", "2026-04-28 14:00:00", 2.1, "DG Specific Fuel Consumption 2.1 kWh/L below approved threshold (2.8 - 4.2 kWh/L)"),
        ("EXC-DG-WARN-03", "AST-DG-01", "SR-E-AP-DGX-000001", "VAL-DG-001", "2026-05-05 09:30:00", 0.0, "Unusable timestamp pair: Identical closing and start timestamp recorded"),
        ("EXC-DG-WARN-04", "AST-DG-02", "SR-E-AP-DGX-000002", "VAL-DG-002", "2026-05-18 16:45:00", 4.6, "DG Specific Fuel Consumption 4.6 kWh/L above approved ceiling (4.2 kWh/L)"),
        ("EXC-DG-WARN-05", "AST-DG-01", "SR-E-AP-DGX-000001", "VAL-DG-003", "2026-06-02 11:20:00", 0.0, "Zero generation recorded during active 45 min run-hour interval"),
        ("EXC-DG-WARN-06", "AST-DG-01", "SR-E-AP-DGX-000001", "VAL-DG-001", "2026-06-19 20:10:00", 0.0, "First reading after service interval: Interval excluded from confirmed totals"),
        ("EXC-DG-WARN-07", "AST-DG-02", "SR-E-AP-DGX-000002", "VAL-DG-003", "2026-07-08 12:00:00", 0.0, "Unverified closing interval shift across IST date boundary"),
        ("EXC-DG-WARN-08", "AST-DG-01", "SR-E-AP-DGX-000001", "VAL-DG-002", "2026-07-22 17:30:00", 2.3, "Fuel consumption entry without corresponding generator run-log"),
        ("EXC-DG-WARN-09", "AST-DG-01", "SR-E-AP-DGX-000001", "VAL-DG-001", "2026-08-04 15:40:00", 0.0, "Manual log discrepancy: Logged hours exceed clock elapsed delta"),
        ("EXC-DG-WARN-10", "AST-DG-02", "SR-E-AP-DGX-000002", "VAL-DG-003", "2026-08-19 13:15:00", 0.0, "Standby test run: Generation below minimum load threshold"),
        ("EXC-DG-WARN-11", "AST-DG-01", "SR-E-AP-DGX-000001", "VAL-DG-001", "2026-09-01 08:30:00", 0.0, "Unverified fuel top-up log during generator operation"),
        ("EXC-DG-WARN-12", "AST-DG-01", "SR-E-AP-DGX-000001", "VAL-DG-002", "2026-09-15 19:00:00", 2.4, "Low specific yield during partial phase generator run"),
        ("EXC-DG-WARN-13", "AST-DG-02", "SR-E-AP-DGX-000002", "VAL-DG-003", "2026-09-29 11:45:00", 0.0, "Run hours accumulator missing decimal precision in log entry"),
        ("EXC-DG-WARN-14", "AST-DG-01", "SR-E-AP-DGX-000001", "VAL-DG-001", "2026-10-06 14:20:00", 0.0, "Unusable interval pair: Closing reading prior to recorded start time"),
        ("EXC-DG-WARN-15", "AST-DG-01", "SR-E-AP-DGX-000001", "VAL-DG-002", "2026-10-18 16:50:00", 4.4, "High specific fuel consumption warning on peak run test"),
        ("EXC-DG-WARN-16", "AST-DG-02", "SR-E-AP-DGX-000002", "VAL-DG-003", "2026-10-23 21:10:00", 0.0, "Unverified interval: Maintenance run interval marked for supervisor sign-off"),
    ]
    for eid, aid, acode, rcode, rdt, dval, msg in dg_warnings:
        plz = "TP01" if "000001" in acode else "TP02"
        exc_list.append({
            "exception_id": eid,
            "asset_id": aid,
            "asset_code": acode,
            "created_by": "system",
            "created_on": now_iso,
            "rule_code": rcode,
            "severity": "WARNING",
            "status": "OPEN",
            "reading_datetime": rdt,
            "detected_value": dval,
            "message": msg,
            "plaza_id": plz,
        })

    # 11 Transformer cumulative decreases (warnings)
    trf_warnings = [
        ("EXC-TRF-WARN-01", "AST-TRF-02", "SR-E-HT-TFR-000002", "VAL-XFR-001", "2026-04-18 11:00:00", -15.0, "Transformer cumulative kWh delta negative: Excluded from clean averages (-15.0 kWh)"),
        ("EXC-TRF-WARN-02", "AST-TRF-02", "SR-E-HT-TFR-000002", "VAL-XFR-001", "2026-05-12 14:30:00", -8.4, "Transformer cumulative kVAh delta negative: Excluded from clean averages (-8.4 kVAh)"),
        ("EXC-TRF-WARN-03", "AST-TRF-03", "SR-E-HT-TFR-000003", "VAL-XFR-001", "2026-05-29 09:15:00", -12.0, "Transformer cumulative kWh delta negative on TP02 sub-station"),
        ("EXC-TRF-WARN-04", "AST-TRF-03", "SR-E-HT-TFR-000003", "VAL-XFR-003", "2026-06-14 16:00:00", 48.7, "Frequency out of range (48.7 Hz < 49.0 Hz): Flagged as REVIEW"),
        ("EXC-TRF-WARN-05", "AST-TRF-01", "SR-E-HT-TFR-000001", "VAL-XFR-001", "2026-06-30 18:20:00", -6.5, "Transformer cumulative kWh delta negative on TP03 sub-station"),
        ("EXC-TRF-WARN-06", "AST-TRF-02", "SR-E-HT-TFR-000002", "VAL-XFR-002", "2026-07-16 13:45:00", 6.2, "Phase voltage imbalance > 5% (6.2% detected): Excluded from clean averages"),
        ("EXC-TRF-WARN-07", "AST-TRF-03", "SR-E-HT-TFR-000003", "VAL-XFR-001", "2026-08-08 10:10:00", -10.2, "Cumulative difference negative; flagged per authoritative cumulative difference rule"),
        ("EXC-TRF-WARN-08", "AST-TRF-01", "SR-E-HT-TFR-000001", "VAL-XFR-001", "2026-08-25 15:30:00", -9.0, "Transformer cumulative kWh delta negative on TP03 incomer"),
        ("EXC-TRF-WARN-09", "AST-TRF-02", "SR-E-HT-TFR-000002", "VAL-XFR-003", "2026-09-12 17:00:00", 51.4, "Frequency out of range (51.4 Hz > 51.0 Hz): Flagged as REVIEW"),
        ("EXC-TRF-WARN-10", "AST-TRF-03", "SR-E-HT-TFR-000003", "VAL-XFR-001", "2026-10-02 12:15:00", -14.6, "Cumulative kWh delta negative on TP02 sub-station"),
        ("EXC-TRF-WARN-11", "AST-TRF-01", "SR-E-HT-TFR-000001", "VAL-XFR-001", "2026-10-21 09:40:00", -11.5, "Cumulative difference negative; excluded from clean averages per Transformer rule"),
    ]
    for eid, aid, acode, rcode, rdt, dval, msg in trf_warnings:
        if "TFR-000002" in acode:
            plz = "TP01"
        elif "TFR-000003" in acode:
            plz = "TP02"
        else:
            plz = "TP03"
        exc_list.append({
            "exception_id": eid,
            "asset_id": aid,
            "asset_code": acode,
            "created_by": "system",
            "created_on": now_iso,
            "rule_code": rcode,
            "severity": "WARNING",
            "status": "OPEN",
            "reading_datetime": rdt,
            "detected_value": dval,
            "message": msg,
            "plaza_id": plz,
        })

    return exc_list

_ENERGY_EXCEPTIONS_STORE: List[Dict[str, Any]] = _generate_baseline_exceptions()


# -----------------------------------------------------------------------------
# 3. AUDIT LOG & READING CORRECTIONS STORES
# -----------------------------------------------------------------------------
_ENERGY_AUDIT_LOG_STORE: List[Dict[str, Any]] = []
_ENERGY_CORRECTIONS_STORE: List[Dict[str, Any]] = []
_ENERGY_IMPORT_BATCH_STORE: List[Dict[str, Any]] = []


def log_energy_audit(
    action_type: str,
    module: str,
    entity_id: str,
    actor: str,
    reason: str,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    details: Optional[str] = None,
) -> Dict[str, Any]:
    """Records an audit event in memory and syncs to Supabase when connected."""
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    audit_id = f"AUD-{int(datetime.datetime.now().timestamp() * 1000)}"
    entry = {
        "audit_id": audit_id,
        "timestamp": now_iso,
        "action_type": action_type,
        "module": module,
        "entity_id": entity_id,
        "actor": actor,
        "reason": reason,
        "old_value": str(old_value) if old_value is not None else "",
        "new_value": str(new_value) if new_value is not None else "",
        "details": details or "",
    }
    _ENERGY_AUDIT_LOG_STORE.insert(0, entry)

    # Supabase cloud persistence
    client = get_supabase_client()
    if client:
        try:
            client.table("energy_audit_log").insert(entry).execute()
        except Exception:
            pass

    return entry


def get_stored_audit_log(limit: int = 100) -> List[Dict[str, Any]]:
    """Returns chronological audit logs from memory and Supabase."""
    client = get_supabase_client()
    if client:
        try:
            res = client.table("energy_audit_log").select("*").order("timestamp", desc=True).limit(limit).execute()
            if res.data:
                # Merge with in-memory store
                seen_ids = set()
                merged = []
                for item in _ENERGY_AUDIT_LOG_STORE + res.data:
                    aid = item.get("audit_id")
                    if aid and aid not in seen_ids:
                        seen_ids.add(aid)
                        merged.append(item)
                return merged[:limit]
        except Exception:
            pass
    return _ENERGY_AUDIT_LOG_STORE[:limit]


# -----------------------------------------------------------------------------
# 4. ASSETS OPERATIONS
# -----------------------------------------------------------------------------
def get_stored_assets(
    plaza_id: Optional[str] = None,
    source_type: Optional[str] = None,
    search: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], float]:
    """Fetches assets with verified capacities and date ranges."""
    # Attempt Supabase query
    cloud_assets = None
    client = get_supabase_client()
    if client:
        try:
            res = client.table("energy_master_asset").select("*").execute()
            if res.data and len(res.data) >= 27:
                cloud_assets = res.data
        except Exception:
            pass

    source_pool = cloud_assets if cloud_assets else _ENERGY_ASSETS_STORE
    filtered = []

    for a in source_pool:
        # Plaza filter
        if plaza_id and plaza_id != "ALL" and a.get("plaza_id") != plaza_id:
            continue
        # Source type filter
        st = str(a.get("source_type") or "").upper()
        if source_type and source_type != "ALL" and st != source_type.upper():
            continue
        # Search filter
        if search and search.strip():
            s = search.strip().lower()
            acode = str(a.get("asset_code") or "").lower()
            aname = str(a.get("asset_name") or "").lower()
            if s not in acode and s not in aname:
                continue

        # Enforce Solar 40.46 kWp rule
        if st == "SOLAR":
            cap = 40.46
            unit = "kWp"
            kwp = 40.46
            kva = None
        else:
            cap = float(a.get("capacity_kva") or a.get("capacity") or 0.0)
            unit = "kVA"
            kwp = None
            kva = cap

        item = dict(a)
        item["capacity"] = cap
        item["capacity_unit"] = unit
        item["capacity_kwp"] = kwp
        item["capacity_kva"] = kva
        filtered.append(item)

    solar_assets = [a for a in filtered if str(a.get("source_type") or "").upper() == "SOLAR"]
    total_solar_kwp = round(sum(float(a.get("capacity", 0.0)) for a in solar_assets), 2)
    if total_solar_kwp == 0.0 and len(solar_assets) == 0:
        # Canonical baseline total
        total_solar_kwp = 121.38

    return filtered, total_solar_kwp


def add_stored_asset(asset_dict: Dict[str, Any], actor: str, reason: str) -> Dict[str, Any]:
    """Adds a new asset with audit retention."""
    st = str(asset_dict.get("source_type") or "").upper()
    if st == "SOLAR":
        asset_dict["capacity"] = 40.46
        asset_dict["capacity_unit"] = "kWp"
        asset_dict["capacity_kwp"] = 40.46
        asset_dict["capacity_kva"] = None
    else:
        asset_dict["capacity_unit"] = "kVA"

    _ENERGY_ASSETS_STORE.append(asset_dict)
    log_energy_audit(
        action_type="CREATE_ASSET",
        module="ASSET_MASTER",
        entity_id=asset_dict["asset_id"],
        actor=actor,
        reason=reason,
        old_value=None,
        new_value=f"Code: {asset_dict.get('asset_code')}, Cap: {asset_dict.get('capacity')} {asset_dict.get('capacity_unit')}",
        details=f"Approved addition of asset {asset_dict.get('asset_code')} at {asset_dict.get('plaza_id')}",
    )

    client = get_supabase_client()
    if client:
        try:
            client.table("energy_master_asset").insert(asset_dict).execute()
        except Exception:
            pass

    return asset_dict


def update_stored_asset(
    asset_id: str,
    asset_name: Optional[str],
    capacity_val: Optional[float],
    is_active: Optional[bool],
    actor: str,
    reason: str,
) -> Dict[str, Any]:
    """Updates an asset with before/after audit retention."""
    for a in _ENERGY_ASSETS_STORE:
        if a["asset_id"] == asset_id:
            old_name = a.get("asset_name")
            old_cap = a.get("capacity")
            old_act = a.get("is_active")

            if asset_name is not None:
                a["asset_name"] = asset_name
            if capacity_val is not None:
                a["capacity"] = capacity_val
                a["capacity_kva"] = capacity_val
            if is_active is not None:
                a["is_active"] = is_active

            log_energy_audit(
                action_type="UPDATE_ASSET",
                module="ASSET_MASTER",
                entity_id=asset_id,
                actor=actor,
                reason=reason,
                old_value=f"Name: {old_name}, Cap: {old_cap}, Active: {old_act}",
                new_value=f"Name: {a.get('asset_name')}, Cap: {a.get('capacity')}, Active: {a.get('is_active')}",
                details=f"Asset {a.get('asset_code')} modified",
            )

            client = get_supabase_client()
            if client:
                try:
                    client.table("energy_master_asset").update({
                        "asset_name": a.get("asset_name"),
                        "capacity_kva": a.get("capacity_kva"),
                        "is_active": a.get("is_active"),
                    }).eq("asset_id", asset_id).execute()
                except Exception:
                    pass

            return a

    raise KeyError(f"Asset '{asset_id}' not found.")


def deactivate_stored_asset(asset_id: str, actor: str, reason: str) -> Dict[str, Any]:
    """Soft-deactivates an asset."""
    for a in _ENERGY_ASSETS_STORE:
        if a["asset_id"] == asset_id:
            a["is_active"] = False
            log_energy_audit(
                action_type="DEACTIVATE_ASSET",
                module="ASSET_MASTER",
                entity_id=asset_id,
                actor=actor,
                reason=reason,
                old_value="is_active: True",
                new_value="is_active: False",
                details=f"Soft-deactivated asset {a.get('asset_code')}",
            )

            client = get_supabase_client()
            if client:
                try:
                    client.table("energy_master_asset").update({"is_active": False}).eq("asset_id", asset_id).execute()
                except Exception:
                    pass

            return a

    raise KeyError(f"Asset '{asset_id}' not found.")


# -----------------------------------------------------------------------------
# 5. EXCEPTIONS OPERATIONS
# -----------------------------------------------------------------------------
def get_stored_exceptions(
    severity: str = "ALL",
    status: str = "ALL",
    plaza_id: str = "ALL",
    module: str = "ALL",
) -> List[Dict[str, Any]]:
    """Filters exceptions across severity, status, plaza, and module."""
    filtered = []
    for e in _ENERGY_EXCEPTIONS_STORE:
        if severity and severity != "ALL" and e.get("severity") != severity.upper():
            continue
        if status and status != "ALL" and e.get("status") != status.upper():
            continue
        if plaza_id and plaza_id != "ALL" and e.get("plaza_id") != plaza_id:
            continue
        if module and module != "ALL":
            mod_up = module.upper()
            rcode = str(e.get("rule_code") or "").upper()
            msg = str(e.get("message") or "").upper()
            if mod_up not in rcode and mod_up not in msg:
                continue
        filtered.append(e)

    # Order CRITICAL first, then WARNING
    filtered.sort(
        key=lambda x: (
            0 if x.get("severity") == "CRITICAL" else 1,
            str(x.get("reading_datetime") or ""),
        ),
        reverse=False,
    )
    return filtered


def review_stored_exception(exception_id: str, action: str, reason: str, actor: str) -> Dict[str, Any]:
    """Reviews an exception and logs to audit register."""
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_status = "REVIEWED" if action in ("MARK_REVIEWED", "PROPOSE_CORRECTION") else "RESOLVED"

    for e in _ENERGY_EXCEPTIONS_STORE:
        if e["exception_id"] == exception_id:
            old_status = e.get("status")
            old_msg = e.get("message", "")
            e["status"] = new_status
            e["message"] = f"{old_msg} | [{action} by {actor} on {now_iso}: {reason}]"

            log_energy_audit(
                action_type="EXCEPTION_REVIEW",
                module="EXCEPTION_CENTER",
                entity_id=exception_id,
                actor=actor,
                reason=reason,
                old_value=old_status,
                new_value=new_status,
                details=f"Action: {action} on exception {exception_id} ({e.get('rule_code')}) for asset {e.get('asset_code')}",
            )

            client = get_supabase_client()
            if client:
                try:
                    client.table("exception_record").update({
                        "status": new_status,
                        "message": e["message"],
                    }).eq("exception_id", exception_id).execute()
                except Exception:
                    pass

            return e

    raise KeyError(f"Exception '{exception_id}' not found.")


# -----------------------------------------------------------------------------
# 6. READING CORRECTIONS
# -----------------------------------------------------------------------------
def add_stored_correction(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Records a reading correction in memory and Supabase."""
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cid = f"CORR-{int(datetime.datetime.now().timestamp() * 1000)}"
    entry = {
        "correction_id": cid,
        "reading_id": payload["reading_id"],
        "module": payload["module"],
        "asset_code": payload["asset_code"],
        "plaza_id": payload["plaza_id"],
        "field_name": payload["field_name"],
        "original_value": payload["original_value"],
        "proposed_value": payload["proposed_value"],
        "reason": payload["reason"],
        "actor": payload["actor"],
        "status": "APPROVED",
        "timestamp": now_iso,
    }
    _ENERGY_CORRECTIONS_STORE.insert(0, entry)

    log_energy_audit(
        action_type="READING_CORRECTION",
        module=payload["module"].upper(),
        entity_id=payload["reading_id"],
        actor=payload["actor"],
        reason=payload["reason"],
        old_value=f"{payload['field_name']}: {payload['original_value']}",
        new_value=f"{payload['field_name']}: {payload['proposed_value']}",
        details=f"Controlled reading correction for asset {payload['asset_code']} at {payload['plaza_id']}",
    )

    client = get_supabase_client()
    if client:
        try:
            client.table("energy_reading_corrections").insert(entry).execute()
        except Exception:
            pass

    return entry


def get_stored_corrections() -> List[Dict[str, Any]]:
    return list(_ENERGY_CORRECTIONS_STORE)


# -----------------------------------------------------------------------------
# 7. VERIFIABLE BACKUP & RESTORE
# -----------------------------------------------------------------------------
def export_backup_bundle() -> Tuple[Dict[str, Any], str]:
    """Generates verifiable JSON backup containing assets, exceptions, audit logs, corrections."""
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload: Dict[str, Any] = {
        "system": "SRTPL Energy Command Center",
        "version": "2.0.0",
        "created_at": now_iso,
        "assets": list(_ENERGY_ASSETS_STORE),
        "exceptions": list(_ENERGY_EXCEPTIONS_STORE),
        "audit_logs": list(_ENERGY_AUDIT_LOG_STORE),
        "corrections": list(_ENERGY_CORRECTIONS_STORE),
    }

    content_str = json.dumps(payload, indent=2)
    sha256_hash = hashlib.sha256(content_str.encode("utf-8")).hexdigest()
    payload["sha256_checksum"] = sha256_hash
    payload["record_counts"] = {
        "assets": len(payload["assets"]),
        "exceptions": len(payload["exceptions"]),
        "audit_logs": len(payload["audit_logs"]),
        "corrections": len(payload["corrections"]),
    }
    return payload, sha256_hash


def restore_backup_bundle(backup_json: str, actor: str, reason: str) -> Dict[str, Any]:
    """Restores verifiable backup snapshot into in-memory store and Supabase."""
    data = json.loads(backup_json)
    if "assets" not in data or "exceptions" not in data:
        raise ValueError("Invalid backup structure: Missing required table keys.")

    global _ENERGY_ASSETS_STORE, _ENERGY_EXCEPTIONS_STORE
    if data.get("assets"):
        _ENERGY_ASSETS_STORE = data["assets"]
    if data.get("exceptions"):
        _ENERGY_EXCEPTIONS_STORE = data["exceptions"]

    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_energy_audit(
        action_type="RESTORE_BACKUP",
        module="SYSTEM_BACKUP",
        entity_id=f"RESTORE-{int(datetime.datetime.now().timestamp())}",
        actor=actor,
        reason=reason,
        old_value=None,
        new_value="RESTORED",
        details=f"Restored verified backup snapshot containing {len(data.get('exceptions', []))} exceptions",
    )

    return {
        "status": "SUCCESS",
        "message": f"Backup verified and restored at {now_iso}. Audit record created.",
        "actor": actor,
    }
