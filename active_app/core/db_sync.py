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


def get_all_energy_bills() -> pd.DataFrame:
    """Retrieves all energy bills from Supabase or fallback session state / demo bills."""
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

    # Fallback to demo bills
    return get_demo_bills()


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
