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
    "AUTO": "AUTO",
    "ANY": "AUTO",
    "ALL": "AUTO",
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
                .limit(200)
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
                        fname = r.get("original_filename") or "—"
                        if fname.startswith("juno_upload_") or fname.startswith("srtpl_"):
                            fname = f"{rtype}_DailyLogReport_{sha[:8]}.csv"
                        batches_map[sha] = {
                            "batch_id": b_id,
                            "file_name": fname,
                            "original_filename": fname,
                            "equipment": EQUIPMENT_LABEL_MAP.get(rtype, f"⚡ {rtype}"),
                            "records_count": int(r.get("valid_row_count") or r.get("row_count") or 0),
                            "sha256": sha,
                            "imported_at": str(r.get("created_at") or "")[:19].replace("T", " "),
                            "status": "INGESTED",
                        }
        except Exception:
            pass

    # 2. Merge from in-memory cache (in-memory holds authoritative user-provided filenames)
    for b in IMPORT_BATCHES:
        sha = b.get("sha256")
        if sha:
            batches_map[sha] = b

    result = list(batches_map.values())
    result.sort(key=lambda x: str(x.get("imported_at") or ""), reverse=True)
    return result


def _process_single_juno_upload(
    filename: str,
    content: bytes,
    equipment_param: str = "AUTO",
    uploaded_by: str = "admin@srtpl.com",
    allow_reimport: bool = False,
) -> dict[str, Any]:
    """Helper that validates, deduplicates, auto-detects equipment, and ingests a single Juno CSV file into Supabase & runtime store."""
    if not content:
        return {
            "status": "ERROR",
            "success": False,
            "filename": filename,
            "original_filename": filename,
            "sha256": "",
            "message": f"File '{filename}' is empty (0 bytes).",
            "records_count": 0,
            "valid_count": 0,
            "cloud_injected": False,
        }

    sha256_hash = hashlib.sha256(content).hexdigest()

    # -------------------------------------------------------------------------
    # LEVEL 1 DEDUPLICATION AT APPLICATION LEVEL
    # -------------------------------------------------------------------------
    # Check in-memory store
    if not allow_reimport:
        for b in list(IMPORT_BATCHES):
            if b.get("sha256") == sha256_hash:
                # Check if data actually exists in runtime store or Supabase
                from backend.services.energy_command_store import get_runtime_readings
                rtype_key = str(b.get("report_type") or "EB").lower()
                has_actual_readings = len(get_runtime_readings(rtype_key)) > 0

                client = get_supabase_client()
                if client and not has_actual_readings:
                    try:
                        chk = client.schema("energy_readings").table(rtype_key).select("reading_datetime").limit(1).execute()
                        if chk and chk.data:
                            has_actual_readings = True
                    except Exception:
                        pass

                if has_actual_readings and int(b.get("records_count") or 0) > 0:
                    msg = f"⛔ DUPLICATE REJECTED (Application Level): File '{filename}' (SHA-256: {sha256_hash[:16]}...) was already ingested in batch {b.get('batch_id')} on {b.get('imported_at')}."
                    log_audit_event("DUPLICATE_REJECTED", msg, "FILE", filename, "REJECTED")
                    return {
                        "status": "DUPLICATE_REJECTED",
                        "success": False,
                        "message": msg,
                        "sha256": sha256_hash,
                        "filename": filename,
                        "original_filename": filename,
                        "existing_batch": b,
                        "equipment": b.get("equipment", "EB"),
                        "equipment_label": b.get("equipment", "⚡ EB Grid Supply"),
                        "records_count": b.get("records_count", 0),
                        "valid_count": b.get("records_count", 0),
                        "cloud_injected": False,
                    }
                else:
                    # Previous upload failed to persist readings; purge stale batch entry to permit re-upload
                    IMPORT_BATCHES.remove(b)

        # Check Supabase cloud database if connected
        client = get_supabase_client()
        if client:
            try:
                res = (
                    client.schema("energy_import")
                    .table("import_file")
                    .select("import_file_id, import_batch_id, original_filename, created_at, valid_row_count, report_type")
                    .eq("sha256_hash", sha256_hash)
                    .limit(1)
                    .execute()
                )
                if res.data and len(res.data) > 0:
                    match = res.data[0]
                    if int(match.get("valid_row_count") or 0) > 0:
                        matched_rtype = str(match.get("report_type") or "EB").upper()
                        msg = f"⛔ DUPLICATE REJECTED (Application Level): File '{filename}' was already ingested into Supabase on {match.get('created_at')}."
                        log_audit_event("DUPLICATE_REJECTED", msg, "FILE", filename, "REJECTED")
                        return {
                            "status": "DUPLICATE_REJECTED",
                            "success": False,
                            "message": msg,
                            "sha256": sha256_hash,
                            "filename": filename,
                            "original_filename": filename,
                            "existing_batch": match,
                            "equipment": matched_rtype,
                            "equipment_label": EQUIPMENT_LABEL_MAP.get(matched_rtype, f"⚡ {matched_rtype}"),
                            "records_count": match.get("valid_row_count", 0),
                            "valid_count": match.get("valid_row_count", 0),
                            "cloud_injected": True,
                        }
            except Exception:
                pass

    # -------------------------------------------------------------------------
    # PARSE, NORMALIZE, AND INGEST THROUGH LIVE PIPELINE WITH AUTO-DETECTION
    # -------------------------------------------------------------------------
    ext = Path(filename).suffix or ".csv"
    fd, temp_name = tempfile.mkstemp(prefix="juno_upload_", suffix=ext)
    temp_path = Path(temp_name)

    expected_type = None
    if equipment_param and equipment_param.strip().upper() not in ["AUTO", "ANY", "ALL", ""]:
        expected_type = EQUIPMENT_TYPE_MAP.get(equipment_param.strip(), equipment_param.strip())

    try:
        temp_path.write_bytes(content)
        os.close(fd)

        # Run master ingestion pipeline (auto-detects equipment if expected_type is None)
        res = execute_live_juno_ingestion(
            file_path=temp_path,
            expected_type=expected_type,
            uploaded_by=uploaded_by,
            allow_reimport=allow_reimport,
            original_filename=filename,
        )
    except Exception as exc:
        msg = f"Pipeline execution failed for '{filename}': {exc}"
        log_audit_event("JUNO_IMPORT_ERROR", msg, "FILE", filename, "ERROR")
        return {
            "status": "ERROR",
            "success": False,
            "message": msg,
            "sha256": sha256_hash,
            "filename": filename,
            "original_filename": filename,
            "records_count": 0,
            "valid_count": 0,
            "cloud_injected": False,
        }
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass

    # Handle pipeline deduplication response
    if res.get("status") == "DUPLICATE_FILE":
        msg = res.get("message") or f"⛔ DUPLICATE REJECTED: File '{filename}' has already been imported."
        log_audit_event("DUPLICATE_REJECTED", msg, "FILE", filename, "REJECTED")
        return {
            "status": "DUPLICATE_REJECTED",
            "success": False,
            "message": msg,
            "sha256": sha256_hash,
            "filename": filename,
            "original_filename": filename,
            "records_count": 0,
            "valid_count": 0,
            "cloud_injected": False,
        }

    if res.get("status") == "TYPE_MISMATCH":
        return {
            "status": "ERROR",
            "success": False,
            "message": res.get("message", "File format or report type mismatch."),
            "sha256": sha256_hash,
            "filename": filename,
            "original_filename": filename,
            "records_count": 0,
            "valid_count": 0,
            "cloud_injected": False,
        }

    if not res.get("success"):
        return {
            "status": "ERROR",
            "success": False,
            "message": res.get("message", "Ingestion processing failed."),
            "sha256": sha256_hash,
            "filename": filename,
            "original_filename": filename,
            "records_count": 0,
            "valid_count": 0,
            "cloud_injected": False,
        }

    # -------------------------------------------------------------------------
    # SUCCESS: REGISTER BATCH AND RETURN CONFIRMATION WITH ASSET BREAKDOWN
    # -------------------------------------------------------------------------
    detected_rtype = str(res.get("report_type") or "EB").upper()
    equipment_label = EQUIPMENT_LABEL_MAP.get(detected_rtype, f"⚡ {detected_rtype}")
    asset_code = str(res.get("asset_code") or res.get("asset_id") or "—").strip()
    valid_count = int(res.get("valid_rows") or 0)
    exception_count = int(res.get("exception_rows") or 0)
    total_records = int(res.get("total_records") or valid_count)
    cloud_injected = bool(res.get("cloud_injected", False))
    asset_breakdown = res.get("asset_breakdown", {})

    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    batch_count = len(IMPORT_BATCHES) + 1
    batch_id = f"JUNO-BATCH-{batch_count:04d}"

    new_batch = {
        "batch_id": batch_id,
        "file_name": filename,
        "original_filename": filename,
        "equipment": equipment_label,
        "report_type": detected_rtype,
        "records_count": valid_count,
        "valid_count": valid_count,
        "exception_count": exception_count,
        "sha256": sha256_hash,
        "status": "INGESTED",
        "imported_at": now_iso,
        "cloud_injected": cloud_injected,
        "asset_id": res.get("asset_id", "—"),
        "asset_code": asset_code,
        "plaza_id": res.get("plaza_id", "TP01"),
        "asset_breakdown": asset_breakdown,
    }
    IMPORT_BATCHES.insert(0, new_batch)

    cloud_note = " (Cloud Sync Active: Injected into Supabase)" if cloud_injected else " (Persisted to Runtime Store)"
    success_msg = (
        f"Successfully ingested {filename} into {equipment_label} pipeline [Asset: {asset_code}]: "
        f"{valid_count} clean interval readings, {exception_count} exceptions logged{cloud_note}."
    )
    log_audit_event(
        "JUNO_IMPORT_SUCCESS",
        f"Ingested {filename} ({equipment_label}, Asset: {asset_code}) under batch {batch_id}. Valid: {valid_count}, Cloud: {cloud_injected}",
        "BATCH",
        batch_id,
        "SUCCESS"
    )

    return {
        "status": "SUCCESS",
        "success": True,
        "message": success_msg,
        "batch_id": batch_id,
        "filename": filename,
        "original_filename": filename,
        "equipment": detected_rtype,
        "equipment_label": equipment_label,
        "asset_code": asset_code,
        "plaza_id": res.get("plaza_id", "TP01"),
        "records_count": total_records,
        "valid_count": valid_count,
        "exception_count": exception_count,
        "cloud_injected": cloud_injected,
        "sha256": sha256_hash,
        "asset_breakdown": asset_breakdown,
        "batch": new_batch,
        "details": {
            "valid_rows": valid_count,
            "exception_rows": exception_count,
            "cloud_injected": cloud_injected,
            "cloud_error": res.get("cloud_error"),
            "asset_id": res.get("asset_id"),
            "asset_code": asset_code,
            "plaza_id": res.get("plaza_id", "TP01"),
            "report_type": detected_rtype,
            "asset_breakdown": asset_breakdown,
        }
    }


