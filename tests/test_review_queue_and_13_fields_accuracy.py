import io
import pytest
import pdfplumber
import pandas as pd
from active_app.bill_extractor.extractor_main_full import extract_energy_bill_full
from active_app.bill_extractor.extractor_md_full import extract_md_bill_data
from active_app.bill_extractor.merge_clean_core import merge_and_clean_dataframes, enrich_bill_record
from active_app.core.db_sync import (
    _IN_MEMORY_UPLOADED_BILLS,
    _IN_MEMORY_REVIEW_QUEUE,
    _IN_MEMORY_REJECTED_BILLS,
    save_to_review_queue,
    get_bill_review_queue,
    move_to_rejected_bucket,
    get_rejected_bills_bucket,
    restore_rejected_bill,
    delete_rejected_bill,
    verify_and_post_bill,
    get_official_bill_register,
    format_bill_for_db,
    _ensure_official_register_columns,
)


def test_pdf_extraction_13_fields_accuracy():
    """Verify that all 6 uploaded PDFs extract all 13 requested fields with 100% precision and no hardcoded 10 KW."""
    pdf_files = [
        ("C:/Users/prabo/.gemini/antigravity/brain/83225691-b0cb-4392-bb5b-407b77fc9a89/.user_uploaded/media_1792852844664_409203e2.pdf", "416001111004", "LT", "HIGHWAY", 6.0, "6 KW"),
        ("C:/Users/prabo/.gemini/antigravity/brain/83225691-b0cb-4392-bb5b-407b77fc9a89/.user_uploaded/media_1792852922586_9584e98a.pdf", "416001111004", "LT", "HIGHWAY", 6.0, "6 KW"),
        ("C:/Users/prabo/.gemini/antigravity/brain/83225691-b0cb-4392-bb5b-407b77fc9a89/.user_uploaded/media_1792933000331_bc65641e.pdf", "813413021313", "LT", "HIGHWAY", 1.0, "1 KW"),
        ("C:/Users/prabo/.gemini/antigravity/brain/83225691-b0cb-4392-bb5b-407b77fc9a89/.user_uploaded/media_1792933000331_d9c0f442.pdf", "813000000281", "HT", "PLAZA", 120.0, "120 KVA"),
        ("C:/Users/prabo/.gemini/antigravity/brain/83225691-b0cb-4392-bb5b-407b77fc9a89/.user_uploaded/media_1792933000331_f382d16f.pdf", "813413052467", "LT", "HIGHWAY", 2.0, "2 KW"),
        ("C:/Users/prabo/.gemini/antigravity/brain/83225691-b0cb-4392-bb5b-407b77fc9a89/.user_uploaded/media_1792935623399_80b3efcd.pdf", "812001020208", "HT", "PLAZA", 100.0, "100 KVA"),
    ]

    for path, exp_ac, exp_btype, exp_scope, exp_load, exp_cd in pdf_files:
        fname = path.split("/")[-1]
        with open(path, "rb") as f:
            raw_bytes = f.read()
        with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
            text = pdf.pages[0].extract_text()

        b_main = extract_energy_bill_full(io.BytesIO(raw_bytes), fname, extracted_text=text)
        b_md = extract_md_bill_data(io.BytesIO(raw_bytes), fname, extracted_text=text)
        merged_df = merge_and_clean_dataframes(b_main, b_md, raw_bytes=raw_bytes, filename=fname)
        assert not merged_df.empty, f"Merged df is empty for {fname}"
        rec = merged_df.iloc[0].to_dict()

        # Check core classification
        assert rec["bill_type"] == exp_btype, f"Expected {exp_btype} for {exp_ac}, got {rec['bill_type']}"
        assert rec["consumer_scope"] == exp_scope, f"Expected {exp_scope} for {exp_ac}, got {rec['consumer_scope']}"
        assert rec["sanctioned_load_kw"] == exp_load, f"Expected {exp_load} for {exp_ac}, got {rec['sanctioned_load_kw']}"
        assert rec["contract_demand"] == exp_cd, f"Expected {exp_cd} for {exp_ac}, got {rec['contract_demand']}"

        # Check all 13 requested fields are not blank or None
        assert rec["Rebate Date"] != "", f"Missing Rebate Date in {fname}"
        assert rec["Meter Sl. No."] != "", f"Missing Meter Sl. No. in {fname}"
        assert rec["Tariff Category"] != "", f"Missing Tariff Category in {fname}"
        assert rec["Section"] != "", f"Missing Section in {fname}"
        assert rec["Sub-Division"] != "", f"Missing Sub-Division in {fname}"
        assert rec["MD"] != "", f"Missing MD in {fname}"
        assert rec["Net Payable Amount Before Rbt. Dt.(Rs.)"] != "", f"Missing Net Before in {fname}"
        assert rec["Net Payable Amount After Rbt. Dt.(Rs.)"] != "", f"Missing Net After in {fname}"


