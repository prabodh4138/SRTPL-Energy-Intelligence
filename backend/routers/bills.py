import io
import os
import sys
import time
from typing import Any
import pandas as pd
from fastapi import APIRouter, File, UploadFile, HTTPException
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


@router.post("/upload")
async def upload_and_process_bills(files: list[UploadFile] = File(...)):
    """Accepts multiple PDF bills/receipts or ZIP archives, extracts, cleans, audits, and routes."""
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
    results = []

    for idx, item in enumerate(unpacked_items):
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

        stream_receipt = io.BytesIO(raw_bytes)
        stream_receipt.name = fname
        stream_main = io.BytesIO(raw_bytes)
        stream_main.name = fname
        stream_md = io.BytesIO(raw_bytes)
        stream_md.name = fname

        is_receipt = any(k in fname.lower() for k in ["receipt", "payment", "utr", "challan"])

        if is_receipt:
            try:
                rec = extract_energy_receipt_data(stream_receipt, fname)
                rec_no = rec.get("receipt_no") or f"RCP-{idx}"
                amt = _clean_kpi_num(rec.get("amount_paid") or rec.get("amount"))
                save_payment_receipt(rec)
                results.append({
                    "file": fname,
                    "kind": "Receipt",
                    "consumer": str(rec.get("account_no") or rec.get("consumer_no") or "—"),
                    "month": str(rec.get("bill_month") or "—"),
                    "detail": f"Receipt {rec_no}",
                    "amount": amt,
                    "result": "EXTRACTED",
                    "payload": rec,
                })
            except Exception as e:
                results.append({
                    "file": fname,
                    "kind": "Receipt",
                    "consumer": "—",
                    "month": "—",
                    "detail": str(e),
                    "amount": 0.0,
                    "result": "FAILED",
                    "payload": {},
                })
        else:
            try:
                bill_main = extract_energy_bill_full(stream_main, fname)
                bill_md = extract_md_bill_data(stream_md, fname)
                cleaned_df = merge_and_clean_dataframes(bill_main, bill_md, raw_bytes=raw_bytes, filename=fname)
                bill_dict = cleaned_df.iloc[0].to_dict() if not cleaned_df.empty else {**bill_main, **bill_md}
                if "raw_text" not in bill_dict and "raw_text" in bill_main:
                    bill_dict["raw_text"] = bill_main["raw_text"]

                v_res = verify_bill_calculations(bill_dict, raw_text=bill_dict.get("raw_text", ""))

                # Enrich with calculations
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

                if b_basis in ["AVERAGE", "PROVISIONAL"]:
                    save_to_review_queue({
                        "bill_number": b_no,
                        "consumer_account_no": ac_no,
                        "bill_month": b_mo,
                        "bill_basis": b_basis,
                        "amount": amt,
                        "exception_reason": f"{b_basis.capitalize()} bill basis held for review",
                        "hold_reason_code": "PROVISIONAL_AVERAGE_AUDIT",
                        "source_filename": fname,
                        "raw_payload": bill_dict,
                    })
                    results.append({
                        "file": fname, "kind": "Bill", "consumer": ac_no, "month": b_mo,
                        "detail": f"{b_basis} · {b_no}", "amount": amt, "result": "REVIEW", "payload": bill_dict
                    })
                elif not v_res.get("is_valid", False) and v_res.get("audit_status") != "VERIFIED ✓":
                    mismatch_reason = v_res.get("mismatch_reason") or "Formula calculation mismatch"
                    save_to_review_queue({
                        "bill_number": b_no,
                        "consumer_account_no": ac_no,
                        "bill_month": b_mo,
                        "bill_basis": b_basis,
                        "amount": amt,
                        "exception_reason": f"Calculation mismatch: {mismatch_reason}",
                        "hold_reason_code": "ARITHMETIC_MISMATCH",
                        "source_filename": fname,
                        "raw_payload": bill_dict,
                    })
                    results.append({
                        "file": fname, "kind": "Bill", "consumer": ac_no, "month": b_mo,
                        "detail": f"MISMATCH · {b_no}", "amount": amt, "result": "REVIEW", "payload": bill_dict
                    })
                else:
                    save_energy_bill(bill_dict, v_res)
                    log_audit_event("AUTO_POSTED", f"Bill {b_no} verified and posted", "BILL", b_no, "POSTED")
                    results.append({
                        "file": fname, "kind": "Bill", "consumer": ac_no, "month": b_mo,
                        "detail": f"ACTUAL · {b_no}", "amount": amt, "result": "VERIFIED", "payload": bill_dict
                    })
            except Exception as e:
                results.append({
                    "file": fname, "kind": "Bill", "consumer": "—", "month": "—",
                    "detail": str(e), "amount": 0.0, "result": "FAILED", "payload": {}
                })

    return {"processed": len(results), "candidates": results}


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
