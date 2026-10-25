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

    {"asset_id": "AST-EB-02", "asset_code": "SR-E-EM-EB-130-000", "asset_name": "Main EB Incomer TP02", "plaza_id": "TP02", "source_type": "EB", "capacity_kva": 500.0, "is_active": True},
    {"asset_id": "AST-DG-03", "asset_code": "SR-E-AP-DGX-000003", "asset_name": "Diesel Generator 3", "plaza_id": "TP02", "source_type": "DG", "capacity_kva": 250.0, "is_active": True},
    {"asset_id": "AST-DG-04", "asset_code": "SR-E-AP-DGX-000004", "asset_name": "Diesel Generator 4", "plaza_id": "TP02", "source_type": "DG", "capacity_kva": 250.0, "is_active": True},
    {"asset_id": "AST-SOL-02", "asset_code": "SR-E-AP-SPX-000002", "asset_name": "Solar Plant 2", "plaza_id": "TP02", "source_type": "SOLAR", "capacity_kva": 100.0, "is_active": True},
    {"asset_id": "AST-TRF-03", "asset_code": "SR-E-HT-TFR-000003", "asset_name": "HT Substation Transformer 3", "plaza_id": "TP02", "source_type": "TRANSFORMER", "capacity_kva": 500.0, "is_active": True},
    {"asset_id": "AST-UPS-04", "asset_code": "SR-E-AP-UPS-000004", "asset_name": "Toll Plaza UPS 4", "plaza_id": "TP02", "source_type": "UPS", "capacity_kva": 40.0, "is_active": True},
    {"asset_id": "AST-UPS-09", "asset_code": "SR-E-AP-UPS-000009", "asset_name": "Toll Plaza UPS 9", "plaza_id": "TP02", "source_type": "UPS", "capacity_kva": 40.0, "is_active": True},

    {"asset_id": "AST-EB-03", "asset_code": "SRTPL_Test_JUNO_EB", "asset_name": "Main EB Incomer TP03", "plaza_id": "TP03", "source_type": "EB", "capacity_kva": 500.0, "is_active": True},
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
# 3. ENERGY BILLS CRUD (Add, Modify, Delete)
# ---------------------------------------------------------------------------

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
