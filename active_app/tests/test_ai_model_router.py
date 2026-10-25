import os
import pytest
from bill_extractor.extractor_main_full import extract_energy_bill_full
from bill_extractor.extractor_md_full import extract_md_bill_data
from bill_extractor.verifier import verify_bill_calculations
from bill_extractor.ai_model_router import (
    classify_bill_format,
    compute_derived_sbm_slabs,
    MODEL_CATALOG,
)

BILL_1_PATH = r"C:\Users\prabo\.gemini\antigravity\brain\83225691-b0cb-4392-bb5b-407b77fc9a89\.user_uploaded\media_1792933000331_d9c0f442.pdf"
BILL_2_PATH = r"C:\Users\prabo\.gemini\antigravity\brain\83225691-b0cb-4392-bb5b-407b77fc9a89\.user_uploaded\media_1792933000331_bc65641e.pdf"
BILL_3_PATH = r"C:\Users\prabo\.gemini\antigravity\brain\83225691-b0cb-4392-bb5b-407b77fc9a89\.user_uploaded\media_1792933000331_f382d16f.pdf"


def test_ai_model_catalog_structure():
    assert "MODEL_1_HT_TOD" in MODEL_CATALOG
    assert "MODEL_2_LT_SBM" in MODEL_CATALOG
    assert "MODEL_3_LT_COMMERCIAL_TOD" in MODEL_CATALOG
    assert "MODEL_4_UNIVERSAL_ADAPTIVE" in MODEL_CATALOG

    for m_id, meta in MODEL_CATALOG.items():
        assert "model_name" in meta
        assert "voltage_class" in meta
        assert "metering_unit" in meta
        assert "default_ed_pct" in meta
        assert "demand_unit" in meta


def test_ai_classifier_bill_1_ht():
    if not os.path.exists(BILL_1_PATH):
        pytest.skip("Bill 1 PDF not available in test environment")

    m = extract_energy_bill_full(BILL_1_PATH, "bill_1.pdf")
    md = extract_md_bill_data(BILL_1_PATH, "bill_1.pdf")
    full = {**m, **md}
    v = verify_bill_calculations(full)

    # 1. AI Model Identification
    assert m["AI Model ID"] == "MODEL_1_HT_TOD"
    assert "HT Industrial" in m["AI Model Applied"]
    assert float(m["AI Model Confidence"].replace("%", "")) >= 90.0

    # 2. Key Field Verifications
    assert m["Consumer A/c No."] == "813000000281"
    assert m["Bill Number"] == "813000005251470713"
    assert m["Old Consumer No."] == "448-L"
    assert m["Bill Basis"] == "ACTUAL"
    assert ">= 110 KVA" in m["Tariff Category"]

    # 3. Decimal Slabs & Net Payable Check
    assert float(m.get("Slab 1 - KWH", 0)) > 0
    assert m["Net Payable Amount Before Rbt. Dt.(Rs.)"] == "216159.00"
    assert md["Net Payable Amount After Rbt. Dt.(Rs.)"] == "218198.00"

    # 4. Zero Arithmetic Variance
    assert v["match_energy_charges"] is True
    assert v["match_electricity_charges"] is True
    assert v["match_current_total"] is True
    assert "VERIFIED" in v["audit_status"]


