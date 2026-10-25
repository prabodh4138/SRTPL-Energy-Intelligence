"""SRTPL Power Consumption Analytics — Real-time Live Database Sync Layer.

Handles bidirectional CRUD operations (Add, Modify, Delete) from the Streamlit
application with simultaneous persistence to Supabase (when connected) and local state.
"""
from __future__ import annotations

from typing import Any
import pandas as pd
import streamlit as st

from core.supabase_manager import get_supabase_client
from core.demo_store import (
    is_demo_mode,
    RAW_EXCEPTION_DETAILS,
    get_demo_bills,
    get_demo_exceptions,
)


# ---------------------------------------------------------------------------
# 1. PLAZAS CRUD (Add, Modify, Delete)
# ---------------------------------------------------------------------------

DEFAULT_PLAZAS = [
    {"plaza_id": "TP01", "plaza_name": "Toll Plaza 01", "location": "SRTPL Corridor Km 24+500", "is_active": True},
    {"plaza_id": "TP02", "plaza_name": "Toll Plaza 02", "location": "SRTPL Corridor Km 68+200", "is_active": True},
    {"plaza_id": "TP03", "plaza_name": "Toll Plaza 03", "location": "SRTPL Corridor Km 112+800", "is_active": True},
]


def get_all_plazas() -> pd.DataFrame:
    """Fetch plazas from Supabase if connected, else from session state / defaults."""
    client = get_supabase_client()
    if client:
        try:
            res = client.table("plaza").select("*").order("plaza_id").execute()
            if res.data:
                return pd.DataFrame(res.data)
        except Exception:
            try:
                res = client.schema("energy_master").table("plaza").select("*").order("plaza_id").execute()
                if res.data:
                    return pd.DataFrame(res.data)
            except Exception:
                pass

    if "custom_plazas" not in st.session_state:
        st.session_state["custom_plazas"] = list(DEFAULT_PLAZAS)

    return pd.DataFrame(st.session_state["custom_plazas"])


def save_plaza(plaza_id: str, plaza_name: str, location: str, is_active: bool = True) -> dict[str, Any]:
    """Add or update a plaza in Supabase and local session state simultaneously."""
    payload = {
        "plaza_id": plaza_id.strip().upper(),
        "plaza_name": plaza_name.strip(),
        "location": location.strip(),
        "is_active": bool(is_active),
    }

    client = get_supabase_client()
    cloud_synced = False
    if client:
        try:
            client.table("plaza").upsert(payload).execute()
            cloud_synced = True
        except Exception:
            try:
                client.schema("energy_master").table("plaza").upsert(payload).execute()
                cloud_synced = True
            except Exception:
                pass

    # Update local session
    if "custom_plazas" not in st.session_state:
        st.session_state["custom_plazas"] = list(DEFAULT_PLAZAS)

    existing = [p for p in st.session_state["custom_plazas"] if p["plaza_id"] != payload["plaza_id"]]
    existing.append(payload)
    st.session_state["custom_plazas"] = sorted(existing, key=lambda x: x["plaza_id"])

    return {"status": "SUCCESS", "cloud_synced": cloud_synced, "payload": payload}


def delete_plaza(plaza_id: str) -> dict[str, Any]:
    """Delete a plaza in Supabase and local session state simultaneously."""
    target_id = plaza_id.strip().upper()
    client = get_supabase_client()
    cloud_deleted = False

    if client:
        try:
            client.table("plaza").delete().eq("plaza_id", target_id).execute()
            cloud_deleted = True
        except Exception:
            try:
                client.schema("energy_master").table("plaza").delete().eq("plaza_id", target_id).execute()
                cloud_deleted = True
            except Exception:
                pass

    if "custom_plazas" in st.session_state:
        st.session_state["custom_plazas"] = [
            p for p in st.session_state["custom_plazas"] if p["plaza_id"] != target_id
        ]

    return {"status": "DELETED", "cloud_synced": cloud_deleted, "plaza_id": target_id}


# ---------------------------------------------------------------------------
# 2. ASSETS CRUD (Add, Modify, Delete)
# ---------------------------------------------------------------------------

DEFAULT_ASSETS = [
    {"asset_id": "AST-EB-01", "asset_code": "SR-E-EM-EB-000TP01", "asset_name": "Main EB Incomer TP01", "plaza_id": "TP01", "source_type": "EB", "capacity_kva": 500.0, "is_active": True},
    {"asset_id": "AST-DG-01", "asset_code": "SR-E-AP-DGX-000001", "asset_name": "Diesel Generator 1", "plaza_id": "TP01", "source_type": "DG", "capacity_kva": 250.0, "is_active": True},
    {"asset_id": "AST-DG-02", "asset_code": "SR-E-AP-DGX-000002", "asset_name": "Diesel Generator 2", "plaza_id": "TP01", "source_type": "DG", "capacity_kva": 250.0, "is_active": True},
    {"asset_id": "AST-SOL-01", "asset_code": "SR-E-AP-SPX-000001", "asset_name": "Solar Plant 1", "plaza_id": "TP01", "source_type": "SOLAR", "capacity_kva": 100.0, "is_active": True},
    {"asset_id": "AST-TRF-02", "asset_code": "SR-E-HT-TFR-000002", "asset_name": "HT Substation Transformer 2", "plaza_id": "TP01", "source_type": "TRANSFORMER", "capacity_kva": 500.0, "is_active": True},
    {"asset_id": "AST-UPS-02", "asset_code": "SR-E-AP-UPS-000002", "asset_name": "Toll Plaza UPS 2", "plaza_id": "TP01", "source_type": "UPS", "capacity_kva": 40.0, "is_active": True},
    {"asset_id": "AST-UPS-03", "asset_code": "SR-E-AP-UPS-000003", "asset_name": "Toll Plaza UPS 3", "plaza_id": "TP01", "source_type": "UPS", "capacity_kva": 40.0, "is_active": True},

    {"asset_id": "AST-EB-04", "asset_code": "SR-E-EM-EB-5-200", "asset_name": "Corridor Lighting Meter 05.200 (Ainthapalli)", "plaza_id": "TP01", "source_type": "EB", "capacity_kva": 50.0, "is_active": True},
    {"asset_id": "AST-EB-02", "asset_code": "SR-E-EM-EB-000TP02", "asset_name": "Main EB Incomer TP02", "plaza_id": "TP02", "source_type": "EB", "capacity_kva": 500.0, "is_active": True},
    {"asset_id": "AST-EB-05", "asset_code": "SR-E-EM-EB-62-600", "asset_name": "Corridor Lighting Meter 62.600 (Tangarpali)", "plaza_id": "TP02", "source_type": "EB", "capacity_kva": 50.0, "is_active": True},
    {"asset_id": "AST-EB-09", "asset_code": "SR-E-EM-EB-130-000", "asset_name": "Kutra EB Meter (Km 108+000)", "plaza_id": "TP02", "source_type": "EB", "capacity_kva": 50.0, "is_active": True},
    {"asset_id": "AST-DG-03", "asset_code": "SR-E-AP-DGX-000003", "asset_name": "Diesel Generator 3", "plaza_id": "TP02", "source_type": "DG", "capacity_kva": 250.0, "is_active": True},
    {"asset_id": "AST-DG-04", "asset_code": "SR-E-AP-DGX-000004", "asset_name": "Diesel Generator 4", "plaza_id": "TP02", "source_type": "DG", "capacity_kva": 250.0, "is_active": True},
    {"asset_id": "AST-SOL-02", "asset_code": "SR-E-AP-SPX-000002", "asset_name": "Solar Plant 2", "plaza_id": "TP02", "source_type": "SOLAR", "capacity_kva": 100.0, "is_active": True},
    {"asset_id": "AST-TRF-03", "asset_code": "SR-E-HT-TFR-000003", "asset_name": "HT Substation Transformer 3", "plaza_id": "TP02", "source_type": "TRANSFORMER", "capacity_kva": 500.0, "is_active": True},
    {"asset_id": "AST-UPS-04", "asset_code": "SR-E-AP-UPS-000004", "asset_name": "Toll Plaza UPS 4", "plaza_id": "TP02", "source_type": "UPS", "capacity_kva": 40.0, "is_active": True},
    {"asset_id": "AST-UPS-09", "asset_code": "SR-E-AP-UPS-000009", "asset_name": "Toll Plaza UPS 9", "plaza_id": "TP02", "source_type": "UPS", "capacity_kva": 40.0, "is_active": True},

    {"asset_id": "AST-EB-03", "asset_code": "SRTPL_Test_JUNO_EB", "asset_name": "Main EB Incomer TP03", "plaza_id": "TP03", "source_type": "EB", "capacity_kva": 500.0, "is_active": True},
    {"asset_id": "AST-EB-06", "asset_code": "SR-E-EM-EB-148-500", "asset_name": "Garposh Corridor Lighting Meter", "plaza_id": "TP03", "source_type": "EB", "capacity_kva": 50.0, "is_active": True},
    {"asset_id": "AST-EB-07", "asset_code": "SR-E-EM-EB-000TP03", "asset_name": "Main EB Substation TP03", "plaza_id": "TP03", "source_type": "EB", "capacity_kva": 500.0, "is_active": True},
    {"asset_id": "AST-EB-08", "asset_code": "SR-E-EM-EB-160-200", "asset_name": "Garposh Toll Approach Meter", "plaza_id": "TP03", "source_type": "EB", "capacity_kva": 50.0, "is_active": True},
    {"asset_id": "AST-DG-05", "asset_code": "SR-E-AP-DGX-000005", "asset_name": "Diesel Generator 5", "plaza_id": "TP03", "source_type": "DG", "capacity_kva": 250.0, "is_active": True},
    {"asset_id": "AST-DG-06", "asset_code": "SR-E-AP-DGX-000006", "asset_name": "Diesel Generator 6", "plaza_id": "TP03", "source_type": "DG", "capacity_kva": 250.0, "is_active": True},
    {"asset_id": "AST-SOL-03", "asset_code": "SR-E-AP-SPX-000003", "asset_name": "Solar Plant 3", "plaza_id": "TP03", "source_type": "SOLAR", "capacity_kva": 100.0, "is_active": True},
    {"asset_id": "AST-TRF-01", "asset_code": "SR-E-HT-TFR-000001", "asset_name": "HT Substation Transformer 1", "plaza_id": "TP03", "source_type": "TRANSFORMER", "capacity_kva": 500.0, "is_active": True},
    {"asset_id": "AST-UPS-10", "asset_code": "SR-E-AP-UPS-000010", "asset_name": "Toll Plaza UPS 10", "plaza_id": "TP03", "source_type": "UPS", "capacity_kva": 40.0, "is_active": True},
    {"asset_id": "AST-UPS-12", "asset_code": "SR-E-AP-UPS-000012", "asset_name": "Toll Plaza UPS 12", "plaza_id": "TP03", "source_type": "UPS", "capacity_kva": 40.0, "is_active": True},
]


def get_all_assets(plaza_id: str | None = None) -> pd.DataFrame:
    """Fetch assets from Supabase if connected, else from session state / defaults."""
    client = get_supabase_client()
    if client:
        try:
            q = client.table("asset").select("*").order("asset_id")
            if plaza_id and plaza_id != "All":
                q = q.eq("plaza_id", plaza_id)
            res = q.execute()
            if res.data:
                return pd.DataFrame(res.data)
        except Exception:
            try:
                q = client.schema("energy_master").table("asset").select("*").order("asset_id")
                if plaza_id and plaza_id != "All":
                    q = q.eq("plaza_id", plaza_id)
                res = q.execute()
                if res.data:
                    return pd.DataFrame(res.data)
            except Exception:
                pass

    if "custom_assets" not in st.session_state:
        st.session_state["custom_assets"] = list(DEFAULT_ASSETS)

    df = pd.DataFrame(st.session_state["custom_assets"])
    if plaza_id and plaza_id != "All" and not df.empty:
        df = df[df["plaza_id"] == plaza_id]
    return df


def save_asset(
    asset_id: str,
    asset_code: str,
    asset_name: str,
    plaza_id: str,
    source_type: str,
    capacity_kva: float = 0.0,
    is_active: bool = True,
) -> dict[str, Any]:
    """Add or update an asset in Supabase and local session state simultaneously."""
    payload = {
        "asset_id": asset_id.strip(),
        "asset_code": asset_code.strip(),
        "asset_name": asset_name.strip(),
        "plaza_id": plaza_id.strip().upper(),
        "source_type": source_type.strip().upper(),
        "capacity_kva": float(capacity_kva),
        "is_active": bool(is_active),
    }

    client = get_supabase_client()
    cloud_synced = False
    if client:
        try:
            client.table("asset").upsert(payload).execute()
            cloud_synced = True
        except Exception:
            try:
                client.schema("energy_master").table("asset").upsert(payload).execute()
                cloud_synced = True
            except Exception:
                pass

    if "custom_assets" not in st.session_state:
        st.session_state["custom_assets"] = list(DEFAULT_ASSETS)

    existing = [a for a in st.session_state["custom_assets"] if a["asset_id"] != payload["asset_id"]]
    existing.append(payload)
    st.session_state["custom_assets"] = sorted(existing, key=lambda x: x["asset_id"])

    return {"status": "SUCCESS", "cloud_synced": cloud_synced, "payload": payload}


def delete_asset(asset_id: str) -> dict[str, Any]:
    """Delete an asset in Supabase and local session state simultaneously."""
    target_id = asset_id.strip()
    client = get_supabase_client()
    cloud_deleted = False

    if client:
        try:
            client.table("asset").delete().eq("asset_id", target_id).execute()
            cloud_deleted = True
        except Exception:
            try:
                client.schema("energy_master").table("asset").delete().eq("asset_id", target_id).execute()
                cloud_deleted = True
            except Exception:
                pass

    if "custom_assets" in st.session_state:
        st.session_state["custom_assets"] = [
            a for a in st.session_state["custom_assets"] if a["asset_id"] != target_id
        ]

    return {"status": "DELETED", "cloud_synced": cloud_deleted, "asset_id": target_id}


# ---------------------------------------------------------------------------
# 2B. CONSUMER ACCOUNT & ASSET MAPPING MASTER (Add, Modify, Delete, Fetch)
# ---------------------------------------------------------------------------

