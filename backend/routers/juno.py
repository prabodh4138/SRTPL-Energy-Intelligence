from fastapi import APIRouter, UploadFile, File, HTTPException
import hashlib
import sys
import os
import tempfile
from pathlib import Path
from typing import Any
import datetime

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "active_app"))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from core.db_sync import log_audit_event
from core.supabase_manager import get_supabase_client
from core.live_pipeline import execute_live_juno_ingestion
from core.local_db import (
    init_local_db,
    is_juno_file_duplicate_sqlite,
    fetch_juno_batches_sqlite,
)

router = APIRouter(prefix="/api/juno", tags=["Juno Import"])

# Equipment code normalizer mapping
EQUIPMENT_TYPE_MAP = {
    "⚡ EB Grid Supply": "EB",
    "EB Grid Supply": "EB",
    "EB": "EB",
    "⚡ DG Backup Generator": "DG",
    "DG Backup Generator": "DG",
    "DG": "DG",
    "☀️ Solar Rooftop Array": "SOLAR",
    "Solar Rooftop Array": "SOLAR",
    "SOLAR": "SOLAR",
    "🔌 Step-Down Transformer": "TRANSFORMER",
    "Step-Down Transformer": "TRANSFORMER",
    "TRANSFORMER": "TRANSFORMER",
    "🔋 UPS Battery System": "UPS",
    "UPS Battery System": "UPS",
    "UPS": "UPS",
}

EQUIPMENT_LABEL_MAP = {
    "EB": "⚡ EB Grid Supply",
    "DG": "⚡ DG Backup Generator",
    "SOLAR": "☀️ Solar Rooftop Array",
    "TRANSFORMER": "🔌 Step-Down Transformer",
    "UPS": "🔋 UPS Battery System",
}

# In-memory batch store (syncs with SQLite and Supabase)
IMPORT_BATCHES: list[dict[str, Any]] = []


@router.get("/batches")
def get_import_batches() -> list[dict[str, Any]]:
    """Returns all historical Juno batches formatted for the frontend table.
    Merges records from Supabase, SQLite, and in-memory cache with deduplication."""
    batches_map: dict[str, dict[str, Any]] = {}

    # 1. First load from Supabase if connected
    client = get_supabase_client()
    if client:
        try:
            res = (
                client.schema("energy_import")
                .table("import_file")
                .select("import_file_id, import_batch_id, original_filename, sha256_hash, report_type, row_count, valid_row_count, created_at")
                .order("created_at", desc=True)
                .limit(100)
                .execute()
            )
            if res and res.data:
                for idx, r in enumerate(res.data):
                    sha = str(r.get("sha256_hash") or "").strip()
                    if sha:
                        rtype = str(r.get("report_type") or "EB").upper()
                        b_id = str(r.get("import_batch_id") or "")
                        if not b_id.startswith("JUNO-BATCH-"):
                            b_id = f"JUNO-BATCH-{idx + 1:04d}"
                        batches_map[sha] = {
                            "batch_id": b_id,
                            "file_name": r.get("original_filename") or "—",
                            "equipment": EQUIPMENT_LABEL_MAP.get(rtype, f"⚡ {rtype}"),
                            "records_count": int(r.get("valid_row_count") or r.get("row_count") or 0),
                            "sha256": sha,
                            "imported_at": str(r.get("created_at") or "")[:19].replace("T", " "),
                            "status": "INGESTED",
                        }
        except Exception:
            pass

    # 2. Merge from local SQLite database
    try:
        sqlite_batches = fetch_juno_batches_sqlite()
        for b in sqlite_batches:
            sha = b.get("sha256")
            if sha and sha not in batches_map:
                batches_map[sha] = b
    except Exception:
        pass

    # 3. Merge from in-memory cache
    for b in IMPORT_BATCHES:
        sha = b.get("sha256")
        if sha and sha not in batches_map:
            batches_map[sha] = b

    result = list(batches_map.values())
    result.sort(key=lambda x: str(x.get("imported_at") or ""), reverse=True)
    return result


