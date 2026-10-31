from fastapi import APIRouter, UploadFile, File, HTTPException
import hashlib
import sys
import os
from typing import Any

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "active_app"))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from core.db_sync import log_audit_event

router = APIRouter(prefix="/api/juno", tags=["Juno Import"])

# In-memory batch store
IMPORT_BATCHES = [
    {
        "batch_id": "JUNO-BATCH-20261028-01",
        "file_name": "SRTPL_Oct2026_EB_Log.csv",
        "equipment": "EB Grid Supply",
        "records_count": 1420,
        "sha256": "4f9b8c2a1e7d6b3c5a8e0f1d2c3b4a5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c",
        "status": "INGESTED",
        "imported_at": "2026-10-28 14:22:10",
    },
    {
        "batch_id": "JUNO-BATCH-20261025-02",
        "file_name": "DG_RunHours_Fuel_Sep2026.xlsx",
        "equipment": "DG Backup",
        "records_count": 480,
        "sha256": "8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b",
        "status": "INGESTED",
        "imported_at": "2026-10-25 11:05:44",
    },
]


@router.get("/batches")
def get_import_batches() -> list[dict[str, Any]]:
    return IMPORT_BATCHES


@router.post("/upload")
async def import_juno_file(equipment: str, file: UploadFile = File(...)) -> dict[str, Any]:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    sha256_hash = hashlib.sha256(content).hexdigest()

    # Check for duplicate by SHA-256 hash or filename
    for b in IMPORT_BATCHES:
        if b["sha256"] == sha256_hash or b["file_name"] == file.filename:
            log_audit_event("DUPLICATE_REJECTED", f"Blocked duplicate file {file.filename} (Hash: {sha256_hash[:8]}...)", "FILE", file.filename, "REJECTED")
            return {
                "status": "DUPLICATE_REJECTED",
                "message": f"DUPLICATE REJECTED: File '{file.filename}' was already ingested in batch {b['batch_id']}.",
                "existing_batch": b,
            }

    batch_id = f"JUNO-BATCH-{len(IMPORT_BATCHES) + 1:04d}"
    new_batch = {
        "batch_id": batch_id,
        "file_name": file.filename,
        "equipment": equipment,
        "records_count": max(12, len(content) // 256),
        "sha256": sha256_hash,
        "status": "INGESTED",
        "imported_at": "2026-10-31 21:00:00",
    }
    IMPORT_BATCHES.insert(0, new_batch)
    log_audit_event("JUNO_IMPORT_SUCCESS", f"Ingested {file.filename} ({equipment}) under batch {batch_id}", "BATCH", batch_id, "SUCCESS")

    return {
        "status": "SUCCESS",
        "message": f"Successfully ingested {file.filename} into {equipment} pipeline.",
        "batch": new_batch,
    }
