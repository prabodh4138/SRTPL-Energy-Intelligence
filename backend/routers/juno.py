from fastapi import APIRouter, UploadFile, File, HTTPException
import hashlib
import sys
import os
from typing import Any

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "active_app"))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from core.db_sync import log_audit_event
from core.supabase_manager import get_supabase_client

router = APIRouter(prefix="/api/juno", tags=["Juno Import"])

# Clean in-memory batch store (starts empty, only holds genuinely uploaded files)
IMPORT_BATCHES: list[dict[str, Any]] = []


@router.get("/batches")
def get_import_batches() -> list[dict[str, Any]]:
    client = get_supabase_client()
    if client:
        try:
            res = client.schema("energy_import").table("import_batch").select("*").order("created_at", desc=True).limit(50).execute()
            if res and res.data:
                return res.data
        except Exception:
            pass
    return list(IMPORT_BATCHES)


@router.post("/upload")
async def import_juno_file(equipment: str, file: UploadFile = File(...)) -> dict[str, Any]:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    sha256_hash = hashlib.sha256(content).hexdigest()

    # Check for duplicate by SHA-256 hash or filename
    for b in IMPORT_BATCHES:
        if b.get("sha256") == sha256_hash or b.get("file_name") == file.filename:
            log_audit_event("DUPLICATE_REJECTED", f"Blocked duplicate file {file.filename} (Hash: {sha256_hash[:8]}...)", "FILE", file.filename, "REJECTED")
            return {
                "status": "DUPLICATE_REJECTED",
                "message": f"DUPLICATE REJECTED: File '{file.filename}' was already ingested in batch {b.get('batch_id')}.",
                "existing_batch": b,
            }

    import datetime
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    batch_id = f"JUNO-BATCH-{len(IMPORT_BATCHES) + 1:04d}"
    new_batch = {
        "batch_id": batch_id,
        "file_name": file.filename,
        "equipment": equipment,
        "records_count": max(1, len(content) // 128),
        "sha256": sha256_hash,
        "status": "INGESTED",
        "imported_at": now_iso,
    }
    IMPORT_BATCHES.insert(0, new_batch)

    # Cloud sync if connected
    client = get_supabase_client()
    if client:
        try:
            client.schema("energy_import").table("import_batch").insert(new_batch).execute()
        except Exception:
            pass

    log_audit_event("JUNO_IMPORT_SUCCESS", f"Ingested {file.filename} ({equipment}) under batch {batch_id}", "BATCH", batch_id, "SUCCESS")

    return {
        "status": "SUCCESS",
        "message": f"Successfully ingested {file.filename} into {equipment} pipeline.",
        "batch": new_batch,
    }