@router.post("/upload")
async def import_juno_file(equipment: str, file: UploadFile = File(...)) -> dict[str, Any]:
    """Uploads, validates, deduplicates, and ingests interval logs into Supabase & SQLite."""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    sha256_hash = hashlib.sha256(content).hexdigest()
    rtype = EQUIPMENT_TYPE_MAP.get(equipment.strip(), "EB")
    equipment_label = EQUIPMENT_LABEL_MAP.get(rtype, equipment)

    # -------------------------------------------------------------------------
    # LEVEL 1 DEDUPLICATION AT APPLICATION LEVEL
    # -------------------------------------------------------------------------
    # Check in-memory store
    for b in IMPORT_BATCHES:
        if b.get("sha256") == sha256_hash:
            msg = f"⛔ DUPLICATE REJECTED (Application Level): File '{file.filename}' (SHA-256: {sha256_hash[:16]}...) was already ingested in batch {b.get('batch_id')} on {b.get('imported_at')}."
            log_audit_event("DUPLICATE_REJECTED", msg, "FILE", file.filename, "REJECTED")
            return {
                "status": "DUPLICATE_REJECTED",
                "message": msg,
                "sha256": sha256_hash,
                "filename": file.filename,
                "existing_batch": b,
            }

    # Check local SQLite database
    is_sq_dup, sq_match = is_juno_file_duplicate_sqlite(sha256_hash)
    if is_sq_dup and sq_match:
        msg = f"⛔ DUPLICATE REJECTED (Application Level): File '{file.filename}' (SHA-256: {sha256_hash[:16]}...) was already ingested on {sq_match.get('created_at')}."
        log_audit_event("DUPLICATE_REJECTED", msg, "FILE", file.filename, "REJECTED")
        return {
            "status": "DUPLICATE_REJECTED",
            "message": msg,
            "sha256": sha256_hash,
            "filename": file.filename,
            "existing_batch": sq_match,
        }

    # Check Supabase cloud database if connected
    client = get_supabase_client()
    if client:
        try:
            res = (
                client.schema("energy_import")
                .table("import_file")
                .select("import_file_id, import_batch_id, original_filename, created_at, valid_row_count")
                .eq("sha256_hash", sha256_hash)
                .limit(1)
                .execute()
            )
            if res.data and len(res.data) > 0:
                match = res.data[0]
                if int(match.get("valid_row_count") or 0) > 0:
                    msg = f"⛔ DUPLICATE REJECTED (Application Level): File '{file.filename}' was already ingested into Supabase on {match.get('created_at')}."
                    log_audit_event("DUPLICATE_REJECTED", msg, "FILE", file.filename, "REJECTED")
                    return {
                        "status": "DUPLICATE_REJECTED",
                        "message": msg,
                        "sha256": sha256_hash,
                        "filename": file.filename,
                        "existing_batch": match,
                    }
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # PARSE, NORMALIZE, AND INGEST THROUGH LIVE PIPELINE
    # -------------------------------------------------------------------------
    ext = Path(file.filename).suffix or ".csv"
    fd, temp_name = tempfile.mkstemp(prefix="juno_upload_", suffix=ext)
    temp_path = Path(temp_name)
    try:
        temp_path.write_bytes(content)
        os.close(fd)

        # Run master ingestion pipeline
        res = execute_live_juno_ingestion(
            file_path=temp_path,
            expected_type=rtype,
            uploaded_by="admin@srtpl.com",
            allow_reimport=False,
        )
    except Exception as exc:
        msg = f"Pipeline execution failed: {exc}"
        log_audit_event("JUNO_IMPORT_ERROR", msg, "FILE", file.filename, "ERROR")
        return {
            "status": "ERROR",
            "message": msg,
            "sha256": sha256_hash,
            "filename": file.filename,
        }
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass

    # -------------------------------------------------------------------------
    # LEVEL 1 & LEVEL 2 DEDUPLICATION CHECK FROM PIPELINE RESULT
    # -------------------------------------------------------------------------
    if res.get("status") == "DUPLICATE_FILE":
        msg = res.get("message") or f"⛔ DUPLICATE REJECTED: File '{file.filename}' has already been imported."
        log_audit_event("DUPLICATE_REJECTED", msg, "FILE", file.filename, "REJECTED")
        return {
            "status": "DUPLICATE_REJECTED",
            "message": msg,
            "sha256": sha256_hash,
            "filename": file.filename,
        }

    if res.get("status") == "TYPE_MISMATCH":
        return {
            "status": "ERROR",
            "message": res.get("message", "File format or report type mismatch."),
            "sha256": sha256_hash,
            "filename": file.filename,
        }

    if not res.get("success"):
        return {
            "status": "ERROR",
            "message": res.get("message", "Ingestion processing failed."),
            "sha256": sha256_hash,
            "filename": file.filename,
        }

    # -------------------------------------------------------------------------
    # SUCCESS: REGISTER BATCH AND RETURN CONFIRMATION
    # -------------------------------------------------------------------------
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    batch_count = len(IMPORT_BATCHES) + 1
    batch_id = f"JUNO-BATCH-{batch_count:04d}"

    new_batch = {
        "batch_id": batch_id,
        "file_name": file.filename,
        "equipment": equipment_label,
        "records_count": res.get("valid_rows", 0),
        "valid_count": res.get("valid_rows", 0),
        "exception_count": res.get("exception_rows", 0),
        "sha256": sha256_hash,
        "status": "INGESTED",
        "imported_at": now_iso,
        "cloud_injected": res.get("cloud_injected", False),
        "asset_id": res.get("asset_id", "—"),
    }
    IMPORT_BATCHES.insert(0, new_batch)

    cloud_note = " (Cloud Sync Active: Injected into Supabase)" if res.get("cloud_injected") else ""
    success_msg = (
        f"Successfully ingested {file.filename} into {equipment_label} pipeline: "
        f"{res.get('valid_rows', 0)} clean interval readings, {res.get('exception_rows', 0)} exceptions logged{cloud_note}."
    )
    log_audit_event(
        "JUNO_IMPORT_SUCCESS",
        f"Ingested {file.filename} ({equipment_label}) under batch {batch_id}. Valid: {res.get('valid_rows')}, Cloud: {res.get('cloud_injected')}",
        "BATCH",
        batch_id,
        "SUCCESS"
    )

    return {
        "status": "SUCCESS",
        "message": success_msg,
        "batch": new_batch,
        "details": {
            "valid_rows": res.get("valid_rows", 0),
            "exception_rows": res.get("exception_rows", 0),
            "cloud_injected": res.get("cloud_injected", False),
            "cloud_error": res.get("cloud_error"),
            "asset_id": res.get("asset_id"),
        }
    }