@router.post("/upload")
async def import_juno_file(
    equipment: str = "AUTO",
    allow_reimport: bool = False,
    file: UploadFile = File(...),
) -> dict[str, Any]:
    """Single-file endpoint with auto-detection of equipment & asset code."""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    return _process_single_juno_upload(
        file.filename,
        content,
        equipment_param=equipment,
        allow_reimport=allow_reimport,
    )


@router.post("/upload-multi")
async def import_juno_multi_files(
    files: list[UploadFile] = File(...),
    equipment: str = "AUTO",
    allow_reimport: bool = False,
) -> dict[str, Any]:
    """Unified multi-file upload endpoint.
    Accepts multiple CSV/XLSX files simultaneously across DG, EB, Solar, Transformer, UPS.
    Automatically detects equipment type and asset codes per file and injects into Supabase & runtime store."""
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    file_results: list[dict[str, Any]] = []
    success_count = 0
    dup_count = 0
    fail_count = 0
    total_valid_rows = 0
    aggregated_asset_breakdown: dict[str, dict[str, Any]] = {}

    for f in files:
        content = await f.read()
        res = _process_single_juno_upload(
            f.filename,
            content,
            equipment_param=equipment,
            allow_reimport=allow_reimport,
        )
        status = res.get("status")

        if status == "SUCCESS":
            success_count += 1
            total_valid_rows += int(res.get("valid_count") or 0)
            for ac, b_info in res.get("asset_breakdown", {}).items():
                if ac not in aggregated_asset_breakdown:
                    aggregated_asset_breakdown[ac] = dict(b_info)
                else:
                    agg = aggregated_asset_breakdown[ac]
                    agg["count"] += b_info["count"]
                    if b_info.get("start_date") and (not agg.get("start_date") or b_info["start_date"] < agg["start_date"]):
                        agg["start_date"] = b_info["start_date"]
                    if b_info.get("last_date") and (not agg.get("last_date") or b_info["last_date"] > agg["last_date"]):
                        agg["last_date"] = b_info["last_date"]
        elif status == "DUPLICATE_REJECTED":
            dup_count += 1
        else:
            fail_count += 1

        file_results.append(res)

    overall_status = (
        "SUCCESS" if (fail_count == 0 and dup_count == 0 and success_count > 0)
        else ("PARTIAL" if success_count > 0
        else ("DUPLICATES_ONLY" if dup_count > 0 and fail_count == 0
        else "ERROR"))
    )

    summary_msg = (
        f"Processed {len(files)} files: {success_count} ingested successfully ({total_valid_rows} total records), "
        f"{dup_count} duplicate(s) rejected, {fail_count} failed."
    )

    return {
        "status": overall_status,
        "total_files": len(files),
        "successful": success_count,
        "duplicates": dup_count,
        "failed": fail_count,
        "total_valid_rows": total_valid_rows,
        "asset_breakdown": aggregated_asset_breakdown,
        "message": summary_msg,
        "file_results": file_results,
    }


