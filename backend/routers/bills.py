import io
import os
import sys
import time
import json
import tempfile
import shutil
from typing import Any
from concurrent.futures import ThreadPoolExecutor
import pdfplumber
import pandas as pd
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "active_app"))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from bill_extractor.extractor_main_full import extract_energy_bill_full
from bill_extractor.extractor_md_full import extract_md_bill_data
from bill_extractor.extractor_receipt_full import extract_energy_receipt_data
from bill_extractor.merge_clean_core import merge_and_clean_dataframes
from bill_extractor.verifier import verify_bill_calculations
from bill_extractor.zip_handler import extract_pdfs_from_inputs

from core.db_sync import (
    get_all_energy_bills,
    get_official_bill_register,
    get_bill_review_queue,
    save_to_review_queue,
    verify_and_post_bill,
    void_posted_bill,
    delete_held_draft,
    save_energy_bill,
    save_payment_receipt,
    get_existing_bill_numbers,
    get_existing_receipt_numbers,
    get_receipt_reconciliation,
    allocate_receipt_to_bill,
    log_audit_event,
    _clean_kpi_num,
)

router = APIRouter(prefix="/api/bills", tags=["Bills"])


class AllocateReceiptPayload(BaseModel):
    receipt_no: str
    bill_number: str
    allocation_amount: float
    notes: str = ""


class ReviewResolutionPayload(BaseModel):
    corrections: dict[str, Any] | None = None


