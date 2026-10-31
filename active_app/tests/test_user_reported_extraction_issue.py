import io
import os
import pandas as pd
import pytest

from bill_extractor.extractor_main_full import extract_energy_bill_full
from bill_extractor.extractor_md_full import extract_md_bill_data
from bill_extractor.merge_clean_core import merge_and_clean_dataframes
from bill_extractor.verifier import verify_bill_calculations
from core.db_sync import format_bill_for_db, save_energy_bill, save_to_review_queue


def test_merge_and_clean_dataframes_with_raw_bytes_and_filename_kwargs():
    """Verify merge_and_clean_dataframes handles raw_bytes and filename keyword arguments without raising TypeError."""
    fname = "source_data/user_uploaded_bills/extractor/411001070208_82025_EN.pdf"
    if not os.path.exists(fname):
        pytest.skip(f"Test PDF not found at {fname}")

    with open(fname, "rb") as f:
        raw_bytes = f.read()

    stream_main = io.BytesIO(raw_bytes)
    stream_md = io.BytesIO(raw_bytes)

    bill_main = extract_energy_bill_full(stream_main, "411001070208_82025_EN.pdf")
    bill_md = extract_md_bill_data(stream_md, "411001070208_82025_EN.pdf")

    # Call merge_and_clean_dataframes directly with dictionaries and kwargs (as happened in UI)
    cleaned_df = merge_and_clean_dataframes(bill_main, bill_md, raw_bytes=raw_bytes, filename="411001070208_82025_EN.pdf")

    assert not cleaned_df.empty
    assert len(cleaned_df) == 1
    assert "Bill Number" in cleaned_df.columns
    assert "Consumer A/c No." in cleaned_df.columns
    assert "Bill Month" in cleaned_df.columns
    assert "MD-KW" in cleaned_df.columns
    assert "MD-KVA" in cleaned_df.columns
    assert "Source PDF" in cleaned_df.columns

    bill_dict = cleaned_df.iloc[0].to_dict()
    bill_dict["raw_text"] = bill_main.get("raw_text", "")

    # Perform calculations and verification
    v_res = verify_bill_calculations(bill_dict, raw_text=bill_dict.get("raw_text", ""))
    assert v_res["is_valid"] is True
    assert v_res["audit_status"] == "VERIFIED ✓"

    # Verify database formatting
    db_payload = format_bill_for_db(bill_dict, v_res)
    assert db_payload["bill_number"] == "411010709251615163"
    assert db_payload["consumer_account_no"] == "411001070208"
    assert db_payload["bill_month"] == "2025/08"
    assert db_payload["verification_status"] == "VERIFIED_MATCH"
    assert db_payload["total_amount_payable"] > 0

    # Save to energy_bills
    save_res = save_energy_bill(bill_dict, v_res)
    assert save_res["bill_number"] == "411010709251615163"


def test_mismatch_routing_to_review_queue():
    """Verify that calculation mismatches route to save_to_review_queue."""
    mismatched_bill = {
        "Bill Number": "BILL-TEST-MISM",
        "Consumer A/c No.": "411001070208",
        "Bill Month": "2026/05",
        "Bill Basis": "ACTUAL",
        "Current Total (o)": 99999.0,  # Deliberate mismatch
        "a. Energy Charges": 100.0,
        "Electricity Charge (i)": 100.0,
    }

    v_res = verify_bill_calculations(mismatched_bill)
    assert v_res["is_valid"] is False

    res = save_to_review_queue({
        "bill_number": mismatched_bill["Bill Number"],
        "consumer_account_no": mismatched_bill["Consumer A/c No."],
        "bill_month": mismatched_bill["Bill Month"],
        "bill_basis": mismatched_bill["Bill Basis"],
        "amount": mismatched_bill["Current Total (o)"],
        "exception_reason": f"Calculation mismatch: {v_res.get('mismatch_reason')}",
        "hold_reason_code": "ARITHMETIC_MISMATCH",
        "source_filename": "test_mismatch.pdf",
        "raw_payload": mismatched_bill,
    })
    assert res["status"] == "SUCCESS"
    assert res["candidate_id"].startswith("REV-")
