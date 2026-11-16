"""SRTPL Power Consumption Analytics — Deprecated Local DB Shim.

ARCHITECTURAL MANDATE:
Zero intermediate or local SQLite database. Supabase PostgreSQL is the sole authoritative
source of truth for all schemas, views, tables, and analytics.
All methods here delegate directly to Supabase or in-memory caches.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from core.supabase_manager import get_supabase_client


def get_sqlite_connection() -> Any:
    """
    Deprecated: Local SQLite database has been completely removed per project governance.
    Supabase PostgreSQL is the sole source of truth.
    """
    raise RuntimeError(
        "Local SQLite database has been permanently removed per architectural requirements. "
        "Supabase PostgreSQL is the sole source of truth. Connect via get_supabase_client()."
    )


def init_local_db() -> None:
    """No-op: Local SQLite database initialization is permanently disabled."""
    pass


# ---------------------------------------------------------------------------
# Consumer Master Operations (Direct Supabase)
# ---------------------------------------------------------------------------

def fetch_consumers_from_sqlite() -> pd.DataFrame:
    """Direct Supabase query for energy_consumer_master."""
    client = get_supabase_client()
    if not client:
        return pd.DataFrame()
    try:
        res = client.table("energy_consumer_master").select("*").execute()
        return pd.DataFrame(res.data or [])
    except Exception:
        try:
            res = client.table("consumer_account").select("*").execute()
            return pd.DataFrame(res.data or [])
        except Exception:
            return pd.DataFrame()


def save_consumer_to_sqlite(payload: Dict[str, Any]) -> bool:
    """Direct Supabase upsert for energy_consumer_master."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        client.table("energy_consumer_master").upsert(payload, on_conflict="consumer_account_no").execute()
        return True
    except Exception:
        try:
            client.table("consumer_account").upsert(payload, on_conflict="consumer_account_no").execute()
            return True
        except Exception:
            return False


def delete_consumer_from_sqlite(consumer_account_no: str) -> bool:
    """Direct Supabase deletion for energy_consumer_master."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        client.table("energy_consumer_master").delete().eq("consumer_account_no", consumer_account_no).execute()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Energy Bills Operations (Direct Supabase)
# ---------------------------------------------------------------------------

def fetch_energy_bills_from_sqlite() -> pd.DataFrame:
    """Direct Supabase query for energy_bills."""
    client = get_supabase_client()
    if not client:
        return pd.DataFrame()
    try:
        res = client.table("energy_bills").select("*").execute()
        return pd.DataFrame(res.data or [])
    except Exception:
        return pd.DataFrame()


def save_bill_to_sqlite(payload: Dict[str, Any]) -> bool:
    """Direct Supabase upsert for energy_bills."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        client.table("energy_bills").upsert(payload, on_conflict="bill_number").execute()
        return True
    except Exception:
        return False


def delete_bill_from_sqlite(bill_number: str) -> bool:
    """Direct Supabase deletion for energy_bills."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        client.table("energy_bills").delete().eq("bill_number", bill_number).execute()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Payment Receipts Operations (Direct Supabase)
# ---------------------------------------------------------------------------

def fetch_payment_receipts_from_sqlite() -> pd.DataFrame:
    """Direct Supabase query for payment_receipts."""
    client = get_supabase_client()
    if not client:
        return pd.DataFrame()
    try:
        res = client.table("payment_receipts").select("*").execute()
        return pd.DataFrame(res.data or [])
    except Exception:
        return pd.DataFrame()


def save_receipt_to_sqlite(payload: Dict[str, Any]) -> bool:
    """Direct Supabase upsert for payment_receipts."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        client.table("payment_receipts").upsert(payload, on_conflict="receipt_number").execute()
        return True
    except Exception:
        return False


def delete_receipt_from_sqlite(receipt_number: str) -> bool:
    """Direct Supabase deletion for payment_receipts."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        client.table("payment_receipts").delete().eq("receipt_number", receipt_number).execute()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Juno Ingestion & Deduplication Operations (Direct Supabase)
# ---------------------------------------------------------------------------

def is_juno_file_duplicate_sqlite(sha256_hash: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Checks file deduplication directly in Supabase energy_import.import_file."""
    client = get_supabase_client()
    if not client:
        return False, None
    try:
        res = client.table("import_file").select("*").eq("sha256_hash", sha256_hash).limit(1).execute()
        if res.data and len(res.data) > 0:
            return True, res.data[0]
    except Exception:
        try:
            res = client.schema("energy_import").table("import_file").select("*").eq("sha256_hash", sha256_hash).limit(1).execute()
            if res.data and len(res.data) > 0:
                return True, res.data[0]
        except Exception:
            pass
    return False, None


def save_juno_ingestion_to_sqlite(*args: Any, **kwargs: Any) -> bool:
    """No-op: Ingestion saves directly to Supabase PostgreSQL."""
    return True


def fetch_juno_batches_sqlite() -> List[Dict[str, Any]]:
    """Fetches Juno batches directly from Supabase."""
    client = get_supabase_client()
    if not client:
        return []
    try:
        res = client.table("import_batch").select("*").order("created_at", desc=True).limit(100).execute()
        return res.data or []
    except Exception:
        try:
            res = client.schema("energy_import").table("import_batch").select("*").order("created_at", desc=True).limit(100).execute()
            return res.data or []
        except Exception:
            return []


def wipe_only_juno_data_sqlite() -> Dict[str, Any]:
    """No-op: Local SQLite database does not exist."""
    return {"status": "SUCCESS", "message": "Local DB removed. Supabase is single source of truth."}


def wipe_all_operational_data_sqlite() -> Dict[str, Any]:
    """No-op: Local SQLite database does not exist."""
    return {"status": "SUCCESS", "message": "Local DB removed. Supabase is single source of truth."}