def _extract_single_item(item_tuple: tuple[int, Any]) -> dict[str, Any]:
    """Helper to extract bill/receipt text and metadata in a worker thread."""
    idx, item = item_tuple
    if isinstance(item, tuple) and len(item) == 2:
        fname, raw_bytes = item
    elif isinstance(item, dict):
        fname = item.get("name") or f"file_{idx}.pdf"
        raw_bytes = item.get("content") or item.get("raw_bytes") or b""
    else:
        fname = getattr(item, "name", None) or f"file_{idx}.pdf"
        if hasattr(item, "getvalue"):
            raw_bytes = item.getvalue()
        elif hasattr(item, "read"):
            if hasattr(item, "seek"):
                item.seek(0)
            raw_bytes = item.read()
        else:
            raw_bytes = bytes(item) if item else b""

    is_receipt = any(k in fname.lower() for k in ["receipt", "payment", "utr", "challan"])

    if is_receipt:
        try:
            stream_receipt = io.BytesIO(raw_bytes)
            stream_receipt.name = fname
            rec = extract_energy_receipt_data(stream_receipt, fname)
            rec_no = str(rec.get("receipt_no") or f"RCP-{idx}").strip()
            amt = _clean_kpi_num(rec.get("amount_paid") or rec.get("amount"))
            return {
                "idx": idx,
                "file": fname,
                "kind": "Receipt",
                "consumer": str(rec.get("account_no") or rec.get("consumer_no") or "—"),
                "month": str(rec.get("bill_month") or "—"),
                "identifier": rec_no,
                "amount": amt,
                "payload": rec,
                "is_receipt": True,
                "error": None,
            }
        except Exception as e:
            return {
                "idx": idx,
                "file": fname,
                "kind": "Receipt",
                "consumer": "—",
                "month": "—",
                "identifier": f"RCP-{idx}",
                "amount": 0.0,
                "payload": {},
                "is_receipt": True,
                "error": str(e),
            }

    # Bill Extraction (Single-pass PDF text extraction for max performance)
    try:
        extracted_text = ""
        try:
            with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
                if pdf.pages:
                    extracted_text = pdf.pages[0].extract_text() or ""
        except Exception:
            extracted_text = ""

        stream_main = io.BytesIO(raw_bytes)
        stream_main.name = fname
        stream_md = io.BytesIO(raw_bytes)
        stream_md.name = fname

        bill_main = extract_energy_bill_full(stream_main, fname, extracted_text=extracted_text)
        bill_md = extract_md_bill_data(stream_md, fname, extracted_text=extracted_text)
        cleaned_df = merge_and_clean_dataframes(bill_main, bill_md, raw_bytes=raw_bytes, filename=fname)
        bill_dict = cleaned_df.iloc[0].to_dict() if not cleaned_df.empty else {**bill_main, **bill_md}
        if "raw_text" not in bill_dict and "raw_text" in bill_main:
            bill_dict["raw_text"] = bill_main["raw_text"]
        elif "raw_text" not in bill_dict and extracted_text:
            bill_dict["raw_text"] = extracted_text

        v_res = verify_bill_calculations(bill_dict, raw_text=bill_dict.get("raw_text", ""))

        # Enrich with calculation checks
        bill_dict["Cal Energy Charges"] = v_res.get("cal_energy_charges", 0.0)
        bill_dict["Energy Charges Check"] = "MATCH ✓" if v_res.get("match_energy_charges") else "MISMATCH ⚠️"
        bill_dict["Cal Electricity Charges"] = v_res.get("cal_electricity_charges", 0.0)
        bill_dict["Electricity Charges Check"] = "MATCH ✓" if v_res.get("match_electricity_charges") else "MISMATCH ⚠️"
        bill_dict["Cal Current Total"] = v_res.get("cal_current_total", 0.0)
        bill_dict["Current Total Check"] = "MATCH ✓" if v_res.get("match_current_total") else "MISMATCH ⚠️"
        bill_dict["Audit Verdict"] = v_res.get("audit_status", "AUDIT REQUIRED ⚠️")

        b_no = str(bill_dict.get("Bill Number") or bill_dict.get("bill_number") or f"BILL-{idx}").strip()
        ac_no = str(bill_dict.get("Consumer A/c No.") or bill_dict.get("consumer_account_no") or "—").strip()
        b_mo = str(bill_dict.get("Bill Month") or bill_dict.get("bill_month") or "—").strip()
        amt = _clean_kpi_num(
            bill_dict.get("Net Payable Amount Before Rbt. Dt.(Rs.)")
            or bill_dict.get("total_amount_payable")
            or bill_dict.get("Current Total (o)")
            or bill_dict.get("current_total")
        )
        b_basis = str(bill_dict.get("Bill Basis") or bill_dict.get("bill_basis") or "ACTUAL").strip().upper()

        return {
            "idx": idx,
            "file": fname,
            "kind": "Bill",
            "consumer": ac_no,
            "month": b_mo,
            "identifier": b_no,
            "amount": amt,
            "basis": b_basis,
            "verifier_result": v_res,
            "payload": bill_dict,
            "is_receipt": False,
            "error": None,
        }
    except Exception as e:
        return {
            "idx": idx,
            "file": fname,
            "kind": "Bill",
            "consumer": "—",
            "month": "—",
            "identifier": f"BILL-{idx}",
            "amount": 0.0,
            "basis": "UNKNOWN",
            "verifier_result": {},
            "payload": {},
            "is_receipt": False,
            "error": str(e),
        }