def test_ai_classifier_bill_2_lt_sbm():
    if not os.path.exists(BILL_2_PATH):
        pytest.skip("Bill 2 PDF not available in test environment")

    m = extract_energy_bill_full(BILL_2_PATH, "bill_2.pdf")
    md = extract_md_bill_data(BILL_2_PATH, "bill_2.pdf")
    full = {**m, **md}
    v = verify_bill_calculations(full)

    # 1. AI Model Identification
    assert m["AI Model ID"] == "MODEL_2_LT_SBM"
    assert "LT SBM Spot Billing" in m["AI Model Applied"]
    assert float(m["AI Model Confidence"].replace("%", "")) >= 90.0

    # 2. Alphanumeric & Slashed ID Integrity
    assert m["Consumer A/c No."] == "813413021313"
    assert m["Bill Number"] == "813090525000020M9529"
    assert m["Old Consumer No."] == "COM12-B-116/LT"
    assert m["Bill Basis"] == "ACTUAL"

    # 3. Derived Demand & Before/After Rebate
    assert md["MD-KW"] == "1.000"
    assert m["Net Payable Amount Before Rbt. Dt.(Rs.)"] == "366.00"
    assert md["Net Payable Amount After Rbt. Dt.(Rs.)"] == "374.00"

    # 4. Exact Zero Variance
    assert v["match_energy_charges"] is True
    assert v["match_electricity_charges"] is True
    assert v["match_current_total"] is True
    assert abs(v["diff_energy_charges"]) == 0.0
    assert abs(v["diff_electricity_charges"]) == 0.0
    assert abs(v["diff_current_total"]) == 0.0
    assert "VERIFIED" in v["audit_status"]


def test_ai_classifier_bill_3_lt_sbm():
    if not os.path.exists(BILL_3_PATH):
        pytest.skip("Bill 3 PDF not available in test environment")

    m = extract_energy_bill_full(BILL_3_PATH, "bill_3.pdf")
    md = extract_md_bill_data(BILL_3_PATH, "bill_3.pdf")
    full = {**m, **md}
    v = verify_bill_calculations(full)

    # 1. AI Model Identification
    assert m["AI Model ID"] == "MODEL_2_LT_SBM"
    assert "LT SBM Spot Billing" in m["AI Model Applied"]
    assert float(m["AI Model Confidence"].replace("%", "")) >= 90.0

    # 2. Alphanumeric & Slashed ID Integrity
    assert m["Consumer A/c No."] == "813413052467"
    assert m["Bill Number"] == "813040525000069M9396"
    assert m["Old Consumer No."] == "C12-Y-296/LT"
    assert m["Bill Basis"] == "ACTUAL"

    # 3. Derived Demand & Before/After Rebate
    assert md["MD-KW"] == "2.860"
    assert m["Net Payable Amount Before Rbt. Dt.(Rs.)"] == "401.00"
    assert md["Net Payable Amount After Rbt. Dt.(Rs.)"] == "408.00"

    # 4. Exact Zero Variance
    assert v["match_energy_charges"] is True
    assert v["match_electricity_charges"] is True
    assert v["match_current_total"] is True
    assert abs(v["diff_energy_charges"]) == 0.0
    assert abs(v["diff_electricity_charges"]) == 0.0
    assert abs(v["diff_current_total"]) == 0.0
    assert "VERIFIED" in v["audit_status"]


def test_compute_derived_sbm_slabs():
    # 77 units -> 77 @ 5.90 = 454.30
    slabs, total = compute_derived_sbm_slabs(77.0)
    assert len(slabs) == 1
    assert slabs[0]["units"] == 77.0
    assert slabs[0]["amount"] == 454.30
    assert total == 454.30

    # 150 units -> 100 @ 5.90 (590) + 50 @ 7.00 (350) = 940.00
    slabs_150, total_150 = compute_derived_sbm_slabs(150.0)
    assert len(slabs_150) == 2
    assert slabs_150[0]["units"] == 100.0
    assert slabs_150[1]["units"] == 50.0
    assert total_150 == 940.00


def test_classifier_universal_fallback():
    # When text is ambiguous or lacks clear markers, it routes to Universal Adaptive
    cls_res = classify_bill_format("GENERIC ELECTRICITY BILL FOR DOMESTIC USAGE 50 UNITS")
    assert cls_res["model_id"] == "MODEL_4_UNIVERSAL_ADAPTIVE"
    assert "Universal Adaptive" in cls_res["model_name"]
    assert cls_res["confidence"] > 0.8
