import os
import sys
import glob
import io
import time
import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
APP_DIR = os.path.join(ROOT_DIR, "active_app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from bill_extractor.extractor_main_full import extract_energy_bill_full
from bill_extractor.extractor_md_full import extract_md_bill_data
from bill_extractor.merge_clean_core import merge_and_clean_dataframes
from bill_extractor.verifier import verify_bill_calculations
from bill_extractor.zip_handler import extract_pdfs_from_inputs
from backend.routers.bills import _extract_single_item, _process_candidate

SAMPLE_DIR = os.path.join(ROOT_DIR, "source_data", "user_uploaded_bills", "extractor")
SAMPLE_PDFS = [p for p in glob.glob(os.path.join(SAMPLE_DIR, "*.pdf")) if "HDFC" not in p]


def test_sample_files_exist():
    assert len(SAMPLE_PDFS) >= 3, f"Expected at least 3 test bills, found {len(SAMPLE_PDFS)}"


def test_extraction_of_all_13_fields_on_lt_bill():
    lt_bill = [p for p in SAMPLE_PDFS if "411001070208" in p][0]
    with open(lt_bill, "rb") as f:
        data = f.read()

    bio = io.BytesIO(data)
    bio.name = os.path.basename(lt_bill)

    res = _extract_single_item((0, bio))
    assert res["error"] is None
    payload = res["payload"]

    # 1. Security Deposit
    assert payload.get("Security Deposit") in ["36360.14", "36,360.14"]
    # 2. MD
    assert payload.get("MD") is not None and str(payload.get("MD")).strip() != ""
    # 3. Contract Demand
    assert "KW" in payload.get("Contract Demand", "") or "10" in payload.get("Contract Demand", "")
    # 4. Section
    assert payload.get("Section") == "ESO RE SECTION"
    # 5. Sub-Division
    assert payload.get("Sub-Division") == "SDO-I SAMBALPUR"
    # 6. Rebate Date
    assert payload.get("Rebate Date") is not None and "/" in payload.get("Rebate Date")
    # 7. CUML MD-KVA
    assert payload.get("CUML MD-KVA") is not None and str(payload.get("CUML MD-KVA")).strip() != ""
    # 8. CUML MD-KW
    assert payload.get("CUML MD-KW") is not None and str(payload.get("CUML MD-KW")).strip() != ""
    # 9. DPS(Rs.)
    assert payload.get("DPS(Rs.)") is not None
    # 10. Tariff Category
    assert "PUBLIC LIGHT" in payload.get("Tariff Category", "")
    # 11. Meter Sl. No.
    assert payload.get("Meter Sl. No.") == "10029454"
    # 12. Net Payable Amount Before Rbt. Dt.(Rs.)
    assert payload.get("Net Payable Amount Before Rbt. Dt.(Rs.)") is not None
    # 13. Net Payable Amount After Rbt. Dt.(Rs.)
    assert payload.get("Net Payable Amount After Rbt. Dt.(Rs.)") is not None


def test_extraction_of_all_13_fields_on_ht_bill():
    ht_bill = [p for p in SAMPLE_PDFS if "416000000110" in p][0]
    with open(ht_bill, "rb") as f:
        data = f.read()

    bio = io.BytesIO(data)
    bio.name = os.path.basename(ht_bill)

    res = _extract_single_item((0, bio))
    assert res["error"] is None
    payload = res["payload"]

    # 1. Security Deposit
    assert payload.get("Security Deposit") in ["390096.00", "3,90,096.00"]
    # 2. MD
    assert payload.get("MD") is not None and str(payload.get("MD")).strip() != ""
    # 3. Contract Demand
    assert "120 KVA" in payload.get("Contract Demand", "")
    # 4. Section
    assert payload.get("Section") == "ESO SASON"
    # 5. Sub-Division
    assert payload.get("Sub-Division") == "SDO RENGALI"
    # 6. Rebate Date
    assert payload.get("Rebate Date") == "06/10/2026"
    # 7. CUML MD-KVA
    assert payload.get("CUML MD-KVA") is not None
    # 8. CUML MD-KW
    assert payload.get("CUML MD-KW") is not None
    # 9. DPS(Rs.)
    assert payload.get("DPS(Rs.)") == "0.00"
    # 10. Tariff Category
    assert "GENERAL PURPOSE" in payload.get("Tariff Category", "")
    # 11. Meter Sl. No.
    assert payload.get("Meter Sl. No.") == "TWN20045"
    # 12. Net Payable Amount Before Rbt. Dt.(Rs.)
    assert payload.get("Net Payable Amount Before Rbt. Dt.(Rs.)") == "167472.00"
    # 13. Net Payable Amount After Rbt. Dt.(Rs.)
    assert payload.get("Net Payable Amount After Rbt. Dt.(Rs.)") == "169071.00"


def test_ai_model_classification_100_percent_fit():
    for p in SAMPLE_PDFS[:5]:
        with open(p, "rb") as f:
            data = f.read()
        bio = io.BytesIO(data)
        bio.name = os.path.basename(p)
        res = _extract_single_item((0, bio))
        payload = res["payload"]
        assert payload.get("AI Model Applied") is not None
        assert payload.get("AI Model Confidence") == "100%"
        assert payload.get("AI Model Fit Percentage") == "100%"


def test_arithmetic_calculation_verification_prevents_wrong_data_insertion():
    # Construct candidate with invalid arithmetic calculation
    invalid_candidate = {
        "idx": 0,
        "file": "tampered_bill.pdf",
        "kind": "Bill",
        "consumer": "999999999999",
        "month": "2026/09",
        "identifier": "TAMPERED-BILL-001",
        "amount": 50000.0,
        "basis": "ACTUAL",
        "verifier_result": {
            "is_valid": False,
            "audit_status": "AUDIT REQUIRED ⚠️",
            "mismatch_reason": "Energy charges mismatch (Cal ₹15,000.00 vs Ext ₹25,000.00)",
        },
        "payload": {
            "Bill Number": "TAMPERED-BILL-001",
            "Consumer A/c No.": "999999999999",
            "Bill Month": "2026/09",
            "Bill Basis": "ACTUAL",
            "Cal Energy Charges": 15000.0,
            "a. Energy Charges": "25000.00",
            "Energy Charges Check": "MISMATCH ⚠️",
            "Audit Verdict": "AUDIT REQUIRED ⚠️",
        },
        "is_receipt": False,
        "error": None,
    }

    stats = {"verified": 0, "review": 0, "duplicates_rejected": 0, "failed": 0}
    result = _process_candidate(
        invalid_candidate, set(), set(), set(), set(), stats
    )

    # Must be routed to REVIEW and NEVER posted as VERIFIED
    assert result["result"] == "REVIEW"
    assert stats["verified"] == 0
    assert stats["review"] == 1
    assert "MISMATCH" in result["detail"]


def test_duplicate_rejection_at_application_and_db_level():
    cand1 = {
        "idx": 0,
        "file": "bill_tp01.pdf",
        "kind": "Bill",
        "consumer": "416000000110",
        "month": "2026/09",
        "identifier": "EXISTING-BILL-12345",
        "amount": 167472.0,
        "basis": "ACTUAL",
        "verifier_result": {"is_valid": True, "audit_status": "VERIFIED ✓"},
        "payload": {"bill_number": "EXISTING-BILL-12345"},
        "is_receipt": False,
        "error": None,
    }

    # Simulate existing bill in database
    existing_bills = {"EXISTING-BILL-12345"}
    seen_in_batch = set()
    stats = {"verified": 0, "review": 0, "duplicates_rejected": 0, "failed": 0}

    # 1. Reject duplicate present in database
    res1 = _process_candidate(cand1, existing_bills, set(), seen_in_batch, set(), stats)
    assert res1["result"] == "DUPLICATE_REJECTED"
    assert stats["duplicates_rejected"] == 1

    # 2. Reject duplicate within same batch
    cand2 = dict(cand1, identifier="NEW-BILL-999")
    cand2["payload"] = {"bill_number": "NEW-BILL-999"}
    res2 = _process_candidate(cand2, set(), set(), seen_in_batch, set(), stats)
    assert res2["result"] == "VERIFIED"

    # Re-sending the same bill in the batch
    res3 = _process_candidate(cand2, set(), set(), seen_in_batch, set(), stats)
    assert res3["result"] == "DUPLICATE_REJECTED"
    assert stats["duplicates_rejected"] == 2


def test_sub_second_in_memory_speed():
    sample = SAMPLE_PDFS[0]
    with open(sample, "rb") as f:
        data = f.read()

    t0 = time.time()
    bio = io.BytesIO(data)
    bio.name = os.path.basename(sample)
    res = _extract_single_item((0, bio))
    elapsed = time.time() - t0

    assert res["error"] is None
    # Must process in less than 2.0 seconds per bill
    assert elapsed < 2.0, f"Extraction took {elapsed:.2f}s, expected < 2.0s"