@router.post("/upload")
async def upload_and_process_bills(files: list[UploadFile] = File(...)):
    """Accepts multiple PDF bills/receipts or ZIP archives, extracts in parallel, audits, and rejects duplicates."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    # Convert uploaded files into format expected by extract_pdfs_from_inputs
    wrapped_files = []
    for f in files:
        content = await f.read()
        b_io = io.BytesIO(content)
        b_io.name = f.filename
        wrapped_files.append(b_io)

    unpacked_items = extract_pdfs_from_inputs(wrapped_files)
    if not unpacked_items:
        return {"processed": 0, "candidates": []}

    # Parallel extraction across available CPU workers
    workers_count = min(4, os.cpu_count() or 4, len(unpacked_items))
    indexed_items = [(idx, item) for idx, item in enumerate(unpacked_items)]

    with ThreadPoolExecutor(max_workers=workers_count) as executor:
        extracted_data = list(executor.map(_extract_single_item, indexed_items))

def _process_candidate(
    item: dict[str, Any],
    existing_bills: set[str],
    existing_receipts: set[str],
    seen_bills_in_batch: set[str],
    seen_receipts_in_batch: set[str],
    stats: dict[str, int],
) -> dict[str, Any]:
    """Applies duplicate checks, validates formulas, and saves structured metadata (NO PDF files in DB)."""
    fname = item["file"]
    is_receipt = item["is_receipt"]
    err = item["error"]

    if err:
        stats["failed"] += 1
        return {
            "file": fname,
            "kind": item["kind"],
            "consumer": item["consumer"],
            "month": item["month"],
            "detail": f"Extraction Failed: {err}",
            "amount": 0.0,
            "result": "FAILED",
            "payload": {},
        }

    if is_receipt:
        rec_no = item["identifier"]
        rec = item["payload"]
        amt = item["amount"]

        # Ensure NO raw file bytes in database
        rec.pop("raw_bytes", None)
        rec.pop("content", None)

        if rec_no in existing_receipts or rec_no in seen_receipts_in_batch:
            stats["duplicates_rejected"] += 1
            log_audit_event("DUPLICATE_REJECTED", f"Receipt {rec_no} rejected as duplicate", "RECEIPT", rec_no, "REJECTED")
            return {
                "file": fname,
                "kind": "Receipt",
                "consumer": item["consumer"],
                "month": item["month"],
                "detail": f"DUPLICATE REJECTED · Receipt #{rec_no} already exists in database",
                "amount": amt,
                "result": "DUPLICATE_REJECTED",
                "payload": rec,
            }
        else:
            seen_receipts_in_batch.add(rec_no)
            save_payment_receipt(rec, prevent_duplicates=True)
            stats["verified"] += 1
            return {
                "file": fname,
                "kind": "Receipt",
                "consumer": item["consumer"],
                "month": item["month"],
                "detail": f"Receipt {rec_no} Registered",
                "amount": amt,
                "result": "EXTRACTED",
                "payload": rec,
            }
    else:
        b_no = item["identifier"]
        ac_no = item["consumer"]
        b_mo = item["month"]
        amt = item["amount"]
        b_basis = item["basis"]
        bill_dict = item["payload"]
        v_res = item["verifier_result"]

        # Ensure NO raw file bytes in database
        bill_dict.pop("raw_bytes", None)
        bill_dict.pop("content", None)
        bill_dict.pop("raw_content", None)

        if b_no in existing_bills or b_no in seen_bills_in_batch:
            stats["duplicates_rejected"] += 1
            log_audit_event("DUPLICATE_REJECTED", f"Bill {b_no} rejected as duplicate", "BILL", b_no, "REJECTED")
            return {
                "file": fname,
                "kind": "Bill",
                "consumer": ac_no,
                "month": b_mo,
                "detail": f"DUPLICATE REJECTED · Bill #{b_no} already registered in database",
                "amount": amt,
                "result": "DUPLICATE_REJECTED",
                "payload": bill_dict,
            }
        else:
            seen_bills_in_batch.add(b_no)

            if b_basis in ["AVERAGE", "PROVISIONAL"]:
                clean_payload = {k: v for k, v in bill_dict.items() if not isinstance(v, (bytes, bytearray))}
                save_to_review_queue({
                    "bill_number": b_no,
                    "consumer_account_no": ac_no,
                    "bill_month": b_mo,
                    "bill_basis": b_basis,
                    "amount": amt,
                    "exception_reason": f"{b_basis.capitalize()} bill basis held for review",
                    "hold_reason_code": "PROVISIONAL_AVERAGE_AUDIT",
                    "source_filename": fname,
                    "raw_payload": clean_payload,
                }, prevent_duplicates=True)
                stats["review"] += 1
                return {
                    "file": fname,
                    "kind": "Bill",
                    "consumer": ac_no,
                    "month": b_mo,
                    "detail": f"{b_basis} · {b_no} Held in Review Queue",
                    "amount": amt,
                    "result": "REVIEW",
                    "payload": bill_dict,
                }
            elif not v_res.get("is_valid", False) and v_res.get("audit_status") != "VERIFIED ✓":
                mismatch_reason = v_res.get("mismatch_reason") or "Formula calculation mismatch"
                clean_payload = {k: v for k, v in bill_dict.items() if not isinstance(v, (bytes, bytearray))}
                save_to_review_queue({
                    "bill_number": b_no,
                    "consumer_account_no": ac_no,
                    "bill_month": b_mo,
                    "bill_basis": b_basis,
                    "amount": amt,
                    "exception_reason": f"Calculation mismatch: {mismatch_reason}",
                    "hold_reason_code": "ARITHMETIC_MISMATCH",
                    "source_filename": fname,
                    "raw_payload": clean_payload,
                }, prevent_duplicates=True)
                stats["review"] += 1
                return {
                    "file": fname,
                    "kind": "Bill",
                    "consumer": ac_no,
                    "month": b_mo,
                    "detail": f"MISMATCH · {b_no} Held in Review Queue",
                    "amount": amt,
                    "result": "REVIEW",
                    "payload": bill_dict,
                }
            else:
                save_energy_bill(bill_dict, v_res, prevent_duplicates=True)
                log_audit_event("AUTO_POSTED", f"Bill {b_no} verified and posted", "BILL", b_no, "POSTED")
                stats["verified"] += 1
                return {
                    "file": fname,
                    "kind": "Bill",
                    "consumer": ac_no,
                    "month": b_mo,
                    "detail": f"ACTUAL · {b_no} Verified & Posted",
                    "amount": amt,
                    "result": "VERIFIED",
                    "payload": bill_dict,
                }


@router.post("/upload")
async def upload_and_process_bills(files: list[UploadFile] = File(...)):
    """Accepts multiple PDF bills/receipts or ZIP archives, extracts in parallel, audits, and rejects duplicates.
    Files are stored temporarily on disk and immediately deleted after extraction.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    temp_dir = tempfile.mkdtemp(prefix="srtpl_bill_extract_")
    try:
        temp_file_paths = []
        for f in files:
            t_path = os.path.join(temp_dir, f.filename)
            content = await f.read()
            with open(t_path, "wb") as out_fp:
                out_fp.write(content)
            temp_file_paths.append(t_path)

        unpacked_items = extract_pdfs_from_inputs(temp_file_paths)
        if not unpacked_items:
            return {"processed": 0, "candidates": []}

        # Parallel extraction across available CPU workers
        workers_count = min(4, os.cpu_count() or 4, len(unpacked_items))
        indexed_items = [(idx, item) for idx, item in enumerate(unpacked_items)]

        with ThreadPoolExecutor(max_workers=workers_count) as executor:
            extracted_data = list(executor.map(_extract_single_item, indexed_items))

        # Pre-fetch existing database identifiers for instant O(1) duplicate rejection
        existing_bills = get_existing_bill_numbers()
        existing_receipts = get_existing_receipt_numbers()

        seen_bills_in_batch: set[str] = set()
        seen_receipts_in_batch: set[str] = set()

        results = []
        stats = {"verified": 0, "review": 0, "duplicates_rejected": 0, "failed": 0}

        for item in extracted_data:
            cand = _process_candidate(
                item, existing_bills, existing_receipts, seen_bills_in_batch, seen_receipts_in_batch, stats
            )
            results.append(cand)

        return {
            "processed": len(results),
            "verified": stats["verified"],
            "review": stats["review"],
            "duplicates_rejected": stats["duplicates_rejected"],
            "failed": stats["failed"],
            "candidates": results,
        }
    finally:
        # STRICT CLEANUP: Purge all temporary files from server
        shutil.rmtree(temp_dir, ignore_errors=True)