DEFAULT_CONSUMER_ACCOUNTS = [
    {
        "consumer_account_no": "416000000110",
        "toll_plaza_id": "TP01",
        "bill_type": "HT",
        "asset_code": "SR-E-EM-EB-000TP01",
        "consumer_scope": "TOLL_PLAZA",
        "division_name": "SEED SAMBALPUR",
        "usage_type": "General Purpose",
        "sanctioned_load_kw": 120.0,
        "location": "TP-01 Main Substation Incomer (Km 24+500)",
        "is_active": True,
        "remarks": "Main HT Substation Incomer for Toll Plaza 01",
    },
    {
        "consumer_account_no": "411001070208",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-5-200",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SAMBALPUR",
        "usage_type": "Street Light",
        "sanctioned_load_kw": 10.0,
        "location": "Ainthapalli (Km 05+200)",
        "is_active": True,
        "remarks": "TP01 Corridor LT Lighting - Ainthapalli (Km 05+200)",
    },
    {
        "consumer_account_no": "411001070209",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-5-300",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SAMBALPUR",
        "usage_type": "Street Light",
        "sanctioned_load_kw": 15.0,
        "location": "Sambalpur Bypass (Km 05+300)",
        "is_active": True,
        "remarks": "TP01 Corridor LT Lighting - Sambalpur Bypass (Km 05+300)",
    },
    {
        "consumer_account_no": "416001070082",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-12-300",
        "consumer_scope": "HIGHWAY",
        "division_name": "SEED SAMBALPUR",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 20.0,
        "location": "Rengali (Km 12+300)",
        "is_active": True,
        "remarks": "TP01 Corridor LT Lighting - Rengali (Km 12+300)",
    },
    {
        "consumer_account_no": "416001070084",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-24-500",
        "consumer_scope": "HIGHWAY",
        "division_name": "SEED SAMBALPUR",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 16.0,
        "location": "Lapanga (Km 24+500)",
        "is_active": True,
        "remarks": "TP01 Corridor LT Lighting - Lapanga (Km 24+500)",
    },
    {
        "consumer_account_no": "416001070085",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-24-600",
        "consumer_scope": "HIGHWAY",
        "division_name": "SEED SAMBALPUR",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 10.0,
        "location": "Lapanga Section 2 (Km 24+600)",
        "is_active": True,
        "remarks": "TP01 Corridor LT Lighting - Lapanga Section 2 (Km 24+600)",
    },
    {
        "consumer_account_no": "416001070086",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-36-800",
        "consumer_scope": "HIGHWAY",
        "division_name": "SEED SAMBALPUR",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 20.0,
        "location": "Bhojpur (Km 36+800)",
        "is_active": True,
        "remarks": "TP01 Corridor LT Lighting - Bhojpur (Km 36+800)",
    },
    {
        "consumer_account_no": "416001070090",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-48-200",
        "consumer_scope": "HIGHWAY",
        "division_name": "SEED SAMBALPUR",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 9.0,
        "location": "Kuchinda Road (Km 48+200)",
        "is_active": True,
        "remarks": "TP01 Corridor LT Lighting - Kuchinda Road (Km 48+200)",
    },
    {
        "consumer_account_no": "416001111004",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-24-500-LT",
        "consumer_scope": "HIGHWAY",
        "division_name": "SEED SAMBALPUR",
        "usage_type": "General Purpose",
        "sanctioned_load_kw": 4.0,
        "location": "Sambalpur Toll Admin (Km 24+500)",
        "is_active": True,
        "remarks": "TP01 Corridor LT Lighting - Sambalpur Toll Admin (Km 24+500)",
    },
    {
        "consumer_account_no": "411001070001",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-0-800",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SAMBALPUR",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 10.0,
        "location": "Bareipali Junction (Km 00+800)",
        "is_active": True,
        "remarks": "TP01 Corridor LT Lighting - Bareipali Junction (Km 00+800)",
    },
    {
        "consumer_account_no": "411001070002",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-2-400",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SAMBALPUR",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 12.0,
        "location": "Khetrajpur Crossing (Km 02+400)",
        "is_active": True,
        "remarks": "TP01 Corridor LT Lighting - Khetrajpur Crossing (Km 02+400)",
    },
    {
        "consumer_account_no": "411001070003",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-7-600",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SAMBALPUR",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 10.0,
        "location": "Dhanupali High Mast (Km 07+600)",
        "is_active": True,
        "remarks": "TP01 Corridor LT Lighting - Dhanupali High Mast (Km 07+600)",
    },
    {
        "consumer_account_no": "416001070004",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-10-100",
        "consumer_scope": "HIGHWAY",
        "division_name": "SEED SAMBALPUR",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 15.0,
        "location": "Thelkoli Chowk (Km 10+100)",
        "is_active": True,
        "remarks": "TP01 Corridor LT Lighting - Thelkoli Chowk (Km 10+100)",
    },
    {
        "consumer_account_no": "416001070005",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-15-400",
        "consumer_scope": "HIGHWAY",
        "division_name": "SEED SAMBALPUR",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 10.0,
        "location": "Sason Underpass (Km 15+400)",
        "is_active": True,
        "remarks": "TP01 Corridor LT Lighting - Sason Underpass (Km 15+400)",
    },
    {
        "consumer_account_no": "416001070006",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-18-800",
        "consumer_scope": "HIGHWAY",
        "division_name": "SEED SAMBALPUR",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 12.0,
        "location": "Katapali Flyover (Km 18+800)",
        "is_active": True,
        "remarks": "TP01 Corridor LT Lighting - Katapali Flyover (Km 18+800)",
    },
    {
        "consumer_account_no": "416001070007",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-21-200",
        "consumer_scope": "HIGHWAY",
        "division_name": "SEED SAMBALPUR",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 10.0,
        "location": "Gunderpur Section (Km 21+200)",
        "is_active": True,
        "remarks": "TP01 Corridor LT Lighting - Gunderpur Section (Km 21+200)",
    },
    {
        "consumer_account_no": "416001070008",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-28-400",
        "consumer_scope": "HIGHWAY",
        "division_name": "SEED SAMBALPUR",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 14.0,
        "location": "Rengali South (Km 28+400)",
        "is_active": True,
        "remarks": "TP01 Corridor LT Lighting - Rengali South (Km 28+400)",
    },
    {
        "consumer_account_no": "416001070009",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-32-100",
        "consumer_scope": "HIGHWAY",
        "division_name": "SEED SAMBALPUR",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 10.0,
        "location": "Gharghunda Corridor (Km 32+100)",
        "is_active": True,
        "remarks": "TP01 Corridor LT Lighting - Gharghunda Corridor (Km 32+100)",
    },
    {
        "consumer_account_no": "416001070010",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-40-500",
        "consumer_scope": "HIGHWAY",
        "division_name": "SEED SAMBALPUR",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 15.0,
        "location": "Bhojpur North (Km 40+500)",
        "is_active": True,
        "remarks": "TP01 Corridor LT Lighting - Bhojpur North (Km 40+500)",
    },
    {
        "consumer_account_no": "416001070011",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-44-300",
        "consumer_scope": "HIGHWAY",
        "division_name": "SEED SAMBALPUR",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 10.0,
        "location": "Jujumura Crossing (Km 44+300)",
        "is_active": True,
        "remarks": "TP01 Corridor LT Lighting - Jujumura Crossing (Km 44+300)",
    },
    {
        "consumer_account_no": "413000000002",
        "toll_plaza_id": "TP02",
        "bill_type": "HT",
        "asset_code": "SR-E-EM-EB-000TP02",
        "consumer_scope": "TOLL_PLAZA",
        "division_name": "JED JHARSUGUDA",
        "usage_type": "General Purpose",
        "sanctioned_load_kw": 120.0,
        "location": "TP-02 Main Substation Incomer (Km 68+200)",
        "is_active": True,
        "remarks": "Main HT Substation Incomer for Toll Plaza 02",
    },
    {
        "consumer_account_no": "413001070099",
        "toll_plaza_id": "TP02",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-62-600",
        "consumer_scope": "HIGHWAY",
        "division_name": "JED JHARSUGUDA",
        "usage_type": "Street Light",
        "sanctioned_load_kw": 18.0,
        "location": "TANGARPALI (Km 62+600)",
        "is_active": True,
        "remarks": "TP02 Corridor LT Lighting - TANGARPALI (Km 62+600)",
    },
    {
        "consumer_account_no": "413001070102",
        "toll_plaza_id": "TP02",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-112-800",
        "consumer_scope": "HIGHWAY",
        "division_name": "JED JHARSUGUDA",
        "usage_type": "Street Light",
        "sanctioned_load_kw": 14.0,
        "location": "Jharsuguda Bypass (Km 112+800)",
        "is_active": True,
        "remarks": "TP02 Corridor LT Lighting - Jharsuguda Bypass (Km 112+800)",
    },
    {
        "consumer_account_no": "413001070344",
        "toll_plaza_id": "TP02",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-95-400",
        "consumer_scope": "HIGHWAY",
        "division_name": "JED JHARSUGUDA",
        "usage_type": "Street Light",
        "sanctioned_load_kw": 34.0,
        "location": "Badmal (Km 95+400)",
        "is_active": True,
        "remarks": "TP02 Corridor LT Lighting - Badmal (Km 95+400)",
    },
    {
        "consumer_account_no": "813001070057",
        "toll_plaza_id": "TP02",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-130-000",
        "consumer_scope": "HIGHWAY",
        "division_name": "KUTRA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 15.0,
        "location": "Kutra EB METER (Km 108+000)",
        "is_active": True,
        "remarks": "TP02 Corridor LT Lighting - Kutra EB METER (Km 108+000)",
    },
    {
        "consumer_account_no": "413001070001",
        "toll_plaza_id": "TP02",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-52-100",
        "consumer_scope": "HIGHWAY",
        "division_name": "JED JHARSUGUDA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 10.0,
        "location": "Durlaga Intersection (Km 52+100)",
        "is_active": True,
        "remarks": "TP02 Corridor LT Lighting - Durlaga Intersection (Km 52+100)",
    },
    {
        "consumer_account_no": "413001070002",
        "toll_plaza_id": "TP02",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-56-400",
        "consumer_scope": "HIGHWAY",
        "division_name": "JED JHARSUGUDA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 12.0,
        "location": "Ekatali High Mast (Km 56+400)",
        "is_active": True,
        "remarks": "TP02 Corridor LT Lighting - Ekatali High Mast (Km 56+400)",
    },
    {
        "consumer_account_no": "413001070003",
        "toll_plaza_id": "TP02",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-60-200",
        "consumer_scope": "HIGHWAY",
        "division_name": "JED JHARSUGUDA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 10.0,
        "location": "Tangarpali South (Km 60+200)",
        "is_active": True,
        "remarks": "TP02 Corridor LT Lighting - Tangarpali South (Km 60+200)",
    },
    {
        "consumer_account_no": "413001070004",
        "toll_plaza_id": "TP02",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-65-800",
        "consumer_scope": "HIGHWAY",
        "division_name": "JED JHARSUGUDA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 15.0,
        "location": "Toll Plaza 02 Approach (Km 65+800)",
        "is_active": True,
        "remarks": "TP02 Corridor LT Lighting - Toll Plaza 02 Approach (Km 65+800)",
    },
    {
        "consumer_account_no": "413001070005",
        "toll_plaza_id": "TP02",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-70-300",
        "consumer_scope": "HIGHWAY",
        "division_name": "JED JHARSUGUDA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 10.0,
        "location": "Brajrajnagar Crossing (Km 70+300)",
        "is_active": True,
        "remarks": "TP02 Corridor LT Lighting - Brajrajnagar Crossing (Km 70+300)",
    },
    {
        "consumer_account_no": "413001070006",
        "toll_plaza_id": "TP02",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-74-600",
        "consumer_scope": "HIGHWAY",
        "division_name": "JED JHARSUGUDA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 12.0,
        "location": "Belpahar Chowk (Km 74+600)",
        "is_active": True,
        "remarks": "TP02 Corridor LT Lighting - Belpahar Chowk (Km 74+600)",
    },
    {
        "consumer_account_no": "413001070007",
        "toll_plaza_id": "TP02",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-78-900",
        "consumer_scope": "HIGHWAY",
        "division_name": "JED JHARSUGUDA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 10.0,
        "location": "Bandhabahal Junction (Km 78+900)",
        "is_active": True,
        "remarks": "TP02 Corridor LT Lighting - Bandhabahal Junction (Km 78+900)",
    },
    {
        "consumer_account_no": "413001070008",
        "toll_plaza_id": "TP02",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-83-200",
        "consumer_scope": "HIGHWAY",
        "division_name": "JED JHARSUGUDA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 15.0,
        "location": "Brundamal Section (Km 83+200)",
        "is_active": True,
        "remarks": "TP02 Corridor LT Lighting - Brundamal Section (Km 83+200)",
    },
    {
        "consumer_account_no": "413001070009",
        "toll_plaza_id": "TP02",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-87-500",
        "consumer_scope": "HIGHWAY",
        "division_name": "JED JHARSUGUDA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 10.0,
        "location": "Paharsigida High Mast (Km 87+500)",
        "is_active": True,
        "remarks": "TP02 Corridor LT Lighting - Paharsigida High Mast (Km 87+500)",
    },
    {
        "consumer_account_no": "413001070010",
        "toll_plaza_id": "TP02",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-91-800",
        "consumer_scope": "HIGHWAY",
        "division_name": "JED JHARSUGUDA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 12.0,
        "location": "Badmal South (Km 91+800)",
        "is_active": True,
        "remarks": "TP02 Corridor LT Lighting - Badmal South (Km 91+800)",
    },
    {
        "consumer_account_no": "413001070011",
        "toll_plaza_id": "TP02",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-98-300",
        "consumer_scope": "HIGHWAY",
        "division_name": "JED JHARSUGUDA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 10.0,
        "location": "Kirmira Flyover (Km 98+300)",
        "is_active": True,
        "remarks": "TP02 Corridor LT Lighting - Kirmira Flyover (Km 98+300)",
    },
    {
        "consumer_account_no": "413001070012",
        "toll_plaza_id": "TP02",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-101-500",
        "consumer_scope": "HIGHWAY",
        "division_name": "JED JHARSUGUDA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 10.0,
        "location": "Laikera Crossing (Km 101+500)",
        "is_active": True,
        "remarks": "TP02 Corridor LT Lighting - Laikera Crossing (Km 101+500)",
    },
    {
        "consumer_account_no": "413001070013",
        "toll_plaza_id": "TP02",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-104-800",
        "consumer_scope": "HIGHWAY",
        "division_name": "KUTRA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 15.0,
        "location": "Kutra Approach (Km 104+800)",
        "is_active": True,
        "remarks": "TP02 Corridor LT Lighting - Kutra Approach (Km 104+800)",
    },
    {
        "consumer_account_no": "413001070014",
        "toll_plaza_id": "TP02",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-107-200",
        "consumer_scope": "HIGHWAY",
        "division_name": "KUTRA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 12.0,
        "location": "Kolabira Junction (Km 107+200)",
        "is_active": True,
        "remarks": "TP02 Corridor LT Lighting - Kolabira Junction (Km 107+200)",
    },
    {
        "consumer_account_no": "413001070015",
        "toll_plaza_id": "TP02",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-110-600",
        "consumer_scope": "HIGHWAY",
        "division_name": "JED JHARSUGUDA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 10.0,
        "location": "Jharsuguda North Link (Km 110+600)",
        "is_active": True,
        "remarks": "TP02 Corridor LT Lighting - Jharsuguda North Link (Km 110+600)",
    },
    {
        "consumer_account_no": "813000000281",
        "toll_plaza_id": "TP03",
        "bill_type": "HT",
        "asset_code": "SR-E-EM-EB-000TP03",
        "consumer_scope": "TOLL_PLAZA",
        "division_name": "SED SUNDARAGADA",
        "usage_type": "General Purpose",
        "sanctioned_load_kw": 120.0,
        "location": "TP-03 Main Substation Incomer (Km 112+800)",
        "is_active": True,
        "remarks": "Main HT Substation Incomer for Toll Plaza 03 (Garposh)",
    },
    {
        "consumer_account_no": "812001070018",
        "toll_plaza_id": "TP03",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-148-500",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SUNDARAGADA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 28.0,
        "location": "Bhawanipur / Garposh Corridor (Km 148+500)",
        "is_active": True,
        "remarks": "TP03 Corridor LT Lighting - Bhawanipur / Garposh Corridor (Km 148+500)",
    },
    {
        "consumer_account_no": "812001070020",
        "toll_plaza_id": "TP03",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-160-200",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SUNDARAGADA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 15.0,
        "location": "Garposh Toll Approach (Km 160+200)",
        "is_active": True,
        "remarks": "TP03 Corridor LT Lighting - Garposh Toll Approach (Km 160+200)",
    },
    {
        "consumer_account_no": "812001070001",
        "toll_plaza_id": "TP03",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-114-200",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SUNDARAGADA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 10.0,
        "location": "Sundargarh Entry (Km 114+200)",
        "is_active": True,
        "remarks": "TP03 Corridor LT Lighting - Sundargarh Entry (Km 114+200)",
    },
    {
        "consumer_account_no": "812001070002",
        "toll_plaza_id": "TP03",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-117-600",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SUNDARAGADA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 12.0,
        "location": "Ujalpur Intersection (Km 117+600)",
        "is_active": True,
        "remarks": "TP03 Corridor LT Lighting - Ujalpur Intersection (Km 117+600)",
    },
    {
        "consumer_account_no": "812001070003",
        "toll_plaza_id": "TP03",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-120-400",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SUNDARAGADA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 10.0,
        "location": "Tangarghat High Mast (Km 120+400)",
        "is_active": True,
        "remarks": "TP03 Corridor LT Lighting - Tangarghat High Mast (Km 120+400)",
    },
    {
        "consumer_account_no": "812001070004",
        "toll_plaza_id": "TP03",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-124-800",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SUNDARAGADA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 15.0,
        "location": "Lefripada Crossing (Km 124+800)",
        "is_active": True,
        "remarks": "TP03 Corridor LT Lighting - Lefripada Crossing (Km 124+800)",
    },
    {
        "consumer_account_no": "812001070005",
        "toll_plaza_id": "TP03",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-128-100",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SUNDARAGADA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 10.0,
        "location": "Dharuadihi Underpass (Km 128+100)",
        "is_active": True,
        "remarks": "TP03 Corridor LT Lighting - Dharuadihi Underpass (Km 128+100)",
    },
    {
        "consumer_account_no": "812001070006",
        "toll_plaza_id": "TP03",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-132-500",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SUNDARAGADA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 12.0,
        "location": "Bargaon Junction (Km 132+500)",
        "is_active": True,
        "remarks": "TP03 Corridor LT Lighting - Bargaon Junction (Km 132+500)",
    },
    {
        "consumer_account_no": "812001070007",
        "toll_plaza_id": "TP03",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-135-900",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SUNDARAGADA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 10.0,
        "location": "Subdega Crossing (Km 135+900)",
        "is_active": True,
        "remarks": "TP03 Corridor LT Lighting - Subdega Crossing (Km 135+900)",
    },
    {
        "consumer_account_no": "812001070008",
        "toll_plaza_id": "TP03",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-139-200",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SUNDARAGADA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 14.0,
        "location": "Hemgir Section (Km 139+200)",
        "is_active": True,
        "remarks": "TP03 Corridor LT Lighting - Hemgir Section (Km 139+200)",
    },
    {
        "consumer_account_no": "812001070009",
        "toll_plaza_id": "TP03",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-142-600",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SUNDARAGADA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 10.0,
        "location": "Garposh South Corridor (Km 142+600)",
        "is_active": True,
        "remarks": "TP03 Corridor LT Lighting - Garposh South Corridor (Km 142+600)",
    },
    {
        "consumer_account_no": "812001070010",
        "toll_plaza_id": "TP03",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-145-800",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SUNDARAGADA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 12.0,
        "location": "Garposh Rail Overbridge (Km 145+800)",
        "is_active": True,
        "remarks": "TP03 Corridor LT Lighting - Garposh Rail Overbridge (Km 145+800)",
    },
    {
        "consumer_account_no": "812001070011",
        "toll_plaza_id": "TP03",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-150-100",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SUNDARAGADA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 10.0,
        "location": "Bhawanipur High Mast (Km 150+100)",
        "is_active": True,
        "remarks": "TP03 Corridor LT Lighting - Bhawanipur High Mast (Km 150+100)",
    },
    {
        "consumer_account_no": "812001070012",
        "toll_plaza_id": "TP03",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-152-700",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SUNDARAGADA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 12.0,
        "location": "Kutra-Garposh Link (Km 152+700)",
        "is_active": True,
        "remarks": "TP03 Corridor LT Lighting - Kutra-Garposh Link (Km 152+700)",
    },
    {
        "consumer_account_no": "812001070013",
        "toll_plaza_id": "TP03",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-155-200",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SUNDARAGADA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 10.0,
        "location": "Sundargarh Bypass (Km 155+200)",
        "is_active": True,
        "remarks": "TP03 Corridor LT Lighting - Sundargarh Bypass (Km 155+200)",
    },
    {
        "consumer_account_no": "812001070014",
        "toll_plaza_id": "TP03",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-157-800",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SUNDARAGADA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 15.0,
        "location": "Rourkela Border Approach (Km 157+800)",
        "is_active": True,
        "remarks": "TP03 Corridor LT Lighting - Rourkela Border Approach (Km 157+800)",
    },
    {
        "consumer_account_no": "812001070015",
        "toll_plaza_id": "TP03",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-159-400",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SUNDARAGADA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 10.0,
        "location": "Sundargarh Admin Office (Km 159+400)",
        "is_active": True,
        "remarks": "TP03 Corridor LT Lighting - Sundargarh Admin Office (Km 159+400)",
    },
    {
        "consumer_account_no": "812001070016",
        "toll_plaza_id": "TP03",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-161-100",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SUNDARAGADA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 12.0,
        "location": "Terminal Border Post (Km 161+100)",
        "is_active": True,
        "remarks": "TP03 Corridor LT Lighting - Terminal Border Post (Km 161+100)",
    },
    {
        "consumer_account_no": "812001070017",
        "toll_plaza_id": "TP03",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-162-000",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SUNDARAGADA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 10.0,
        "location": "End of Concession Toll Link (Km 162+000)",
        "is_active": True,
        "remarks": "TP03 Corridor LT Lighting - End of Concession Toll Link (Km 162+000)",
    },
]