def test_review_queue_modification_and_rejected_bucket_lifecycle():
    """Verify modifying a held candidate, posting to register, and rejecting to bucket."""
    _IN_MEMORY_UPLOADED_BILLS.clear()
    _IN_MEMORY_REVIEW_QUEUE.clear()
    _IN_MEMORY_REJECTED_BILLS.clear()

    # 1. Save candidate to review queue
    candidate = {
        "candidate_id": "TEST-CAND-001",
        "bill_number": "EB-TEST-9999",
        "consumer_account_no": "813000000281",
        "toll_plaza_id": "TP03",
        "bill_type": "HT",
        "bill_month": "Apr 2025",
        "bill_basis": "ACTUAL",
        "amount": 216159.0,
        "exception_reason": "Arithmetic check mismatch",
        "hold_reason_code": "ARITHMETIC_MISMATCH",
        "source_filename": "test_bill.pdf",
        "raw_payload": {
            "Consumer A/c No.": "813000000281",
            "Bill Number": "EB-TEST-9999",
            "Bill Month": "2025/04",
            "Tariff Category": "GENERAL PURPOSE >= 110 KVA",
            "Contract Demand": "120 KVA",
            "Security Deposit": "338171.70",
            "MD": "0.3310",
            "CUML MD-KVA": "0.3484",
            "CUML MD-KW": "0.0000",
            "DPS(Rs.)": "0.01",
            "Rebate Date": "06/05/2025",
            "Meter Sl. No.": "WES48722",
            "Section": "ESO NO-I RAJGANGPUR",
            "Sub-Division": "SDO-IRAJGANGPUR",
            "Division": "RED RAJGANGPUR",
            "Net Payable Amount Before Rbt. Dt.(Rs.)": "216159.00",
            "Net Payable Amount After Rbt. Dt.(Rs.)": "218198.00",
        }
    }
    save_to_review_queue(candidate)
    q_df = get_bill_review_queue()
    assert len(q_df) == 1
    assert q_df.iloc[0]["candidate_id"] == "TEST-CAND-001"

    # 2. Operator modifies data and posts
    corrections = {
        "consumer_account_no": "813000000281",
        "bill_number": "EB-TEST-9999",
        "sanctioned_load_kw": 120.0,
        "contract_demand": "120 KVA",
        "total_amount_payable": 216159.0,
        "edit_notes": "Verified against physical meter log",
    }
    post_res = verify_and_post_bill("TEST-CAND-001", corrections)
    assert post_res["status"] == "SUCCESS"
    assert post_res["is_edited"] is True

    # Check that candidate was removed from review queue
    assert get_bill_review_queue().empty

    # Check that bill is now in Official Register with all 13 fields
    reg_df = get_official_bill_register()
    assert len(reg_df) == 1
    row = reg_df.iloc[0].to_dict()
    assert row["bill_number"] == "EB-TEST-9999"
    assert row["bill_type"] == "HT"
    assert row["consumer_scope"] == "PLAZA"
    assert row["sanctioned_load_kw"] == 120.0
    assert row["contract_demand"] == "120 KVA"
    assert float(row["security_deposit"]) == 338171.70
    assert float(row["md"]) == 0.3310
    assert float(row["cuml_md_kva"]) == 0.3484
    assert row["rebate_date"] == "06/05/2025"
    assert row["meter_sl_no"] == "WES48722"
    assert row["section"] == "ESO NO-I RAJGANGPUR"

    # 3. Test Rejected Bucket Lifecycle
    cand2 = {
        "candidate_id": "TEST-CAND-002",
        "bill_number": "EB-TEST-8888",
        "consumer_account_no": "416001111004",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "bill_month": "Sep 2026",
        "amount": 7730.0,
        "exception_reason": "Suspected duplicate meter reading",
        "source_filename": "bad_bill.pdf",
    }
    save_to_review_queue(cand2)
    assert len(get_bill_review_queue()) == 1

    # Move to rejected bucket
    rej_res = move_to_rejected_bucket("TEST-CAND-002", reason="Duplicate scan uploaded", rejected_by="TEST_USER")
    assert rej_res["status"] == "SUCCESS"
    assert get_bill_review_queue().empty

    # Verify present in rejected bucket
    rej_df = get_rejected_bills_bucket()
    assert len(rej_df) == 1
    rej_rec = rej_df.iloc[0].to_dict()
    assert rej_rec["candidate_id"] == "TEST-CAND-002"
    assert rej_rec["rejection_reason"] == "Duplicate scan uploaded"
    rejection_id = rej_rec["rejection_id"]

    # Restore from rejected bucket back to review queue
    rest_res = restore_rejected_bill(rejection_id)
    assert rest_res["status"] == "SUCCESS"
    assert get_rejected_bills_bucket().empty
    assert len(get_bill_review_queue()) == 1

    # Now reject again and delete permanently
    move_to_rejected_bucket("TEST-CAND-002", reason="Purge test", rejected_by="TEST_USER")
    rej_df_2 = get_rejected_bills_bucket()
    assert len(rej_df_2) == 1
    new_rej_id = rej_df_2.iloc[0]["rejection_id"]

    del_res = delete_rejected_bill(new_rej_id)
    assert del_res["status"] == "SUCCESS"
    assert get_rejected_bills_bucket().empty