@router.post("/reset")
@router.delete("/batches")
def reset_all_juno_data() -> dict[str, Any]:
    """
    Wipes all Juno telemetry reading data, import tracking, batches, and deduplication hashes
    across memory and Supabase cloud (if connected).
    Zero SQLite reliance. Preserves all master assets and toll plazas.
    """
    from core.live_pipeline import clear_local_ingestion_hashes
    from backend.services.energy_command_store import clear_runtime_readings
    from core.supabase_manager import get_supabase_client

    # 1. Clear in-memory state
    global IMPORT_BATCHES
    IMPORT_BATCHES.clear()
    clear_local_ingestion_hashes()
    clear_runtime_readings()

    # 2. Wipe Supabase if connected
    supabase_wiped = False
    client = get_supabase_client()
    if client:
        try:
            for s, t in [
                ("energy_readings", "eb"),
                ("energy_readings", "dg"),
                ("energy_readings", "solar"),
                ("energy_readings", "transformer"),
                ("energy_readings", "ups"),
                ("energy_validation", "exception_record"),
                ("energy_import", "import_row"),
                ("energy_import", "import_file"),
                ("energy_import", "import_batch"),
            ]:
                try:
                    client.schema(s).table(t).delete().neq("created_at", "1970-01-01").execute()
                except Exception:
                    pass
            supabase_wiped = True
        except Exception:
            pass

    return {
        "status": "SUCCESS",
        "message": "All Juno reading data, batches, and deduplication hashes successfully wiped from memory and Supabase.",
        "supabase_wiped": supabase_wiped,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    return {
        "status": "SUCCESS",
        "message": "All Juno reading data, batches, and deduplication hashes successfully wiped from memory and Supabase.",
        "supabase_wiped": supabase_wiped,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