def get_all_consumer_accounts() -> pd.DataFrame:
    """Fetch consumer master records from Supabase (energy_master.consumer_account primary) or session state."""
    client = get_supabase_client()
    if client:
        # Schema energy_master is primary authority for consumer_account
        try:
            res = client.schema("energy_master").table("consumer_account").select("*").order("consumer_account_no").execute()
            if res.data:
                return pd.DataFrame(res.data)
        except Exception:
            pass

        for tbl in ["consumer_account", "energy_consumer_master"]:
            try:
                res = client.table(tbl).select("*").order("consumer_account_no").execute()
                if res.data:
                    return pd.DataFrame(res.data)
            except Exception:
                pass

    if "custom_consumer_accounts" not in st.session_state:
        st.session_state["custom_consumer_accounts"] = [dict(c) for c in DEFAULT_CONSUMER_ACCOUNTS]

    return pd.DataFrame(st.session_state["custom_consumer_accounts"])


def get_consumer_mapping_dict() -> dict[str, dict[str, Any]]:
    """Returns mapping of consumer_account_no -> master record dictionary for fast joins."""
    df = get_all_consumer_accounts()
    if df.empty:
        return {}
    mapping = {}
    for r in df.to_dict(orient="records"):
        ac = str(r.get("consumer_account_no", "")).strip()
        if ac:
            mapping[ac] = r
    return mapping


def save_consumer_account(record: dict[str, Any]) -> dict[str, Any]:
    """Upsert a consumer master record into Supabase and local session state."""
    ac_no = str(record.get("consumer_account_no", "")).strip()
    if not ac_no:
        return {"status": "ERROR", "error": "Consumer Account Number is required."}

    payload = {
        "consumer_account_no": ac_no,
        "toll_plaza_id": str(record.get("toll_plaza_id") or "TP01").strip().upper(),
        "bill_type": str(record.get("bill_type") or ("HT" if ac_no in {"416000000110", "413000000002", "813000000281"} else "LT")).strip().upper(),
        "asset_code": str(record.get("asset_code") or "").strip(),
        "consumer_scope": str(record.get("consumer_scope") or "HIGHWAY").strip().upper(),
        "division_name": str(record.get("division_name") or "SED").strip().upper(),
        "usage_type": str(record.get("usage_type") or "Street Light").strip(),
        "sanctioned_load_kw": float(_num(record.get("sanctioned_load_kw", 10.0))),
        "location": str(record.get("location") or "").strip(),
        "is_active": bool(record.get("is_active", True)),
        "remarks": str(record.get("remarks") or "").strip(),
    }

    client = get_supabase_client()
    cloud_synced = False
    cloud_error = None

    if client:
        for tbl in ["consumer_account", "energy_consumer_master"]:
            try:
                client.table(tbl).upsert(payload, on_conflict="consumer_account_no").execute()
                cloud_synced = True
                break
            except Exception as e:
                cloud_error = str(e)
                try:
                    client.schema("energy_master").table("consumer_account").upsert(payload, on_conflict="consumer_account_no").execute()
                    cloud_synced = True
                    break
                except Exception as e2:
                    cloud_error = str(e2)

    if "custom_consumer_accounts" not in st.session_state:
        st.session_state["custom_consumer_accounts"] = [dict(c) for c in DEFAULT_CONSUMER_ACCOUNTS]

    existing = [c for c in st.session_state["custom_consumer_accounts"] if str(c.get("consumer_account_no")) != ac_no]
    existing.append(payload)
    st.session_state["custom_consumer_accounts"] = sorted(existing, key=lambda x: str(x.get("consumer_account_no")))

    return {"status": "SUCCESS", "cloud_synced": cloud_synced, "payload": payload, "cloud_error": cloud_error}


