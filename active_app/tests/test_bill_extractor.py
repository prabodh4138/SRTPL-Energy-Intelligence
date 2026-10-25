import glob
import os
import io
import zipfile
import pandas as pd
import pytest
from bill_extractor.extractor_main_full import extract_energy_bill_full
from bill_extractor.extractor_md_full import extract_md_bill_data
from bill_extractor.extractor_receipt_full import extract_energy_receipt_data
from bill_extractor.merge_clean_core import merge_and_clean_dataframes
from bill_extractor.verifier import verify_bill_calculations
from bill_extractor.zip_handler import extract_pdfs_from_inputs


def test_bill_extractor_all_14_fields():
    bill_pdfs = sorted(glob.glob("source_data/user_uploaded_bills/extractor/*EN.pdf"))
    assert len(bill_pdfs) >= 13, f"Found {len(bill_pdfs)} bill PDFs, expected at least 13"

    expected_14_fields = [
        "Meter Rent Count",
        "Security Deposit",
        "Bill Period",
        "Bill Days/Months",
        "Meter Sl. No.",
        "a. Energy Charges",
        "Slab Normal - KWH",
        "DPS(Rs.)",
        "Tariff Category",
        "Division",
        "Sub-Division",
        "Section",
    ]

    for p in bill_pdfs:
        fname = os.path.basename(p)
        res = extract_energy_bill_full(p, fname)

        # Verify all 14 requested columns exist in dictionary
        for f in expected_14_fields:
            assert f in res, f"Field '{f}' missing from extracted keys in {fname}"

        # Verify critical fields have extracted non-empty values
        assert res["Meter Rent Count"] != "", f"Empty Meter Rent Count in {fname}"
        assert res["Security Deposit"] != "", f"Empty Security Deposit in {fname}"
        assert res["Bill Period"] != "", f"Empty Bill Period in {fname}"
        assert res["Bill Days/Months"] != "", f"Empty Bill Days/Months in {fname}"
        assert res["Meter Sl. No."] != "", f"Empty Meter Sl. No. in {fname}"
        assert res["a. Energy Charges"] != "", f"Empty a. Energy Charges in {fname}"
        assert res["Slab Normal - KWH"] != "", f"Empty Slab Normal - KWH in {fname}"
        assert res["DPS(Rs.)"] != "", f"Empty DPS(Rs.) in {fname}"
        assert res["Tariff Category"] != "", f"Empty Tariff Category in {fname}"
        assert res["Division"] != "", f"Empty Division in {fname}"
        assert res["Sub-Division"] != "", f"Empty Sub-Division in {fname}"
        assert res["Section"] != "", f"Empty Section in {fname}"


def test_bill_mathematical_verification_all_11_bills():
    bill_pdfs = sorted(glob.glob("source_data/user_uploaded_bills/extractor/*EN.pdf"))
    assert len(bill_pdfs) >= 13, f"Found {len(bill_pdfs)} bill PDFs, expected at least 13"

    for p in bill_pdfs:
        fname = os.path.basename(p)
        bill_data = extract_energy_bill_full(p, fname)
        v = verify_bill_calculations(bill_data)

        # Formula 1: Energy charges = slab normal*rate + slab peak*rate + slab solar*rate
        assert v["match_energy_charges"] is True, f"Energy charges mismatch in {fname}: {v['cal_energy_charges']} != {v['ext_energy_charges']}"
        assert abs(v["diff_energy_charges"]) <= 0.05

        # Formula 2: Electricity charges = Cal Energy charges + Demand Charges/MMFC + TOD Incentive + TOD Surchg
        assert v["match_electricity_charges"] is True, f"Electricity charges mismatch in {fname}: {v['cal_electricity_charges']} != {v['ext_electricity_charges']}"
        assert abs(v["diff_electricity_charges"]) <= 0.05

        # Formula 3: Total Current Bill = Cal Electricity Charges + Duty + Meter Rent + Service Charge - EBill Rebate
        assert v["match_current_total"] is True, f"Current total mismatch in {fname}: {v['cal_current_total']} != {v['ext_current_total']}"
        assert abs(v["diff_current_total"]) <= 0.05

        # Overall Audit Verdict
        assert "VERIFIED" in v["audit_status"]


def test_zip_file_unpacking_and_extraction():
    # Build an in-memory ZIP archive containing 2 bill PDFs
    bill_pdfs = sorted(glob.glob("source_data/user_uploaded_bills/extractor/*EN.pdf"))[:2]
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for p in bill_pdfs:
            zf.write(p, arcname=f"nested_folder/{os.path.basename(p)}")

    zip_buffer.seek(0)
    zip_buffer.name = "test_bills_archive.zip"

    # Test extract_pdfs_from_inputs on zip
    extracted_pdfs = extract_pdfs_from_inputs(zip_buffer)
    assert len(extracted_pdfs) == 2
    for pdf_obj in extracted_pdfs:
        assert hasattr(pdf_obj, "name")
        assert pdf_obj.name.endswith(".pdf")
        data = extract_energy_bill_full(pdf_obj, pdf_obj.name)
        assert data["Meter Rent Count"] != ""
        v = verify_bill_calculations(data)
        assert v["match_energy_charges"] is True


def test_bill_merge_pipeline_and_excel_export():
    bill_pdfs = sorted(glob.glob("source_data/user_uploaded_bills/extractor/*EN.pdf"))[:3]
    main_records = []
    md_records = []

    for p in bill_pdfs:
        fname = os.path.basename(p)
        m = extract_energy_bill_full(p, fname)
        v = verify_bill_calculations(m)
        m["Cal Energy Charges"] = v["cal_energy_charges"]
        m["Energy Charges Check"] = "MATCH ✓" if v["match_energy_charges"] else "MISMATCH ⚠️"
        m["Cal Electricity Charges"] = v["cal_electricity_charges"]
        m["Electricity Charges Check"] = "MATCH ✓" if v["match_electricity_charges"] else "MISMATCH ⚠️"
        m["Cal Current Total"] = v["cal_current_total"]
        m["Current Total Check"] = "MATCH ✓" if v["match_current_total"] else "MISMATCH ⚠️"
        m["Audit Verdict"] = v["audit_status"]
        main_records.append(m)
        md_records.append(extract_md_bill_data(p, fname))

    df_main = pd.DataFrame(main_records).drop(columns=["raw_text"], errors="ignore")
    df_md = pd.DataFrame(md_records)

    merged = merge_and_clean_dataframes(df_main, df_md)
    assert not merged.empty
    assert "Slab Normal - KWH" in merged.columns
    assert "Meter Rent Count" in merged.columns
    assert "Net Payable Amount After Rbt. Dt.(Rs.)" in merged.columns
    assert "Cal Energy Charges" in merged.columns
    assert "Audit Verdict" in merged.columns

    # Verify Excel generation
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        merged.to_excel(writer, index=False, sheet_name="Energy_Bill_Data")
    assert output.getvalue().startswith(b"PK")  # ZIP/XLSX header signature


def test_receipt_extraction():
    receipt_pdfs = sorted(glob.glob("source_data/user_uploaded_bills/extractor/*HDFC*.pdf"))
    assert len(receipt_pdfs) >= 4, f"Found {len(receipt_pdfs)} receipts"

    for r in receipt_pdfs:
        fname = os.path.basename(r)
        data = extract_energy_receipt_data(r, fname)
        assert data["Receipt No"] != ""
        assert data["Account NO"] != ""
        assert data["Consumer No"] != ""
        assert data["Amount Paid"] != ""
        assert data["Collections Date"] != ""