@router.post("/upload-stream")
async def upload_and_process_bills_stream(files: list[UploadFile] = File(...)):
    """Accepts PDF bills/receipts or ZIP archives, unpacks into temporary storage,
    and streams real-time extraction progress per bill as NDJSON:
      {"type": "item_progress", "current": 1, "total": 10, "file": "bill1.pdf", "candidate": {...}}
      ...
      {"type": "complete", "total": 10, "verified": 8, "review": 1, "duplicates_rejected": 1, "failed": 0, "candidates": [...]}
    After extraction, all temporary storage is strictly wiped and purged.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    temp_dir = tempfile.mkdtemp(prefix="srtpl_bill_stream_")

    async def stream_generator():
        try:
            temp_file_paths = []
            for f in files:
                t_path = os.path.join(temp_dir, f.filename)
                content = await f.read()
                with open(t_path, "wb") as out_fp:
                    out_fp.write(content)
                temp_file_paths.append(t_path)

            unpacked_items = extract_pdfs_from_inputs(temp_file_paths)
            total_count = len(unpacked_items)

            if total_count == 0:
                yield json.dumps({
                    "type": "complete",
                    "total": 0,
                    "verified": 0,
                    "review": 0,
                    "duplicates_rejected": 0,
                    "failed": 0,
                    "candidates": [],
                }) + "\n"
                return

            yield json.dumps({
                "type": "start",
                "total": total_count,
                "message": f"Found {total_count} documents to extract.",
            }) + "\n"

            existing_bills = get_existing_bill_numbers()
            existing_receipts = get_existing_receipt_numbers()

            seen_bills_in_batch: set[str] = set()
            seen_receipts_in_batch: set[str] = set()

            results = []
            stats = {"verified": 0, "review": 0, "duplicates_rejected": 0, "failed": 0}

            for idx, item in enumerate(unpacked_items):
                extracted_item = _extract_single_item((idx, item))
                cand = _process_candidate(
                    extracted_item, existing_bills, existing_receipts, seen_bills_in_batch, seen_receipts_in_batch, stats
                )
                results.append(cand)

                # Stream progress for each individual bill extracted
                yield json.dumps({
                    "type": "item_progress",
                    "current": idx + 1,
                    "total": total_count,
                    "file": cand["file"],
                    "result": cand["result"],
                    "detail": cand["detail"],
                    "candidate": cand,
                }) + "\n"

            # Stream completion summary
            yield json.dumps({
                "type": "complete",
                "total": total_count,
                "verified": stats["verified"],
                "review": stats["review"],
                "duplicates_rejected": stats["duplicates_rejected"],
                "failed": stats["failed"],
                "candidates": results,
            }) + "\n"

        finally:
            # STRICT CLEANUP: Purge all temporary files from server
            shutil.rmtree(temp_dir, ignore_errors=True)

    return StreamingResponse(stream_generator(), media_type="application/x-ndjson")


@router.get("/register")
def get_register(toll_plaza: str = "ALL", bill_month: str = "ALL", bill_type: str = "ALL"):
    reg_df = get_official_bill_register()
    if reg_df.empty:
        return {"count": 0, "bills": []}

    if toll_plaza != "ALL" and "toll_plaza_id" in reg_df.columns:
        reg_df = reg_df[reg_df["toll_plaza_id"] == toll_plaza]
    if bill_month != "ALL" and "bill_month" in reg_df.columns:
        reg_df = reg_df[reg_df["bill_month"] == bill_month]
    if bill_type != "ALL" and "bill_type" in reg_df.columns:
        reg_df = reg_df[reg_df["bill_type"] == bill_type]

    return {"count": len(reg_df), "bills": reg_df.to_dict(orient="records")}


@router.get("/review-queue")
def get_review_queue():
    q_df = get_bill_review_queue()
    if q_df.empty:
        return {"count": 0, "items": []}
    return {"count": len(q_df), "items": q_df.to_dict(orient="records")}


@router.post("/review-queue/{candidate_id}/verify-and-post")
def post_review_candidate(candidate_id: str, payload: ReviewResolutionPayload):
    res = verify_and_post_bill(candidate_id, payload.corrections)
    return res


@router.post("/review-queue/{candidate_id}/delete")
def delete_review_candidate(candidate_id: str):
    res = delete_held_draft(candidate_id)
    return res


@router.post("/register/{bill_number}/void")
def void_bill(bill_number: str, reason: str = "Voided by operator"):
    res = void_posted_bill(bill_number, reason)
    return res


@router.get("/receipts")
def get_receipts():
    r_df = get_receipt_reconciliation()
    if r_df.empty:
        return {"count": 0, "receipts": []}
    return {"count": len(r_df), "receipts": r_df.to_dict(orient="records")}


@router.post("/receipts/allocate")
def allocate_receipt(payload: AllocateReceiptPayload):
    res = allocate_receipt_to_bill(
        payload.receipt_no,
        payload.bill_number,
        payload.allocation_amount,
        payload.notes,
    )
    return res