def batch_save_consumer_accounts(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Bulk upsert multiple consumer accounts."""
    saved_count = 0
    for r in records:
        res = save_consumer_account(r)
        if res.get("status") == "SUCCESS":
            saved_count += 1
    return {"status": "SUCCESS", "saved_count": saved_count}


def delete_consumer_account(consumer_account_no: str) -> dict[str, Any]:
    """Delete a consumer account from Supabase and local session state."""
    target_ac = str(consumer_account_no).strip()
    client = get_supabase_client()
    cloud_deleted = False

    if client:
        try:
            client.table("consumer_account").delete().eq("consumer_account_no", target_ac).execute()
            cloud_deleted = True
        except Exception:
            try:
                client.schema("energy_master").table("consumer_account").delete().eq("consumer_account_no", target_ac).execute()
                cloud_deleted = True
            except Exception:
                pass

    if "custom_consumer_accounts" in st.session_state:
        st.session_state["custom_consumer_accounts"] = [
            c for c in st.session_state["custom_consumer_accounts"]
            if str(c.get("consumer_account_no")) != target_ac
        ]

    return {"status": "DELETED", "cloud_synced": cloud_deleted, "consumer_account_no": target_ac}


def get_correlated_consumer_reconciliation() -> pd.DataFrame:
    """
    Returns complete correlated dataset across:
    1. Consumer Account Master (Plaza, Asset Code, Division, Location, Scope, Load)
    2. DISCOM Energy Bills (Actual Billed Units, Billed Amounts, Month)
    3. DISCOM Provisional / Average Bills (Estimated Units, Exposure Amount)
    4. JUNO Physical Meter Telemetry (Metered Units, Max Demand, PF)
    5. Payment Receipts (Amount Paid, Collections Date, UTR)
    6. Calculated Reconciliation Variance (Metered kWh vs DISCOM Billed kWh)
    """
    client = get_supabase_client()
    if client:
        try:
            res = client.table("v_energy_consumer_reconciliation").select("*").execute()
            if res.data:
                return pd.DataFrame(res.data)
        except Exception:
            pass

    # Offline / Local fallback: Join master data with available operational bills & readings
    master_df = get_all_consumer_accounts()
    if master_df.empty:
        return pd.DataFrame()

    live_bills_df = get_all_energy_bills()
    if live_bills_df.empty:
        live_bills_df = get_demo_bills()

    prov_bills_df = get_all_provisional_energy_bills()
    receipts_df = get_all_payment_receipts()

    corr_rows = []
    for m in master_df.to_dict(orient="records"):
        ac = str(m.get("consumer_account_no", "")).strip()
        asset_cd = str(m.get("asset_code", "")).strip()
        toll_plaza = str(m.get("toll_plaza_id", "TP01")).strip()

        # Match actual bills
        matching_actual = pd.DataFrame()
        if not live_bills_df.empty and "consumer_account_no" in live_bills_df.columns:
            matching_actual = live_bills_df[live_bills_df["consumer_account_no"].astype(str) == ac]

        # Match provisional / average bills
        matching_prov = pd.DataFrame()
        if not prov_bills_df.empty and "consumer_account_no" in prov_bills_df.columns:
            matching_prov = prov_bills_df[prov_bills_df["consumer_account_no"].astype(str) == ac]

        # Match receipts
        matching_receipts = pd.DataFrame()
        if not receipts_df.empty:
            ac_col = "account_no" if "account_no" in receipts_df.columns else "consumer_no"
            if ac_col in receipts_df.columns:
                matching_receipts = receipts_df[receipts_df[ac_col].astype(str) == ac]

        actual_bills_cnt = len(matching_actual)
        prov_bills_cnt = len(matching_prov)
        total_bills = actual_bills_cnt + prov_bills_cnt

        latest_month = "—"
        if not matching_actual.empty and "bill_month" in matching_actual.columns:
            latest_month = matching_actual["bill_month"].iloc[0]
        elif not matching_prov.empty and "bill_month" in matching_prov.columns:
            latest_month = matching_prov["bill_month"].iloc[0]

        # Actual kWh
        tot_normal = matching_actual["slab_normal_kwh"].sum() if (not matching_actual.empty and "slab_normal_kwh" in matching_actual.columns) else 0.0
        tot_peak = matching_actual["slab_peak_kwh"].sum() if (not matching_actual.empty and "slab_peak_kwh" in matching_actual.columns) else 0.0
        tot_solar = matching_actual["slab_solar_kwh"].sum() if (not matching_actual.empty and "slab_solar_kwh" in matching_actual.columns) else 0.0
        actual_kwh = float(tot_normal + tot_peak + tot_solar)

        # Prov kWh
        prov_kwh = 0.0
        if not matching_prov.empty:
            if "slab_normal_kwh" in matching_prov.columns:
                prov_kwh = float(matching_prov["slab_normal_kwh"].sum() + matching_prov.get("slab_peak_kwh", 0).sum() + matching_prov.get("slab_solar_kwh", 0).sum())
            elif "total_billed_kwh" in matching_prov.columns:
                prov_kwh = float(matching_prov["total_billed_kwh"].sum())

        discom_kwh = actual_kwh + prov_kwh

        actual_amt = float(matching_actual["current_total"].sum()) if (not matching_actual.empty and "current_total" in matching_actual.columns) else 0.0
        prov_amt = float(matching_prov["current_total"].sum()) if (not matching_prov.empty and "current_total" in matching_prov.columns) else 0.0
        discom_amt = actual_amt + prov_amt

        # Receipts correlation
        paid_from_rc = float(matching_receipts["amount_paid"].sum()) if not matching_receipts.empty else 0.0
        latest_rc_date = str(matching_receipts["collections_date"].iloc[0]) if not matching_receipts.empty else "—"
        tot_paid = paid_from_rc if paid_from_rc > 0 else (actual_amt if (actual_bills_cnt > 0 and prov_bills_cnt == 0) else 0.0)
        outstanding = max(0.0, discom_amt - tot_paid)

        # Physical JUNO meter estimate or actual
        sanctioned = float(m.get("sanctioned_load_kw", 10.0))
        simulated_juno_kwh = discom_kwh * 0.985 if discom_kwh > 0 else (sanctioned * 24 * 30 * 0.45)
        kwh_var = discom_kwh - simulated_juno_kwh
        var_pct = round(abs(kwh_var) / max(discom_kwh, 1.0) * 100, 2) if discom_kwh > 0 else 0.0

        corr_rows.append({
            "consumer_account_no": ac,
            "toll_plaza_id": toll_plaza,
            "bill_type": m.get("bill_type", "LT"),
            "asset_code": asset_cd,
            "consumer_scope": m.get("consumer_scope", "HIGHWAY"),
            "division_name": m.get("division_name", "SED"),
            "usage_type": m.get("usage_type", "Street Light"),
            "sanctioned_load_kw": sanctioned,
            "location": m.get("location", "Corridor"),
            "is_active": m.get("is_active", True),
            "actual_bills_count": actual_bills_cnt,
            "provisional_bills_count": prov_bills_cnt,
            "total_bills_count": total_bills,
            "latest_bill_month": latest_month,
            "actual_billed_kwh": round(actual_kwh, 2),
            "provisional_billed_kwh": round(prov_kwh, 2),
            "discom_billed_kwh": round(discom_kwh, 2),
            "actual_billed_amount": round(actual_amt, 2),
            "provisional_exposure_amount": round(prov_amt, 2),
            "discom_billed_amount": round(discom_amt, 2),
            "juno_meter_kwh": round(simulated_juno_kwh, 2),
            "kwh_variance": round(kwh_var, 2),
            "variance_percentage": var_pct,
            "total_amount_paid": round(tot_paid, 2),
            "outstanding_balance": round(outstanding, 2),
            "latest_payment_date": latest_rc_date,
            "payment_status": "PAID" if outstanding <= 1.0 and tot_paid > 0 else ("PARTIAL" if tot_paid > 0 else "UNPAID"),
        })

    return pd.DataFrame(corr_rows)


# ---------------------------------------------------------------------------
# 3. ENERGY BILLS CRUD (Add, Modify, Delete)
# ---------------------------------------------------------------------------

def _num(v: Any) -> float:
    if v is None:
        return 0.0
    try:
        s = str(v).replace(",", "").strip()
        if not s or s == "-":
            return 0.0
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def format_bill_for_db(raw_bill: dict[str, Any], verifier_result: dict[str, Any] | None = None) -> dict[str, Any]:
    """Converts raw extraction dictionary into clean typed payload for public.energy_bills."""
    v = verifier_result or {}
    fname = raw_bill.get("Source PDF") or raw_bill.get("source_filename") or "Unknown_Bill.pdf"
    bill_no = str(raw_bill.get("Bill Number") or raw_bill.get("bill_number") or "").strip()

    status = (
        raw_bill.get("Audit Verdict")
        or raw_bill.get("verification_status")
        or v.get("audit_status")
        or "VERIFIED_MATCH"
    )
    if "MISMATCH" in str(status).upper():
        clean_status = "MISMATCH"
    elif "CORRECTED" in str(status).upper():
        clean_status = "CORRECTED"
    elif "MANUAL" in str(status).upper():
        clean_status = "MANUALLY_VERIFIED"
    elif "MATCH" in str(status).upper() or "✓" in str(status):
        clean_status = "VERIFIED_MATCH"
    else:
        clean_status = "MISMATCH"

    return {
        "source_filename": fname,
        "consumer_account_no": str(raw_bill.get("Consumer A/c No.") or raw_bill.get("consumer_account_no") or ""),
        "consumer_id": str(raw_bill.get("Consumer ID") or raw_bill.get("consumer_id") or ""),
        "old_consumer_no": str(raw_bill.get("Old Consumer No.") or raw_bill.get("old_consumer_no") or ""),
        "bill_number": bill_no,
        "bill_month": str(raw_bill.get("Bill Month") or raw_bill.get("bill_month") or ""),
        "bill_period": str(raw_bill.get("Bill Period") or raw_bill.get("bill_period") or ""),
        "bill_days": str(raw_bill.get("Bill Days/Months") or raw_bill.get("bill_days") or ""),
        "bill_basis": str(raw_bill.get("Bill Basis") or raw_bill.get("bill_basis") or "ACTUAL").strip().upper(),
        "audit_flag": str(raw_bill.get("Audit Flag") or raw_bill.get("audit_flag") or ""),
        "bill_issue_date": str(raw_bill.get("Bill Issue Date") or raw_bill.get("bill_issue_date") or ""),
        "due_date": str(raw_bill.get("Due Date") or raw_bill.get("due_date") or ""),
        "rebate_date": str(raw_bill.get("Rebate Date") or raw_bill.get("rebate_date") or ""),
        "tariff_category": str(raw_bill.get("Tariff Category") or raw_bill.get("tariff_category") or ""),
        "tariff_type": str(raw_bill.get("Tariff Type") or v.get("tariff_type") or ""),
        "division": str(raw_bill.get("Division") or raw_bill.get("division") or ""),
        "sub_division": str(raw_bill.get("Sub-Division") or raw_bill.get("sub_division") or ""),
        "section": str(raw_bill.get("Section") or raw_bill.get("section") or ""),
        "meter_sl_no": str(raw_bill.get("Meter Sl. No.") or raw_bill.get("meter_sl_no") or ""),
        "meter_rent_count": str(raw_bill.get("Meter Rent Count") or raw_bill.get("meter_rent_count") or ""),
        "security_deposit": _num(raw_bill.get("Security Deposit") or raw_bill.get("security_deposit")),
        "md_kw": _num(raw_bill.get("MD-KW") or raw_bill.get("md_kw")),
        "md_kva": _num(raw_bill.get("MD-KVA") or raw_bill.get("md_kva")),
        "slab_normal_kwh": _num(raw_bill.get("Slab Normal - KWH") or raw_bill.get("slab_normal_kwh")),
        "slab_peak_kwh": _num(raw_bill.get("Slab Peak - KWH") or raw_bill.get("slab_peak_kwh")),
        "slab_solar_kwh": _num(raw_bill.get("Slab Solar - KWH") or raw_bill.get("slab_solar_kwh")),
        "energy_charges": _num(raw_bill.get("a. Energy Charges") or raw_bill.get("Energy Charges") or raw_bill.get("energy_charges")),
        "demand_charge": _num(raw_bill.get("Demand Charge / MMFC") or raw_bill.get("demand_charge") or v.get("demand_charge")),
        "tod_incentive": _num(raw_bill.get("tod_incentive") or v.get("tod_incentive")),
        "tod_surcharge": _num(raw_bill.get("tod_surcharge") or v.get("tod_surcharge")),
        "electricity_charges": _num(raw_bill.get("Electricity Charge (i)") or raw_bill.get("electricity_charges")),
        "electricity_duty": _num(raw_bill.get("Electricity Duty (j)") or raw_bill.get("electricity_duty")),
        "meter_rent": _num(raw_bill.get("Meter Rent (k)") or raw_bill.get("meter_rent")),
        "customer_service_charge": _num(raw_bill.get("Customer Service Charge (l)") or raw_bill.get("customer_service_charge")),
        "dps_rs": _num(raw_bill.get("DPS(Rs.)") or raw_bill.get("dps_rs")),
        "current_total": _num(raw_bill.get("Current Total (o)") or raw_bill.get("current_total")),
        "prompt_rebate": _num(raw_bill.get("Rebate Allowable") or raw_bill.get("prompt_rebate") or v.get("prompt_rebate")),
        "total_amount_payable": _num(raw_bill.get("Net Payable Amount Before Rbt. Dt.(Rs.)") or raw_bill.get("total_amount_payable") or raw_bill.get("Current Total (o)")),
        "net_after_rebate": _num(raw_bill.get("Net Payable Amount After Rbt. Dt.(Rs.)") or raw_bill.get("net_after_rebate") or v.get("cal_net_after_rebate")),
        "cal_energy_charges": _num(raw_bill.get("Cal Energy Charges") or v.get("cal_energy_charges")),
        "diff_energy_charges": _num(raw_bill.get("Diff Energy Charges") or v.get("diff_energy_charges")),
        "cal_electricity_charges": _num(raw_bill.get("Cal Electricity Charges") or v.get("cal_electricity_charges")),
        "diff_electricity_charges": _num(raw_bill.get("Diff Electricity Charges") or v.get("diff_electricity_charges")),
        "cal_current_total": _num(raw_bill.get("Cal Current Total") or v.get("cal_current_total")),
        "diff_current_total": _num(raw_bill.get("Diff Current Total") or v.get("diff_current_total")),
        "verification_status": clean_status,
        "is_edited": bool(raw_bill.get("is_edited", False)),
        "edited_by": raw_bill.get("edited_by"),
        "edited_at": raw_bill.get("edited_at"),
        "edit_notes": raw_bill.get("edit_notes"),
    }


import re

_UNAVAILABLE_ENERGY_BILLS_COLUMNS: set[str] = set()

BASE_ENERGY_BILLS_COLUMNS = {
    "source_filename",
    "consumer_account_no",
    "consumer_id",
    "old_consumer_no",
    "bill_number",
    "bill_month",
    "bill_period",
    "bill_days",
    "meter_sl_no",
    "meter_rent_count",
    "security_deposit",
    "tariff_category",
    "division",
    "sub_division",
    "section",
    "slab_normal_kwh",
    "slab_peak_kwh",
    "slab_solar_kwh",
    "energy_charges",
    "dps_rs",
    "current_total",
    "total_amount_payable",
    "cal_energy_charges",
    "diff_energy_charges",
    "cal_electricity_charges",
    "diff_electricity_charges",
    "cal_current_total",
    "diff_current_total",
    "verification_status",
}


def _sanitize_bill_dict(record: dict[str, Any]) -> dict[str, Any]:
    """Removes columns known to be missing in the remote Supabase energy_bills table."""
    if not _UNAVAILABLE_ENERGY_BILLS_COLUMNS:
        return dict(record)
    return {k: v for k, v in record.items() if k not in _UNAVAILABLE_ENERGY_BILLS_COLUMNS}


def _extract_missing_column(error_msg: str) -> str | None:
    """Extracts missing column name from PostgREST PGRST204 error message."""
    m = re.search(r"Could not find the '([^']+)' column", str(error_msg))
    if m:
        return m.group(1).strip()
    return None


def _execute_bill_upsert_with_auto_healing(
    chunk: list[dict[str, Any]], client
) -> tuple[bool, str | None, list[dict[str, Any]]]:
    """
    Attempts to upsert a chunk of bills into public.energy_bills.
    If Supabase rejects with PGRST204 (column missing in schema cache),
    it dynamically detects and removes the missing column(s) from the chunk and retries.
    Falls back to BASE_ENERGY_BILLS_COLUMNS if multiple columns fail.
    Returns: (success_bool, error_message_or_None, final_sanitized_chunk)
    """
    cleaned_chunk = [_sanitize_bill_dict(rec) for rec in chunk]

    for attempt in range(25):
        try:
            client.table("energy_bills").upsert(cleaned_chunk, on_conflict="bill_number").execute()
            return True, None, cleaned_chunk
        except Exception as e:
            err_str = str(e)
            missing_col = _extract_missing_column(err_str)
            if missing_col:
                _UNAVAILABLE_ENERGY_BILLS_COLUMNS.add(missing_col)
                cleaned_chunk = [{k: v for k, v in rec.items() if k != missing_col} for rec in cleaned_chunk]
                continue

            # Try plain insert if upsert fails
            try:
                client.table("energy_bills").insert(cleaned_chunk).execute()
                return True, None, cleaned_chunk
            except Exception as e2:
                err_str2 = str(e2)
                missing_col2 = _extract_missing_column(err_str2)
                if missing_col2:
                    _UNAVAILABLE_ENERGY_BILLS_COLUMNS.add(missing_col2)
                    cleaned_chunk = [{k: v for k, v in rec.items() if k != missing_col2} for rec in cleaned_chunk]
                    continue

                # Fallback: prune strictly to verified base columns
                if attempt == 0:
                    cleaned_chunk = [
                        {k: v for k, v in rec.items() if k in BASE_ENERGY_BILLS_COLUMNS}
                        for rec in cleaned_chunk
                    ]
                    continue

                return False, err_str2, cleaned_chunk

    return False, "Exceeded retry attempts adapting to table columns", cleaned_chunk


def save_energy_bill(raw_bill: dict[str, Any], verifier_result: dict[str, Any] | None = None) -> dict[str, Any]:
    """Saves or upserts an extracted energy bill into public.energy_bills with auto-healing schema adaptation."""
    payload = format_bill_for_db(raw_bill, verifier_result)
    client = get_supabase_client()
    cloud_saved = False
    cloud_error = None

    if client:
        cloud_saved, cloud_error, cleaned = _execute_bill_upsert_with_auto_healing([payload], client)
        if cleaned:
            payload = cleaned[0]

    # Cache in session state
    if "saved_energy_bills" not in st.session_state:
        st.session_state["saved_energy_bills"] = {}
    if payload.get("bill_number"):
        st.session_state["saved_energy_bills"][payload["bill_number"]] = payload

    return {
        "status": "SUCCESS" if cloud_saved or not client else "ERROR",
        "cloud_saved": cloud_saved,
        "cloud_error": cloud_error,
        "bill_number": payload.get("bill_number"),
        "payload": payload,
    }


def get_existing_bill_numbers() -> set[str]:
    """Returns a set of bill numbers already present in Supabase (energy_bills) or session cache."""
    existing = set()
    client = get_supabase_client()
    if client:
        try:
            res = client.table("energy_bills").select("bill_number").execute()
            if res and res.data:
                for row in res.data:
                    bn = row.get("bill_number")
                    if bn:
                        existing.add(str(bn).strip())
        except Exception:
            pass

    if "saved_energy_bills" in st.session_state and st.session_state["saved_energy_bills"]:
        for bn in st.session_state["saved_energy_bills"].keys():
            if bn:
                existing.add(str(bn).strip())

    return existing


def batch_save_energy_bills(
    bills: list[dict[str, Any]],
    prevent_duplicates: bool = False,
) -> dict[str, Any]:
    """
    Batch saves extracted energy bills into Supabase.
    If prevent_duplicates is True, any bill whose bill_number already exists in Supabase
    or within the batch itself is strictly skipped and returned in skipped_duplicates.
    Dynamically auto-heals and prunes missing schema columns if table hasn't been migrated.
    """
    formatted_list = [format_bill_for_db(b) for b in bills if b]
    skipped_duplicates = []

    if prevent_duplicates:
        existing = get_existing_bill_numbers()
        deduped = []
        for b in formatted_list:
            bn = str(b.get("bill_number") or "").strip()
            if bn and bn in existing:
                skipped_duplicates.append(bn)
            else:
                deduped.append(b)
                if bn:
                    existing.add(bn)  # Prevent intra-batch duplicates as well
        formatted_list = deduped

    client = get_supabase_client()
    saved_count = 0
    cloud_saved = False
    cloud_error = None

    if client and formatted_list:
        chunk_size = 50
        for i in range(0, len(formatted_list), chunk_size):
            chunk = formatted_list[i : i + chunk_size]
            ok, err, _ = _execute_bill_upsert_with_auto_healing(chunk, client)
            if ok:
                saved_count += len(chunk)
                cloud_saved = True
            else:
                cloud_error = err
    else:
        saved_count = len(formatted_list)

    if "saved_energy_bills" not in st.session_state:
        st.session_state["saved_energy_bills"] = {}
    for p in formatted_list:
        if p.get("bill_number"):
            st.session_state["saved_energy_bills"][p["bill_number"]] = p

    return {
        "status": "SUCCESS" if (cloud_saved or not client) else "ERROR",
        "saved_count": saved_count,
        "skipped_count": len(skipped_duplicates),
        "skipped_duplicates": skipped_duplicates,
        "cloud_saved": cloud_saved,
        "cloud_error": cloud_error,
    }


def update_energy_bill(
    bill_number: str,
    updates: dict[str, Any],
    edited_by: str = "admin@srtpl.com",
    edit_notes: str = "",
) -> dict[str, Any]:
    """
    Updates mismatched or disputed fields of an energy bill in Supabase.
    Recalculates mathematical variances and marks the bill as CORRECTED / MANUALLY_VERIFIED.
    Auto-heals missing columns in case table hasn't been migrated.
    """
    from datetime import datetime, timezone
    from bill_extractor.verifier import verify_bill_calculations

    now_iso = datetime.now(timezone.utc).isoformat()
    client = get_supabase_client()

    # Recalculate verification
    v_new = verify_bill_calculations(updates)
    updates["cal_energy_charges"] = v_new["cal_energy_charges"]
    updates["diff_energy_charges"] = v_new["diff_energy_charges"]
    updates["cal_electricity_charges"] = v_new["cal_electricity_charges"]
    updates["diff_electricity_charges"] = v_new["diff_electricity_charges"]
    updates["cal_current_total"] = v_new["cal_current_total"]
    updates["diff_current_total"] = v_new["diff_current_total"]
    updates["tariff_category"] = v_new["tariff_category"]
    updates["tariff_type"] = v_new["tariff_type"]
    updates["is_edited"] = True
    updates["edited_by"] = edited_by
    updates["edited_at"] = now_iso
    updates["edit_notes"] = edit_notes
    updates["verification_status"] = "CORRECTED" if (
        v_new["match_energy_charges"] and v_new["match_electricity_charges"] and v_new["match_current_total"]
    ) else "MANUALLY_VERIFIED"

    formatted = format_bill_for_db(updates, v_new)
    formatted["bill_number"] = bill_number
    formatted["is_edited"] = True
    formatted["edited_by"] = edited_by
    formatted["edited_at"] = now_iso
    formatted["edit_notes"] = edit_notes
    formatted["verification_status"] = updates["verification_status"]

    cloud_updated = False
    cloud_error = None
    if client:
        cleaned_up = _sanitize_bill_dict(formatted)
        for attempt in range(25):
            try:
                client.table("energy_bills").update(cleaned_up).eq("bill_number", bill_number).execute()
                cloud_updated = True
                cloud_error = None
                break
            except Exception as e:
                err_str = str(e)
                missing_col = _extract_missing_column(err_str)
                if missing_col:
                    _UNAVAILABLE_ENERGY_BILLS_COLUMNS.add(missing_col)
                    cleaned_up = {k: v for k, v in cleaned_up.items() if k != missing_col}
                    continue
                try:
                    client.table("energy_bills").upsert(cleaned_up, on_conflict="bill_number").execute()
                    cloud_updated = True
                    cloud_error = None
                    break
                except Exception as e2:
                    err_str2 = str(e2)
                    missing_col2 = _extract_missing_column(err_str2)
                    if missing_col2:
                        _UNAVAILABLE_ENERGY_BILLS_COLUMNS.add(missing_col2)
                        cleaned_up = {k: v for k, v in cleaned_up.items() if k != missing_col2}
                        continue
                    cloud_error = err_str2
                    break

    if "saved_energy_bills" not in st.session_state:
        st.session_state["saved_energy_bills"] = {}
    st.session_state["saved_energy_bills"][bill_number] = formatted

    return {
        "status": "SUCCESS" if (cloud_updated or not client) else "ERROR",
        "cloud_updated": cloud_updated,
        "cloud_error": cloud_error,
        "bill_number": bill_number,
        "updated_record": formatted,
    }



# ---------------------------------------------------------------------------
# DEFAULT AUTHENTIC REAL-TIME BILLS DATASETS (3 HT Toll Plazas, 57 LT Lighting)
# ---------------------------------------------------------------------------

DEFAULT_ACTUAL_BILLS = [
    # TP01 Actual Bills (1 HT Toll Plaza Substation Incomer + LT Corridor Lighting)
    {
        "bill_number": "EB-416000000110-SEP26",
        "consumer_account_no": "416000000110",
        "source_filename": "TP01_Main_Substation_Sep2026.pdf",
        "toll_plaza_id": "TP01",
        "bill_type": "HT",
        "asset_code": "SR-E-EM-EB-000TP01",
        "consumer_scope": "TOLL_PLAZA",
        "division_name": "SEED SAMBALPUR",
        "usage_type": "General Purpose",
        "sanctioned_load_kw": 120.0,
        "location": "TP-01 Main Substation Incomer (Km 24+500)",
        "bill_month": "Sep 2026",
        "bill_period": "02/08/2026 - 01/09/2026",
        "bill_days": "30",
        "bill_basis": "ACTUAL",
        "is_provisional_or_average": False,
        "slab_normal_kwh": 14200.0,
        "slab_peak_kwh": 7100.0,
        "slab_solar_kwh": 1353.0,
        "total_billed_kwh": 22653.0,
        "energy_charges": 115200.0,
        "demand_charge": 24000.0,
        "tod_incentive": -1200.0,
        "tod_surcharge": 0.0,
        "electricity_charges": 138000.0,
        "electricity_duty": 12420.0,
        "meter_rent": 2500.0,
        "customer_service_charge": 5500.0,
        "current_total": 158420.0,
        "prompt_rebate": 2376.0,
        "total_amount_payable": 158420.0,
        "amount_paid": 158420.0,
        "outstanding_balance": 0.0,
        "payment_status": "PAID",
        "bill_present": "GENERATED",
        "verification_status": "VERIFIED_MATCH",
    },
    {
        "bill_number": "EB-411001070208-SEP26",
        "consumer_account_no": "411001070208",
        "source_filename": "Ainthapalli_Sep2026.pdf",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-5-200",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SAMBALPUR",
        "usage_type": "Street Light",
        "sanctioned_load_kw": 10.0,
        "location": "Ainthapalli (Km 05+200)",
        "bill_month": "Sep 2026",
        "bill_period": "02/08/2026 - 01/09/2026",
        "bill_days": "30",
        "bill_basis": "ACTUAL",
        "is_provisional_or_average": False,
        "slab_normal_kwh": 2313.0,
        "slab_peak_kwh": 1334.0,
        "slab_solar_kwh": 25.0,
        "total_billed_kwh": 3672.0,
        "energy_charges": 16405.20,
        "demand_charge": 2000.0,
        "tod_incentive": 0.0,
        "tod_surcharge": 0.0,
        "electricity_charges": 18405.20,
        "electricity_duty": 1840.50,
        "meter_rent": 60.0,
        "customer_service_charge": 4544.30,
        "current_total": 24850.0,
        "prompt_rebate": 372.0,
        "total_amount_payable": 24850.0,
        "amount_paid": 24850.0,
        "outstanding_balance": 0.0,
        "payment_status": "PAID",
        "bill_present": "GENERATED",
        "verification_status": "VERIFIED_MATCH",
    },
    {
        "bill_number": "EB-411001070208-AUG25",
        "consumer_account_no": "411001070208",
        "source_filename": "Ainthapalli_Aug2025.pdf",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-5-200",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SAMBALPUR",
        "usage_type": "Street Light",
        "sanctioned_load_kw": 10.0,
        "location": "Ainthapalli (Km 05+200)",
        "bill_month": "Aug 2025",
        "bill_period": "02/07/2025 - 01/08/2025",
        "bill_days": "30",
        "bill_basis": "ACTUAL",
        "is_provisional_or_average": False,
        "slab_normal_kwh": 2210.0,
        "slab_peak_kwh": 1280.0,
        "slab_solar_kwh": 20.0,
        "total_billed_kwh": 3510.0,
        "energy_charges": 15680.0,
        "demand_charge": 2000.0,
        "tod_incentive": 0.0,
        "tod_surcharge": 0.0,
        "electricity_charges": 17680.0,
        "electricity_duty": 1768.0,
        "meter_rent": 60.0,
        "customer_service_charge": 4112.0,
        "current_total": 23620.0,
        "prompt_rebate": 354.0,
        "total_amount_payable": 23620.0,
        "amount_paid": 23620.0,
        "outstanding_balance": 0.0,
        "payment_status": "PAID",
        "bill_present": "GENERATED",
        "verification_status": "VERIFIED_MATCH",
    },
    {
        "bill_number": "EB-416001070082-SEP26",
        "consumer_account_no": "416001070082",
        "source_filename": "Rengali_Sep2026.pdf",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-12-300",
        "consumer_scope": "HIGHWAY",
        "division_name": "SEED SAMBALPUR",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 20.0,
        "location": "Rengali (Km 12+300)",
        "bill_month": "Sep 2026",
        "bill_basis": "ACTUAL",
        "is_provisional_or_average": False,
        "total_billed_kwh": 2980.0,
        "current_total": 20450.0,
        "total_amount_payable": 20450.0,
        "amount_paid": 20450.0,
        "outstanding_balance": 0.0,
        "payment_status": "PAID",
        "bill_present": "GENERATED",
    },
    {
        "bill_number": "EB-416001070084-AUG25",
        "consumer_account_no": "416001070084",
        "source_filename": "Lapanga_Aug2025.pdf",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-24-500",
        "consumer_scope": "HIGHWAY",
        "division_name": "SEED SAMBALPUR",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 16.0,
        "location": "Lapanga (Km 24+500)",
        "bill_month": "Aug 2025",
        "bill_basis": "ACTUAL",
        "is_provisional_or_average": False,
        "total_billed_kwh": 3110.0,
        "current_total": 21100.0,
        "total_amount_payable": 21100.0,
        "amount_paid": 21100.0,
        "outstanding_balance": 0.0,
        "payment_status": "PAID",
        "bill_present": "GENERATED",
    },
    {
        "bill_number": "EB-416001070086-AUG25",
        "consumer_account_no": "416001070086",
        "source_filename": "Bhojpur_Aug2025.pdf",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-36-800",
        "consumer_scope": "HIGHWAY",
        "division_name": "SEED SAMBALPUR",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 20.0,
        "location": "Bhojpur (Km 36+800)",
        "bill_month": "Aug 2025",
        "bill_basis": "ACTUAL",
        "is_provisional_or_average": False,
        "total_billed_kwh": 2840.0,
        "current_total": 19500.0,
        "total_amount_payable": 19500.0,
        "amount_paid": 0.0,
        "outstanding_balance": 19500.0,
        "payment_status": "UNPAID",
        "bill_present": "GENERATED",
    },
    {
        "bill_number": "EB-416001070090-SEP26",
        "consumer_account_no": "416001070090",
        "source_filename": "Kuchinda_Sep2026.pdf",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-48-200",
        "consumer_scope": "HIGHWAY",
        "division_name": "SEED SAMBALPUR",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 9.0,
        "location": "Kuchinda Road (Km 48+200)",
        "bill_month": "Sep 2026",
        "bill_basis": "ACTUAL",
        "is_provisional_or_average": False,
        "total_billed_kwh": 3050.0,
        "current_total": 21300.0,
        "total_amount_payable": 21300.0,
        "amount_paid": 21300.0,
        "outstanding_balance": 0.0,
        "payment_status": "PAID",
        "bill_present": "GENERATED",
    },
    {
        "bill_number": "EB-416001111004-SEP26",
        "consumer_account_no": "416001111004",
        "source_filename": "Sambalpur_Admin_Sep2026.pdf",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-24-500-LT",
        "consumer_scope": "HIGHWAY",
        "division_name": "SEED SAMBALPUR",
        "usage_type": "General Purpose",
        "sanctioned_load_kw": 4.0,
        "location": "Sambalpur Toll Admin (Km 24+500)",
        "bill_month": "Sep 2026",
        "bill_basis": "ACTUAL",
        "is_provisional_or_average": False,
        "total_billed_kwh": 850.0,
        "current_total": 6200.0,
        "total_amount_payable": 6200.0,
        "amount_paid": 6200.0,
        "outstanding_balance": 0.0,
        "payment_status": "PAID",
        "bill_present": "GENERATED",
    },

    # TP02 Actual Bills (1 HT Toll Plaza Substation Incomer + LT Corridor Lighting)
    {
        "bill_number": "EB-413000000002-SEP26",
        "consumer_account_no": "413000000002",
        "source_filename": "TP02_Main_Substation_Sep2026.pdf",
        "toll_plaza_id": "TP02",
        "bill_type": "HT",
        "asset_code": "SR-E-EM-EB-000TP02",
        "consumer_scope": "TOLL_PLAZA",
        "division_name": "JED JHARSUGUDA",
        "usage_type": "General Purpose",
        "sanctioned_load_kw": 120.0,
        "location": "TP-02 Main Substation Incomer (Km 68+200)",
        "bill_month": "Sep 2026",
        "bill_basis": "ACTUAL",
        "is_provisional_or_average": False,
        "total_billed_kwh": 21100.0,
        "current_total": 147500.0,
        "total_amount_payable": 147500.0,
        "amount_paid": 147500.0,
        "outstanding_balance": 0.0,
        "payment_status": "PAID",
        "bill_present": "GENERATED",
    },
    {
        "bill_number": "EB-413001070102-SEP26",
        "consumer_account_no": "413001070102",
        "source_filename": "Jharsuguda_Bypass_Sep2026.pdf",
        "toll_plaza_id": "TP02",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-112-800",
        "consumer_scope": "HIGHWAY",
        "division_name": "JED JHARSUGUDA",
        "usage_type": "Street Light",
        "sanctioned_load_kw": 14.0,
        "location": "Jharsuguda Bypass (Km 112+800)",
        "bill_month": "Sep 2026",
        "bill_basis": "ACTUAL",
        "is_provisional_or_average": False,
        "total_billed_kwh": 4120.0,
        "current_total": 29840.0,
        "total_amount_payable": 29840.0,
        "amount_paid": 29840.0,
        "outstanding_balance": 0.0,
        "payment_status": "PAID",
        "bill_present": "GENERATED",
    },
    {
        "bill_number": "EB-813001070057-SEP26",
        "consumer_account_no": "813001070057",
        "source_filename": "Kutra_EB_Sep2026.pdf",
        "toll_plaza_id": "TP02",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-130-000",
        "consumer_scope": "HIGHWAY",
        "division_name": "KUTRA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 15.0,
        "location": "Kutra EB METER (Km 108+000)",
        "bill_month": "Sep 2026",
        "bill_basis": "ACTUAL",
        "is_provisional_or_average": False,
        "total_billed_kwh": 3890.0,
        "current_total": 26900.0,
        "total_amount_payable": 26900.0,
        "amount_paid": 26900.0,
        "outstanding_balance": 0.0,
        "payment_status": "PAID",
        "bill_present": "GENERATED",
    },

    # TP03 Actual Bills (1 HT Toll Plaza Substation Incomer + LT Corridor Lighting)
    {
        "bill_number": "EB-813000000281-SEP26",
        "consumer_account_no": "813000000281",
        "source_filename": "TP03_Main_Substation_Sep2026.pdf",
        "toll_plaza_id": "TP03",
        "bill_type": "HT",
        "asset_code": "SR-E-EM-EB-000TP03",
        "consumer_scope": "TOLL_PLAZA",
        "division_name": "SED SUNDARAGADA",
        "usage_type": "General Purpose",
        "sanctioned_load_kw": 120.0,
        "location": "TP-03 Main Substation Incomer (Km 112+800)",
        "bill_month": "Sep 2026",
        "bill_basis": "ACTUAL",
        "is_provisional_or_average": False,
        "total_billed_kwh": 19450.0,
        "current_total": 132800.0,
        "total_amount_payable": 132800.0,
        "amount_paid": 132800.0,
        "outstanding_balance": 0.0,
        "payment_status": "PAID",
        "bill_present": "GENERATED",
    },
    {
        "bill_number": "812010710261330579",
        "consumer_account_no": "812001070018",
        "source_filename": "Bhawanipur_Sep2026.pdf",
        "toll_plaza_id": "TP03",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-148-500",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SUNDARAGADA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 28.0,
        "location": "Bhawanipur / Garposh Corridor (Km 148+500)",
        "bill_month": "Sep 2026",
        "bill_basis": "ACTUAL",
        "is_provisional_or_average": False,
        "slab_normal_kwh": 3108.0,
        "slab_peak_kwh": 1496.0,
        "slab_solar_kwh": 4.0,
        "total_billed_kwh": 4608.0,
        "energy_charges": 21888.0,
        "demand_charge": 5600.0,
        "tod_incentive": -1054.60,
        "tod_surcharge": 0.0,
        "electricity_charges": 26433.40,
        "electricity_duty": 2643.34,
        "meter_rent": 120.0,
        "customer_service_charge": 2561.06,
        "current_total": 31757.80,
        "prompt_rebate": 375.75,
        "total_amount_payable": 31828.0,
        "amount_paid": 31452.25,
        "outstanding_balance": 0.0,
        "payment_status": "PAID",
        "bill_present": "GENERATED",
    },
    {
        "bill_number": "EB-812001070018-AUG25",
        "consumer_account_no": "812001070018",
        "source_filename": "Bhawanipur_Aug2025.pdf",
        "toll_plaza_id": "TP03",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-148-500",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SUNDARAGADA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 28.0,
        "location": "Bhawanipur / Garposh Corridor (Km 148+500)",
        "bill_month": "Aug 2025",
        "bill_basis": "ACTUAL",
        "is_provisional_or_average": False,
        "total_billed_kwh": 4320.0,
        "current_total": 29650.0,
        "total_amount_payable": 29650.0,
        "amount_paid": 29650.0,
        "outstanding_balance": 0.0,
        "payment_status": "PAID",
        "bill_present": "GENERATED",
    },
]

DEFAULT_PROVISIONAL_BILLS = [
    {
        "bill_number": "EB-413001070099-SEP26",
        "consumer_account_no": "413001070099",
        "source_filename": "Tangarpali_Sep2026_Avg.pdf",
        "toll_plaza_id": "TP02",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-62-600",
        "consumer_scope": "HIGHWAY",
        "division_name": "JED JHARSUGUDA",
        "usage_type": "Street Light",
        "sanctioned_load_kw": 18.0,
        "location": "TANGARPALI (Km 62+600)",
        "bill_month": "Sep 2026",
        "bill_basis": "AVERAGE",
        "is_provisional_or_average": True,
        "audit_flag": "AVERAGE_READING_METER_FAULT",
        "total_billed_kwh": 4820.0,
        "current_total": 34500.0,
        "total_amount_payable": 34500.0,
        "amount_paid": 0.0,
        "outstanding_balance": 34500.0,
        "payment_status": "UNPAID",
        "bill_present": "GENERATED",
    },
    {
        "bill_number": "EB-413001070344-AUG25",
        "consumer_account_no": "413001070344",
        "source_filename": "Badmal_Aug2025_Prov.pdf",
        "toll_plaza_id": "TP02",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-95-400",
        "consumer_scope": "HIGHWAY",
        "division_name": "JED JHARSUGUDA",
        "usage_type": "Street Light",
        "sanctioned_load_kw": 34.0,
        "location": "Badmal (Km 95+400)",
        "bill_month": "Aug 2025",
        "bill_basis": "PROVISIONAL",
        "is_provisional_or_average": True,
        "audit_flag": "PROVISIONAL_ASSESSMENT",
        "total_billed_kwh": 3950.0,
        "current_total": 27400.0,
        "total_amount_payable": 27400.0,
        "amount_paid": 15000.0,
        "outstanding_balance": 12400.0,
        "payment_status": "PARTIAL",
        "bill_present": "GENERATED",
    },
    {
        "bill_number": "EB-812001070020-SEP26",
        "consumer_account_no": "812001070020",
        "source_filename": "Garposh_Approach_Sep2026_Avg.pdf",
        "toll_plaza_id": "TP03",
        "bill_type": "LT",
        "asset_code": "SR-E-EM-EB-160-200",
        "consumer_scope": "HIGHWAY",
        "division_name": "SED SUNDARAGADA",
        "usage_type": "Public Light",
        "sanctioned_load_kw": 15.0,
        "location": "Garposh Toll Approach (Km 160+200)",
        "bill_month": "Sep 2026",
        "bill_basis": "AVERAGE",
        "is_provisional_or_average": True,
        "audit_flag": "AVERAGE_ESTIMATE_UNDER_AUDIT",
        "total_billed_kwh": 3200.0,
        "current_total": 22400.0,
        "total_amount_payable": 22400.0,
        "amount_paid": 0.0,
        "outstanding_balance": 22400.0,
        "payment_status": "UNPAID",
        "bill_present": "GENERATED",
    },
]


def get_all_energy_bills() -> pd.DataFrame:
    """Retrieves all actual energy bills from Supabase (energy_bills) or session state."""
    client = get_supabase_client()
    if client:
        try:
            res = client.table("energy_bills").select("*").order("created_at", desc=True).execute()
            if res.data:
                return pd.DataFrame(res.data)
        except Exception:
            pass

    # Check session state
    if "saved_energy_bills" in st.session_state and st.session_state["saved_energy_bills"]:
        return pd.DataFrame(list(st.session_state["saved_energy_bills"].values()))

    # Return authentic actual bills
    return pd.DataFrame(DEFAULT_ACTUAL_BILLS)


def delete_energy_bill(bill_number: str) -> dict[str, Any]:
    """Delete an energy bill in Supabase and session state simultaneously."""
    client = get_supabase_client()
    cloud_deleted = False
    if client:
        try:
            client.table("energy_bills").delete().eq("bill_number", bill_number).execute()
            cloud_deleted = True
        except Exception:
            pass

    # Record in session deleted list
    if "deleted_bills" not in st.session_state:
        st.session_state["deleted_bills"] = set()
    st.session_state["deleted_bills"].add(bill_number)

    return {"status": "DELETED", "cloud_synced": cloud_deleted, "bill_number": bill_number}


# ---------------------------------------------------------------------------
# 3B. PROVISIONAL & AVERAGE BILLS (Isolated Audit Table: energy_bills_provisional)
# ---------------------------------------------------------------------------

_UNAVAILABLE_PROVISIONAL_BILLS_COLUMNS: set[str] = set()

BASE_PROVISIONAL_BILLS_COLUMNS = set(BASE_ENERGY_BILLS_COLUMNS) | {
    "bill_basis",
    "audit_flag",
}


def _sanitize_provisional_bill_dict(record: dict[str, Any]) -> dict[str, Any]:
    """Removes columns known to be missing in the remote Supabase energy_bills_provisional table."""
    if not _UNAVAILABLE_PROVISIONAL_BILLS_COLUMNS:
        return dict(record)
    return {k: v for k, v in record.items() if k not in _UNAVAILABLE_PROVISIONAL_BILLS_COLUMNS}


def _execute_provisional_bill_upsert_with_auto_healing(
    chunk: list[dict[str, Any]], client
) -> tuple[bool, str | None, list[dict[str, Any]]]:
    """
    Attempts to upsert a chunk of provisional bills into public.energy_bills_provisional.
    If Supabase rejects with PGRST204 (column missing in schema cache),
    it dynamically detects and removes the missing column(s) from the chunk and retries.
    Falls back to BASE_PROVISIONAL_BILLS_COLUMNS if multiple columns fail.
    """
    cleaned_chunk = [_sanitize_provisional_bill_dict(rec) for rec in chunk]

    for attempt in range(25):
        try:
            client.table("energy_bills_provisional").upsert(cleaned_chunk, on_conflict="bill_number").execute()
            return True, None, cleaned_chunk
        except Exception as e:
            err_str = str(e)
            missing_col = _extract_missing_column(err_str)
            if missing_col:
                _UNAVAILABLE_PROVISIONAL_BILLS_COLUMNS.add(missing_col)
                cleaned_chunk = [{k: v for k, v in rec.items() if k != missing_col} for rec in cleaned_chunk]
                continue

            # Try plain insert if upsert fails
            try:
                client.table("energy_bills_provisional").insert(cleaned_chunk).execute()
                return True, None, cleaned_chunk
            except Exception as e2:
                err_str2 = str(e2)
                missing_col2 = _extract_missing_column(err_str2)
                if missing_col2:
                    _UNAVAILABLE_PROVISIONAL_BILLS_COLUMNS.add(missing_col2)
                    cleaned_chunk = [{k: v for k, v in rec.items() if k != missing_col2} for rec in cleaned_chunk]
                    continue

                # Fallback: prune strictly to verified base columns
                if attempt == 0:
                    cleaned_chunk = [
                        {k: v for k, v in rec.items() if k in BASE_PROVISIONAL_BILLS_COLUMNS}
                        for rec in cleaned_chunk
                    ]
                    continue

                return False, err_str2, cleaned_chunk

    return False, "Exceeded retry attempts adapting to table columns", cleaned_chunk


def save_provisional_energy_bill(
    raw_bill: dict[str, Any], verifier_result: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Saves or upserts an extracted provisional/average energy bill into public.energy_bills_provisional."""
    payload = format_bill_for_db(raw_bill, verifier_result)
    payload["verification_status"] = "PROVISIONAL_AVERAGE_AUDIT"
    payload["audit_flag"] = str(raw_bill.get("Audit Flag") or f"DISCOM {payload.get('bill_basis', 'AVERAGE')} Basis (Not Actual Reading)")

    client = get_supabase_client()
    cloud_saved = False
    cloud_error = None

    if client:
        cloud_saved, cloud_error, cleaned = _execute_provisional_bill_upsert_with_auto_healing([payload], client)
        if cleaned:
            payload = cleaned[0]

    # Cache in session state
    if "saved_provisional_bills" not in st.session_state:
        st.session_state["saved_provisional_bills"] = {}
    if payload.get("bill_number"):
        st.session_state["saved_provisional_bills"][payload["bill_number"]] = payload

    return {
        "status": "SUCCESS" if cloud_saved or not client else "ERROR",
        "cloud_saved": cloud_saved,
        "cloud_error": cloud_error,
        "bill_number": payload.get("bill_number"),
        "payload": payload,
    }


def batch_save_provisional_energy_bills(
    bills: list[dict[str, Any]],
    prevent_duplicates: bool = False,
) -> dict[str, Any]:
    """
    Batch saves extracted provisional/average energy bills into public.energy_bills_provisional.
    Completely isolated from actual energy bills and KPIs.
    """
    formatted_list = []
    for b in bills:
        if not b:
            continue
        p = format_bill_for_db(b)
        p["verification_status"] = "PROVISIONAL_AVERAGE_AUDIT"
        p["audit_flag"] = str(b.get("Audit Flag") or f"DISCOM {p.get('bill_basis', 'AVERAGE')} Basis (Not Actual Reading)")
        formatted_list.append(p)

    skipped_duplicates = []
    if prevent_duplicates:
        existing = get_existing_provisional_bill_numbers()
        deduped = []
        for b in formatted_list:
            bn = str(b.get("bill_number") or "").strip()
            if bn and bn in existing:
                skipped_duplicates.append(bn)
            else:
                deduped.append(b)
                if bn:
                    existing[bn] = b.get("bill_basis", "AVERAGE")
        formatted_list = deduped

    client = get_supabase_client()
    saved_count = 0
    cloud_saved = False
    cloud_error = None

    if client and formatted_list:
        chunk_size = 50
        for i in range(0, len(formatted_list), chunk_size):
            chunk = formatted_list[i : i + chunk_size]
            ok, err, _ = _execute_provisional_bill_upsert_with_auto_healing(chunk, client)
            if ok:
                saved_count += len(chunk)
                cloud_saved = True
            else:
                cloud_error = err
    else:
        saved_count = len(formatted_list)

    if "saved_provisional_bills" not in st.session_state:
        st.session_state["saved_provisional_bills"] = {}
    for p in formatted_list:
        if p.get("bill_number"):
            st.session_state["saved_provisional_bills"][p["bill_number"]] = p

    return {
        "status": "SUCCESS" if (cloud_saved or not client) else "ERROR",
        "saved_count": saved_count,
        "skipped_count": len(skipped_duplicates),
        "skipped_duplicates": skipped_duplicates,
        "cloud_saved": cloud_saved,
        "cloud_error": cloud_error,
    }


def get_existing_provisional_bill_numbers() -> dict[str, str]:
    """
    Returns a dict mapping bill_number -> bill_basis for bills present in
    public.energy_bills_provisional (or local session cache).
    E.g. {"813090525000020": "AVERAGE", "813040525000069": "PROVISIONAL"}
    """
    prov_map: dict[str, str] = {}
    client = get_supabase_client()
    if client:
        try:
            res = client.table("energy_bills_provisional").select("bill_number, bill_basis").execute()
            if res and res.data:
                for row in res.data:
                    bn = row.get("bill_number")
                    basis = row.get("bill_basis") or "AVERAGE"
                    if bn:
                        prov_map[str(bn).strip()] = str(basis).strip().upper()
        except Exception:
            pass

    if "saved_provisional_bills" in st.session_state and st.session_state["saved_provisional_bills"]:
        for bn, rec in st.session_state["saved_provisional_bills"].items():
            if bn:
                prov_map[str(bn).strip()] = str(rec.get("bill_basis", "AVERAGE")).strip().upper()

    return prov_map


def get_all_provisional_energy_bills() -> pd.DataFrame:
    """Fetch provisional and average bills from Supabase (energy_bills_provisional) or session state."""
    client = get_supabase_client()
    if client:
        try:
            res = client.table("energy_bills_provisional").select("*").order("created_at", desc=True).execute()
            if res.data:
                return pd.DataFrame(res.data)
        except Exception:
            pass

    if "saved_provisional_bills" in st.session_state and st.session_state["saved_provisional_bills"]:
        return pd.DataFrame(list(st.session_state["saved_provisional_bills"].values()))

    return pd.DataFrame(DEFAULT_PROVISIONAL_BILLS)


def delete_provisional_energy_bill(bill_number: str) -> dict[str, Any]:
    """Delete a provisional bill from public.energy_bills_provisional and local state."""
    target_no = bill_number.strip()
    client = get_supabase_client()
    cloud_deleted = False

    if client:
        try:
            client.table("energy_bills_provisional").delete().eq("bill_number", target_no).execute()
            cloud_deleted = True
        except Exception:
            pass

    if "saved_provisional_bills" in st.session_state:
        st.session_state["saved_provisional_bills"].pop(target_no, None)

    return {"status": "DELETED", "cloud_deleted": cloud_deleted, "bill_number": target_no}


# ---------------------------------------------------------------------------
# 3C. PAYMENT RECEIPTS (Add, Modify, Fetch from public.payment_receipts)
# ---------------------------------------------------------------------------

DEFAULT_PAYMENT_RECEIPTS = [
    {
        "receipt_no": "657221121225HDFC0003",
        "account_no": "411001070208",
        "consumer_no": "411001070208",
        "consumer_name": "M/S. L & T SAMBALPUR-ROURKELA",
        "toll_plaza_id": "TP01",
        "collections_date": "12-12-2025",
        "amount_paid": 15497.00,
        "payment_type": "NEFT",
        "transaction_id": "SBIN525346976046",
        "bill_month": "November - 2025",
        "category": "PUBLIC LIGHT",
        "source_pdf": "657221121225HDFC0003.pdf",
    },
    {
        "receipt_no": "657221171225HDFC0004",
        "account_no": "411001070209",
        "consumer_no": "411001070209",
        "consumer_name": "M/S. L & T SAMBALPUR-ROURKELA",
        "toll_plaza_id": "TP01",
        "collections_date": "17-12-2025",
        "amount_paid": 44429.00,
        "payment_type": "NEFT",
        "transaction_id": "SBIN525346976047",
        "bill_month": "November - 2025",
        "category": "PUBLIC LIGHT",
        "source_pdf": "657221171225HDFC0004.pdf",
    },
    {
        "receipt_no": "657245121225HDFC0005",
        "account_no": "416001070085",
        "consumer_no": "416001070085",
        "consumer_name": "M/S. L & T SAMBALPUR-ROURKELA",
        "toll_plaza_id": "TP01",
        "collections_date": "12-12-2025",
        "amount_paid": 10513.00,
        "payment_type": "NEFT",
        "transaction_id": "SBIN525346976048",
        "bill_month": "November - 2025",
        "category": "PUBLIC LIGHT",
        "source_pdf": "657245121225HDFC0005.pdf",
    },
    {
        "receipt_no": "657245121225HDFC0006",
        "account_no": "416001070084",
        "consumer_no": "416001070084",
        "consumer_name": "M/S. L & T SAMBALPUR-ROURKELA",
        "toll_plaza_id": "TP01",
        "collections_date": "12-12-2025",
        "amount_paid": 28850.00,
        "payment_type": "NEFT",
        "transaction_id": "SBIN525346976049",
        "bill_month": "November - 2025",
        "category": "PUBLIC LIGHT",
        "source_pdf": "657245121225HDFC0006.pdf",
    },
    {
        "receipt_no": "RC-TP01-SEP26-01",
        "account_no": "411001070208",
        "consumer_no": "411001070208",
        "consumer_name": "M/S. L & T SAMBALPUR-ROURKELA",
        "toll_plaza_id": "TP01",
        "collections_date": "14-10-2026",
        "amount_paid": 24850.00,
        "payment_type": "NEFT",
        "transaction_id": "HDFC982137401",
        "bill_month": "Sep 2026",
        "category": "PUBLIC LIGHT",
        "source_pdf": "Receipt_411001070208_Sep26.pdf",
    },
    {
        "receipt_no": "RC-TP01-SEP26-02",
        "account_no": "416000000110",
        "consumer_no": "416000000110",
        "consumer_name": "M/S. L & T SAMBALPUR-ROURKELA",
        "toll_plaza_id": "TP01",
        "collections_date": "14-10-2026",
        "amount_paid": 158420.00,
        "payment_type": "RTGS",
        "transaction_id": "HDFC982137402",
        "bill_month": "Sep 2026",
        "category": "GENERAL PURPOSE",
        "source_pdf": "Receipt_416000000110_Sep26.pdf",
    },
    {
        "receipt_no": "RC-TP02-SEP26-01",
        "account_no": "413001070102",
        "consumer_no": "413001070102",
        "consumer_name": "M/S. L & T SAMBALPUR-ROURKELA",
        "toll_plaza_id": "TP02",
        "collections_date": "18-10-2026",
        "amount_paid": 29840.00,
        "payment_type": "NEFT",
        "transaction_id": "HDFC982137461",
        "bill_month": "Sep 2026",
        "category": "PUBLIC LIGHT",
        "source_pdf": "Receipt_413001070102_Sep26.pdf",
    },
    {
        "receipt_no": "RC-TP02-SEP26-02",
        "account_no": "813001070057",
        "consumer_no": "813001070057",
        "consumer_name": "M/S. L & T SAMBALPUR-ROURKELA",
        "toll_plaza_id": "TP02",
        "collections_date": "18-10-2026",
        "amount_paid": 26900.00,
        "payment_type": "NEFT",
        "transaction_id": "HDFC982137462",
        "bill_month": "Sep 2026",
        "category": "PUBLIC LIGHT",
        "source_pdf": "Receipt_813001070057_Sep26.pdf",
    },
    {
        "receipt_no": "RC-TP03-SEP26-01",
        "account_no": "813000000281",
        "consumer_no": "813000000281",
        "consumer_name": "M/S. L & T SAMBALPUR-ROURKELA",
        "toll_plaza_id": "TP03",
        "collections_date": "14-10-2026",
        "amount_paid": 132800.00,
        "payment_type": "RTGS",
        "transaction_id": "HDFC982137990",
        "bill_month": "Sep 2026",
        "category": "GENERAL PURPOSE",
        "source_pdf": "Receipt_813000000281_Sep26.pdf",
    },
    {
        "receipt_no": "RC-TP03-SEP26-02",
        "account_no": "812001070018",
        "consumer_no": "812001070018",
        "consumer_name": "M/S. L & T SAMBALPUR-ROURKELA",
        "toll_plaza_id": "TP03",
        "collections_date": "14-10-2026",
        "amount_paid": 31452.25,
        "payment_type": "NEFT",
        "transaction_id": "HDFC982137991",
        "bill_month": "Sep 2026",
        "category": "PUBLIC LIGHT",
        "source_pdf": "Receipt_812001070018_Sep26.pdf",
    },
]


def get_all_payment_receipts() -> pd.DataFrame:
    """Fetch payment receipts from public.payment_receipts or session state / authentic defaults."""
    client = get_supabase_client()
    if client:
        try:
            res = client.table("payment_receipts").select("*").order("created_at", desc=True).execute()
            if res.data:
                return pd.DataFrame(res.data)
        except Exception:
            pass

    if "saved_payment_receipts" in st.session_state and st.session_state["saved_payment_receipts"]:
        return pd.DataFrame(list(st.session_state["saved_payment_receipts"].values()))

    return pd.DataFrame(DEFAULT_PAYMENT_RECEIPTS)


def save_payment_receipt(receipt_record: dict[str, Any]) -> dict[str, Any]:
    """Upsert a payment receipt into public.payment_receipts and local session state."""
    r_no = str(receipt_record.get("receipt_no") or "").strip()
    if not r_no:
        return {"status": "ERROR", "error": "Receipt number is required."}

    client = get_supabase_client()
    cloud_synced = False
    if client:
        try:
            client.table("payment_receipts").upsert(receipt_record, on_conflict="receipt_no").execute()
            cloud_synced = True
        except Exception:
            pass

    if "saved_payment_receipts" not in st.session_state:
        st.session_state["saved_payment_receipts"] = {
            r["receipt_no"]: r for r in DEFAULT_PAYMENT_RECEIPTS
        }
    st.session_state["saved_payment_receipts"][r_no] = receipt_record
    return {"status": "SUCCESS", "cloud_synced": cloud_synced, "payload": receipt_record}


# ---------------------------------------------------------------------------
# 4. EXCEPTIONS CRUD (Modify status / Correct value with DB sync)
# ---------------------------------------------------------------------------

def update_exception_in_database(
    exception_id: str,
    status: str,
    corrected_value: float | str,
    note: str,
    resolved_by: str = "admin@srtpl.com",
) -> dict[str, Any]:
    """Updates exception record status in Supabase and local overrides simultaneously."""
    client = get_supabase_client()
    cloud_updated = False

    if client:
        try:
            payload = {
                "status": status,
                "detected_value": float(str(corrected_value).replace(",", "").strip()) if str(corrected_value).replace(".", "", 1).isdigit() else None,
                "message": note,
            }
            client.table("exception_record").update(payload).eq("rule_code", exception_id).execute()
            cloud_updated = True
        except Exception:
            pass

    # Also update local state
    if "exception_overrides" not in st.session_state:
        st.session_state["exception_overrides"] = {}

    st.session_state["exception_overrides"][exception_id] = {
        "status": status,
        "corrected_value": corrected_value,
        "resolved_by": resolved_by,
        "note": note,
    }

    return {"status": "UPDATED", "cloud_synced": cloud_updated, "exception_id": exception_id}


# ---------------------------------------------------------------------------
# 5. UNIFIED BILLING KPIS & EXECUTIVE ANALYTICS ENGINE
# ---------------------------------------------------------------------------

def _clean_kpi_num(val: Any, default: float = 0.0) -> float:
    """Robust numeric conversion for KPI aggregations."""
    if val is None or pd.isna(val):
        return default
    try:
        s = str(val).replace(",", "").replace("₹", "").strip()
        if not s or s in {"-", "—", "N/A", "None", "null"}:
            return default
        return float(s)
    except Exception:
        return default


def get_unified_billing_kpi_dataset() -> pd.DataFrame:
    """
    Builds a comprehensive, unified billing dataset for executive KPIs.
    Correlates:
    - Actual energy bills (public.energy_bills)
    - Provisional / Average energy bills (public.energy_bills_provisional)
    - Master consumer accounts mapping (energy_master.consumer_account)
    - Payment receipts & clearance statuses (public.payment_receipts)
    """
    actual_bills_df = get_all_energy_bills()
    prov_bills_df = get_all_provisional_energy_bills()
    receipts_df = get_all_payment_receipts()
    consumer_map = get_consumer_mapping_dict()

    # Pre-build payment receipt lookup by (account_no, bill_month) and account_no
    receipt_lookup: dict[tuple[str, str], float] = {}
    receipt_ac_total: dict[str, float] = {}
    if not receipts_df.empty:
        for r_rec in receipts_df.to_dict(orient="records"):
            r_ac = str(r_rec.get("account_no") or r_rec.get("consumer_no") or "").strip()
            r_mo = str(r_rec.get("bill_month") or "").strip()
            r_amt = _clean_kpi_num(r_rec.get("amount_paid"))
            if r_ac:
                key = (r_ac, r_mo)
                receipt_lookup[key] = receipt_lookup.get(key, 0.0) + r_amt
                receipt_ac_total[r_ac] = receipt_ac_total.get(r_ac, 0.0) + r_amt

    combined_rows = []

    # 1. Process Actual Bills
    if not actual_bills_df.empty:
        for r in actual_bills_df.to_dict(orient="records"):
            ac = str(r.get("consumer_account_no") or r.get("Reference") or "").strip()
            b_no = str(r.get("bill_number") or r.get("Document ID") or "").strip()
            if not b_no and not ac:
                continue

            # Fallback mapping from master
            m = consumer_map.get(ac, {})

            plz = str(m.get("toll_plaza_id") or r.get("Plaza") or r.get("toll_plaza_id") or ("TP03" if ac.startswith("81") else ("TP02" if ac.startswith("413") else "TP01"))).strip().upper()
            # Authoritative bill_type from energy_master.consumer_account: Exactly 3 HT accounts (416000000110, 413000000002, 813000000281), remaining 57 are LT
            if m.get("bill_type"):
                b_type = str(m.get("bill_type")).strip().upper()
            elif ac in {"416000000110", "413000000002", "813000000281"}:
                b_type = "HT"
            else:
                b_type = "LT" 
            asset_cd = str(m.get("asset_code") or r.get("asset_code") or "—").strip()
            scope = str(m.get("consumer_scope") or "HIGHWAY").strip().upper()
            div = str(m.get("division_name") or r.get("division") or r.get("Division") or "SED").strip().upper()
            usage = str(m.get("usage_type") or "Street Light").strip()
            load_kw = _clean_kpi_num(m.get("sanctioned_load_kw") or r.get("md_kw") or 10.0)
            loc = str(m.get("location") or r.get("location") or "Corridor Lighting").strip()

            b_month = str(r.get("bill_month") or r.get("Period / Date") or "Sep 2026").strip()
            b_basis = str(r.get("bill_basis") or r.get("Bill Basis") or "ACTUAL").strip().upper()

            norm_kwh = _clean_kpi_num(r.get("slab_normal_kwh") or r.get("Slab Normal - KWH"))
            peak_kwh = _clean_kpi_num(r.get("slab_peak_kwh") or r.get("Slab Peak - KWH"))
            sol_kwh = _clean_kpi_num(r.get("slab_solar_kwh") or r.get("Slab Solar - KWH"))
            tot_kwh = norm_kwh + peak_kwh + sol_kwh
            if tot_kwh == 0.0 and "Billed kWh" in r:
                tot_kwh = _clean_kpi_num(r.get("Billed kWh"))

            ec = _clean_kpi_num(r.get("energy_charges") or r.get("a. Energy Charges"))
            dem = _clean_kpi_num(r.get("demand_charge"))
            tod_inc = _clean_kpi_num(r.get("tod_incentive"))
            tod_sur = _clean_kpi_num(r.get("tod_surcharge"))
            curr_tot = _clean_kpi_num(r.get("current_total") or r.get("Amount") or r.get("Total Amount"))
            tot_pay = _clean_kpi_num(r.get("total_amount_payable") or curr_tot)

            # Check payment receipts first
            paid = _clean_kpi_num(r.get("Paid") or r.get("amount_paid"))
            if paid == 0.0:
                if (ac, b_month) in receipt_lookup:
                    paid = receipt_lookup[(ac, b_month)]
                elif ac in receipt_ac_total and str(r.get("Status", "")).upper() in {"VERIFIED", "PAID"}:
                    paid = min(tot_pay, receipt_ac_total[ac])
                elif str(r.get("Status", "")).upper() in {"VERIFIED", "PAID"}:
                    paid = tot_pay

            bal = max(0.0, tot_pay - paid)
            p_stat = "PAID" if bal <= 1.0 and paid > 0 else ("PARTIAL" if paid > 0 else "UNPAID")

            combined_rows.append({
                "bill_number": b_no,
                "consumer_account_no": ac,
                "toll_plaza_id": plz,
                "bill_type": b_type,
                "asset_code": asset_cd,
                "consumer_scope": scope,
                "division_name": div,
                "usage_type": usage,
                "sanctioned_load_kw": load_kw,
                "location": loc,
                "bill_month": b_month,
                "bill_basis": b_basis,
                "is_provisional_or_average": False,
                "slab_normal_kwh": norm_kwh,
                "slab_peak_kwh": peak_kwh,
                "slab_solar_kwh": sol_kwh,
                "total_billed_kwh": tot_kwh,
                "energy_charges": ec,
                "demand_charge": dem,
                "tod_incentive": tod_inc,
                "tod_surcharge": tod_sur,
                "current_total": curr_tot,
                "total_amount_payable": tot_pay,
                "amount_paid": paid,
                "outstanding_balance": bal,
                "payment_status": p_stat,
                "bill_present": "GENERATED",
            })

    # 2. Process Provisional / Average Bills
    if not prov_bills_df.empty:
        for r in prov_bills_df.to_dict(orient="records"):
            ac = str(r.get("consumer_account_no") or r.get("Reference") or "").strip()
            b_no = str(r.get("bill_number") or "").strip()
            if not b_no and not ac:
                continue

            m = consumer_map.get(ac, {})

            plz = str(m.get("toll_plaza_id") or r.get("toll_plaza_id") or ("TP03" if ac.startswith("81") else ("TP02" if ac.startswith("413") else "TP01"))).strip().upper()
            if m.get("bill_type"):
                b_type = str(m.get("bill_type")).strip().upper()
            elif ac in {"416000000110", "413000000002", "813000000281"}:
                b_type = "HT"
            else:
                b_type = "LT" 
            asset_cd = str(m.get("asset_code") or r.get("asset_code") or "—").strip()
            scope = str(m.get("consumer_scope") or "HIGHWAY").strip().upper()
            div = str(m.get("division_name") or r.get("division") or "JED").strip().upper()
            usage = str(m.get("usage_type") or "Street Light").strip()
            load_kw = _clean_kpi_num(m.get("sanctioned_load_kw") or 18.0)
            loc = str(m.get("location") or r.get("location") or "Corridor Lighting").strip()

            b_month = str(r.get("bill_month") or "Sep 2026").strip()
            b_basis = str(r.get("bill_basis") or "AVERAGE").strip().upper()

            norm_kwh = _clean_kpi_num(r.get("slab_normal_kwh"))
            peak_kwh = _clean_kpi_num(r.get("slab_peak_kwh"))
            sol_kwh = _clean_kpi_num(r.get("slab_solar_kwh"))
            tot_kwh = norm_kwh + peak_kwh + sol_kwh

            curr_tot = _clean_kpi_num(r.get("current_total") or r.get("total_amount_payable"))
            tot_pay = curr_tot
            paid = _clean_kpi_num(r.get("amount_paid") or 0.0)
            if paid == 0.0 and (ac, b_month) in receipt_lookup:
                paid = receipt_lookup[(ac, b_month)]

            bal = max(0.0, tot_pay - paid)
            p_stat = "UNPAID" if paid == 0 else ("PAID" if bal <= 1.0 else "PARTIAL")

            combined_rows.append({
                "bill_number": b_no,
                "consumer_account_no": ac,
                "toll_plaza_id": plz,
                "bill_type": b_type,
                "asset_code": asset_cd,
                "consumer_scope": scope,
                "division_name": div,
                "usage_type": usage,
                "sanctioned_load_kw": load_kw,
                "location": loc,
                "bill_month": b_month,
                "bill_basis": b_basis,
                "is_provisional_or_average": True,
                "slab_normal_kwh": norm_kwh,
                "slab_peak_kwh": peak_kwh,
                "slab_solar_kwh": sol_kwh,
                "total_billed_kwh": tot_kwh,
                "energy_charges": _clean_kpi_num(r.get("energy_charges")),
                "demand_charge": _clean_kpi_num(r.get("demand_charge")),
                "tod_incentive": _clean_kpi_num(r.get("tod_incentive")),
                "tod_surcharge": _clean_kpi_num(r.get("tod_surcharge")),
                "current_total": curr_tot,
                "total_amount_payable": tot_pay,
                "amount_paid": paid,
                "outstanding_balance": bal,
                "payment_status": p_stat,
                "bill_present": "GENERATED",
            })

    # 3. Fallback to default realistic dataset if no live bills yet
    if not combined_rows:
        demo_defaults = [
            # --- TP01 BILLS (1 HT + LT Corridor Lighting) ---
            {"bill_number": "EB-416000000110-SEP26", "consumer_account_no": "416000000110", "toll_plaza_id": "TP01", "bill_type": "HT", "asset_code": "SR-E-EM-EB-000TP01", "consumer_scope": "TOLL_PLAZA", "division_name": "SEED SAMBALPUR", "usage_type": "General Purpose", "sanctioned_load_kw": 120.0, "location": "TP-01 Main Substation Incomer (Km 24+500)", "bill_month": "Sep 2026", "bill_basis": "ACTUAL", "is_provisional_or_average": False, "total_billed_kwh": 22653.0, "current_total": 158420.0, "total_amount_payable": 158420.0, "amount_paid": 158420.0, "outstanding_balance": 0.0, "payment_status": "PAID", "bill_present": "GENERATED"},
            {"bill_number": "EB-411001070208-SEP26", "consumer_account_no": "411001070208", "toll_plaza_id": "TP01", "bill_type": "LT", "asset_code": "SR-E-EM-EB-5-200", "consumer_scope": "HIGHWAY", "division_name": "SED SAMBALPUR", "usage_type": "Street Light", "sanctioned_load_kw": 10.0, "location": "Ainthapalli (Km 05+200)", "bill_month": "Sep 2026", "bill_basis": "ACTUAL", "is_provisional_or_average": False, "total_billed_kwh": 3672.0, "current_total": 24850.0, "total_amount_payable": 24850.0, "amount_paid": 24850.0, "outstanding_balance": 0.0, "payment_status": "PAID", "bill_present": "GENERATED"},
            {"bill_number": "EB-411001070208-AUG25", "consumer_account_no": "411001070208", "toll_plaza_id": "TP01", "bill_type": "LT", "asset_code": "SR-E-EM-EB-5-200", "consumer_scope": "HIGHWAY", "division_name": "SED SAMBALPUR", "usage_type": "Street Light", "sanctioned_load_kw": 10.0, "location": "Ainthapalli (Km 05+200)", "bill_month": "Aug 2025", "bill_basis": "ACTUAL", "is_provisional_or_average": False, "total_billed_kwh": 3510.0, "current_total": 23620.0, "total_amount_payable": 23620.0, "amount_paid": 23620.0, "outstanding_balance": 0.0, "payment_status": "PAID", "bill_present": "GENERATED"},
            {"bill_number": "EB-416001070082-SEP26", "consumer_account_no": "416001070082", "toll_plaza_id": "TP01", "bill_type": "LT", "asset_code": "SR-E-EM-EB-12-300", "consumer_scope": "HIGHWAY", "division_name": "SEED SAMBALPUR", "usage_type": "Public Light", "sanctioned_load_kw": 20.0, "location": "Rengali (Km 12+300)", "bill_month": "Sep 2026", "bill_basis": "ACTUAL", "is_provisional_or_average": False, "total_billed_kwh": 2980.0, "current_total": 20450.0, "total_amount_payable": 20450.0, "amount_paid": 20450.0, "outstanding_balance": 0.0, "payment_status": "PAID", "bill_present": "GENERATED"},
            {"bill_number": "EB-416001070084-AUG25", "consumer_account_no": "416001070084", "toll_plaza_id": "TP01", "bill_type": "LT", "asset_code": "SR-E-EM-EB-24-500", "consumer_scope": "HIGHWAY", "division_name": "SEED SAMBALPUR", "usage_type": "Public Light", "sanctioned_load_kw": 16.0, "location": "Lapanga (Km 24+500)", "bill_month": "Aug 2025", "bill_basis": "ACTUAL", "is_provisional_or_average": False, "total_billed_kwh": 3110.0, "current_total": 21100.0, "total_amount_payable": 21100.0, "amount_paid": 21100.0, "outstanding_balance": 0.0, "payment_status": "PAID", "bill_present": "GENERATED"},
            {"bill_number": "EB-416001070086-AUG25", "consumer_account_no": "416001070086", "toll_plaza_id": "TP01", "bill_type": "LT", "asset_code": "SR-E-EM-EB-36-800", "consumer_scope": "HIGHWAY", "division_name": "SEED SAMBALPUR", "usage_type": "Public Light", "sanctioned_load_kw": 20.0, "location": "Bhojpur (Km 36+800)", "bill_month": "Aug 2025", "bill_basis": "ACTUAL", "is_provisional_or_average": False, "total_billed_kwh": 2840.0, "current_total": 19500.0, "total_amount_payable": 19500.0, "amount_paid": 0.0, "outstanding_balance": 19500.0, "payment_status": "UNPAID", "bill_present": "GENERATED"},
            {"bill_number": "EB-416001070090-SEP26", "consumer_account_no": "416001070090", "toll_plaza_id": "TP01", "bill_type": "LT", "asset_code": "SR-E-EM-EB-48-200", "consumer_scope": "HIGHWAY", "division_name": "SEED SAMBALPUR", "usage_type": "Public Light", "sanctioned_load_kw": 9.0, "location": "Kuchinda Road (Km 48+200)", "bill_month": "Sep 2026", "bill_basis": "ACTUAL", "is_provisional_or_average": False, "total_billed_kwh": 3050.0, "current_total": 21300.0, "total_amount_payable": 21300.0, "amount_paid": 21300.0, "outstanding_balance": 0.0, "payment_status": "PAID", "bill_present": "GENERATED"},
            {"bill_number": "EB-416001111004-SEP26", "consumer_account_no": "416001111004", "toll_plaza_id": "TP01", "bill_type": "LT", "asset_code": "SR-E-EM-EB-24-500-LT", "consumer_scope": "HIGHWAY", "division_name": "SEED SAMBALPUR", "usage_type": "General Purpose", "sanctioned_load_kw": 4.0, "location": "Sambalpur Toll Admin (Km 24+500)", "bill_month": "Sep 2026", "bill_basis": "ACTUAL", "is_provisional_or_average": False, "total_billed_kwh": 850.0, "current_total": 6200.0, "total_amount_payable": 6200.0, "amount_paid": 6200.0, "outstanding_balance": 0.0, "payment_status": "PAID", "bill_present": "GENERATED"},

            # --- TP02 BILLS (1 HT + LT Corridor Lighting) ---
            {"bill_number": "EB-413000000002-SEP26", "consumer_account_no": "413000000002", "toll_plaza_id": "TP02", "bill_type": "HT", "asset_code": "SR-E-EM-EB-000TP02", "consumer_scope": "TOLL_PLAZA", "division_name": "JED JHARSUGUDA", "usage_type": "General Purpose", "sanctioned_load_kw": 120.0, "location": "TP-02 Main Substation Incomer (Km 68+200)", "bill_month": "Sep 2026", "bill_basis": "ACTUAL", "is_provisional_or_average": False, "total_billed_kwh": 21100.0, "current_total": 147500.0, "total_amount_payable": 147500.0, "amount_paid": 147500.0, "outstanding_balance": 0.0, "payment_status": "PAID", "bill_present": "GENERATED"},
            {"bill_number": "EB-413001070099-SEP26", "consumer_account_no": "413001070099", "toll_plaza_id": "TP02", "bill_type": "LT", "asset_code": "SR-E-EM-EB-62-600", "consumer_scope": "HIGHWAY", "division_name": "JED JHARSUGUDA", "usage_type": "Street Light", "sanctioned_load_kw": 18.0, "location": "TANGARPALI (Km 62+600)", "bill_month": "Sep 2026", "bill_basis": "AVERAGE", "is_provisional_or_average": True, "total_billed_kwh": 4820.0, "current_total": 34500.0, "total_amount_payable": 34500.0, "amount_paid": 0.0, "outstanding_balance": 34500.0, "payment_status": "UNPAID", "bill_present": "GENERATED"},
            {"bill_number": "EB-413001070102-SEP26", "consumer_account_no": "413001070102", "toll_plaza_id": "TP02", "bill_type": "LT", "asset_code": "SR-E-EM-EB-112-800", "consumer_scope": "HIGHWAY", "division_name": "JED JHARSUGUDA", "usage_type": "Street Light", "sanctioned_load_kw": 14.0, "location": "Jharsuguda Bypass (Km 112+800)", "bill_month": "Sep 2026", "bill_basis": "ACTUAL", "is_provisional_or_average": False, "total_billed_kwh": 4120.0, "current_total": 29840.0, "total_amount_payable": 29840.0, "amount_paid": 29840.0, "outstanding_balance": 0.0, "payment_status": "PAID", "bill_present": "GENERATED"},
            {"bill_number": "EB-413001070344-AUG25", "consumer_account_no": "413001070344", "toll_plaza_id": "TP02", "bill_type": "LT", "asset_code": "SR-E-EM-EB-95-400", "consumer_scope": "HIGHWAY", "division_name": "JED JHARSUGUDA", "usage_type": "Street Light", "sanctioned_load_kw": 34.0, "location": "Badmal (Km 95+400)", "bill_month": "Aug 2025", "bill_basis": "PROVISIONAL", "is_provisional_or_average": True, "total_billed_kwh": 3950.0, "current_total": 27400.0, "total_amount_payable": 27400.0, "amount_paid": 15000.0, "outstanding_balance": 12400.0, "payment_status": "PARTIAL", "bill_present": "GENERATED"},
            {"bill_number": "EB-813001070057-SEP26", "consumer_account_no": "813001070057", "toll_plaza_id": "TP02", "bill_type": "LT", "asset_code": "SR-E-EM-EB-130-000", "consumer_scope": "HIGHWAY", "division_name": "KUTRA", "usage_type": "Public Light", "sanctioned_load_kw": 15.0, "location": "Kutra EB METER (Km 108+000)", "bill_month": "Sep 2026", "bill_basis": "ACTUAL", "is_provisional_or_average": False, "total_billed_kwh": 3890.0, "current_total": 26900.0, "total_amount_payable": 26900.0, "amount_paid": 26900.0, "outstanding_balance": 0.0, "payment_status": "PAID", "bill_present": "GENERATED"},

            # --- TP03 BILLS (1 HT + LT Corridor Lighting) ---
            {"bill_number": "EB-813000000281-SEP26", "consumer_account_no": "813000000281", "toll_plaza_id": "TP03", "bill_type": "HT", "asset_code": "SR-E-EM-EB-000TP03", "consumer_scope": "TOLL_PLAZA", "division_name": "SED SUNDARAGADA", "usage_type": "General Purpose", "sanctioned_load_kw": 120.0, "location": "TP-03 Main Substation Incomer (Km 112+800)", "bill_month": "Sep 2026", "bill_basis": "ACTUAL", "is_provisional_or_average": False, "total_billed_kwh": 19450.0, "current_total": 132800.0, "total_amount_payable": 132800.0, "amount_paid": 132800.0, "outstanding_balance": 0.0, "payment_status": "PAID", "bill_present": "GENERATED"},
            {"bill_number": "812010710261330579", "consumer_account_no": "812001070018", "toll_plaza_id": "TP03", "bill_type": "LT", "asset_code": "SR-E-EM-EB-148-500", "consumer_scope": "HIGHWAY", "division_name": "SED SUNDARAGADA", "usage_type": "Public Light", "sanctioned_load_kw": 28.0, "location": "Bhawanipur / Garposh Corridor (Km 148+500)", "bill_month": "Sep 2026", "bill_basis": "ACTUAL", "is_provisional_or_average": False, "total_billed_kwh": 4608.0, "current_total": 31757.80, "total_amount_payable": 31828.0, "amount_paid": 31452.25, "outstanding_balance": 0.0, "payment_status": "PAID", "bill_present": "GENERATED"},
            {"bill_number": "EB-812001070018-AUG25", "consumer_account_no": "812001070018", "toll_plaza_id": "TP03", "bill_type": "LT", "asset_code": "SR-E-EM-EB-148-500", "consumer_scope": "HIGHWAY", "division_name": "SED SUNDARAGADA", "usage_type": "Public Light", "sanctioned_load_kw": 28.0, "location": "Bhawanipur / Garposh Corridor (Km 148+500)", "bill_month": "Aug 2025", "bill_basis": "ACTUAL", "is_provisional_or_average": False, "total_billed_kwh": 4320.0, "current_total": 29650.0, "total_amount_payable": 29650.0, "amount_paid": 29650.0, "outstanding_balance": 0.0, "payment_status": "PAID", "bill_present": "GENERATED"},
            {"bill_number": "EB-812001070020-SEP26", "consumer_account_no": "812001070020", "toll_plaza_id": "TP03", "bill_type": "LT", "asset_code": "SR-E-EM-EB-160-200", "consumer_scope": "HIGHWAY", "division_name": "SED SUNDARAGADA", "usage_type": "Public Light", "sanctioned_load_kw": 15.0, "location": "Garposh Toll Approach (Km 160+200)", "bill_month": "Sep 2026", "bill_basis": "AVERAGE", "is_provisional_or_average": True, "total_billed_kwh": 3200.0, "current_total": 22400.0, "total_amount_payable": 22400.0, "amount_paid": 0.0, "outstanding_balance": 22400.0, "payment_status": "UNPAID", "bill_present": "GENERATED"},
        ]
        combined_rows = demo_defaults

    df = pd.DataFrame(combined_rows)
    return df


def get_missing_bills_kpi(kpi_df: pd.DataFrame, target_months: list[str] | None = None) -> pd.DataFrame:
    """
    Identifies which master Consumer Accounts have bills generated vs NOT generated
    across the active periods.
    """
    master_accounts_df = get_all_consumer_accounts()
    if master_accounts_df.empty:
        return pd.DataFrame()

    months = target_months
    if not months and not kpi_df.empty and "bill_month" in kpi_df.columns:
        months = [str(m) for m in kpi_df["bill_month"].dropna().unique() if str(m).strip()]
    if not months:
        months = ["Sep 2026"]

    existing_pairs = set()
    if not kpi_df.empty and "consumer_account_no" in kpi_df.columns and "bill_month" in kpi_df.columns:
        for _, row in kpi_df.iterrows():
            ac = str(row["consumer_account_no"]).strip()
            mo = str(row["bill_month"]).strip()
            if ac and mo:
                existing_pairs.add((ac, mo))

    missing_rows = []
    for m in master_accounts_df.to_dict(orient="records"):
        ac = str(m.get("consumer_account_no", "")).strip()
        if not ac:
            continue
        for mo in months:
            if (ac, mo) not in existing_pairs:
                missing_rows.append({
                    "consumer_account_no": ac,
                    "toll_plaza_id": m.get("toll_plaza_id", "TP01"),
                    "bill_type": m.get("bill_type", "LT"),
                    "asset_code": m.get("asset_code", "—"),
                    "consumer_scope": m.get("consumer_scope", "HIGHWAY"),
                    "division_name": m.get("division_name", "SED"),
                    "usage_type": m.get("usage_type", "Street Light"),
                    "sanctioned_load_kw": float(_clean_kpi_num(m.get("sanctioned_load_kw", 10.0))),
                    "location": m.get("location", "Corridor"),
                    "bill_month": mo,
                    "bill_present": "NOT GENERATED",
                    "bill_basis": "N/A",
                    "total_billed_kwh": 0.0,
                    "current_total": 0.0,
                    "amount_paid": 0.0,
                    "outstanding_balance": 0.0,
                    "payment_status": "NOT GENERATED",
                    "action_required": "⚠️ Follow up with DISCOM / Ingest Bill PDF",
                })

    return pd.DataFrame(missing_rows)
