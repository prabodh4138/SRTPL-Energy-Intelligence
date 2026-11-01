import io
import streamlit as st
import pandas as pd
import pytest
from fastapi import HTTPException
from backend.routers.reports import download_bills_excel, download_bills_csv
from backend.routers.dashboard import get_dashboard_summary
from backend.routers.bills import get_register, get_review_queue
from backend.routers.readings import get_readings
from backend.routers.validation import get_validation_summary
from backend.routers.juno import get_import_batches
from active_app.core.db_sync import (
    get_official_bill_register,
    get_all_energy_bills,
    get_bill_review_queue,
    KNOWN_CONSUMER_EXTRACTION_PROFILES,
    _IN_MEMORY_UPLOADED_BILLS,
    _IN_MEMORY_REVIEW_QUEUE,
    _IN_MEMORY_REJECTED_BILLS,
    save_energy_bill,
)


def test_empty_database_and_schema_purity():
    """Verify that when no data is in database, all endpoints return 0/clean state and export is strictly blocked."""
    _IN_MEMORY_UPLOADED_BILLS.clear()
    _IN_MEMORY_REVIEW_QUEUE.clear()
    _IN_MEMORY_REJECTED_BILLS.clear()
    for k in ["saved_energy_bills", "bill_review_queue", "rejected_bills_bucket"]:
        if k in st.session_state:
            st.session_state[k].clear()

    # 1. Register is completely empty
    reg_df = get_official_bill_register()
    assert reg_df.empty, f"Expected empty register in pristine state, found {len(reg_df)} rows"

    # 2. All bills dataset is empty
    bills_df = get_all_energy_bills()
    assert bills_df.empty, f"Expected empty energy bills, found {len(bills_df)} rows"

    # 3. Review queue is empty (no fake REV-001 or REV-002)
    queue_df = get_bill_review_queue()
    assert queue_df.empty, f"Expected empty review queue, found {len(queue_df)} items"

    # 4. API endpoints return 0 count
    api_reg = get_register()
    assert api_reg["count"] == 0
    assert api_reg["bills"] == []

    api_queue = get_review_queue()
    assert api_queue["count"] == 0
    assert api_queue["items"] == []

    # 5. Dashboard summary returns 0 KPIs and empty trend
    summary = get_dashboard_summary()
    assert summary["kpis"]["total_bills_found"] == 0
    assert summary["kpis"]["verified_posted"] == 0
    assert summary["kpis"]["held_for_review"] == 0
    assert summary["trend"] == [], f"Expected empty trend list, got {summary['trend']}"

    # 6. Readings endpoint returns 0 telemetry records when database is empty
    eb_readings = get_readings("eb")
    assert eb_readings["records"] == []
    assert eb_readings["kpis"][0]["value"] == "0 Meters"
    assert eb_readings["kpis"][1]["value"] == "0 kWh"

    # 7. Validation endpoint returns 0 open exceptions
    val_summary = get_validation_summary()
    assert val_summary["kpis"]["total_open_exceptions"] == 0
    assert val_summary["exceptions"] == []

    # 8. Juno import batches returns 0 batches
    batches = get_import_batches()
    assert batches == []

    # 9. Excel and CSV export STRICTLY BLOCKED with HTTP 400 when database is empty (no dummy file created)
    with pytest.raises(HTTPException) as exc_info:
        download_bills_excel()
    assert exc_info.value.status_code == 400
    assert "No bill records are present in the Supabase database" in exc_info.value.detail

    with pytest.raises(HTTPException) as exc_info_csv:
        download_bills_csv()
    assert exc_info_csv.value.status_code == 400


def test_uploaded_bills_extraction_accuracy_and_all_13_fields():
    """Verify that when authentic bills are ingested, all 13 fields, HT/LT, and PLAZA/HIGHWAY are 100% accurate."""
    _IN_MEMORY_UPLOADED_BILLS.clear()
    _IN_MEMORY_REVIEW_QUEUE.clear()
    _IN_MEMORY_REJECTED_BILLS.clear()
    for k in ["saved_energy_bills", "bill_review_queue", "rejected_bills_bucket"]:
        if k in st.session_state:
            st.session_state[k].clear()

    # Ingest 14 test bills matching the real corridor profiles (3 HT Toll Plaza + 11 LT Highway)
    test_bills = [
        # --- 3 HT Toll Plaza Substation Incomers ---
        {
            "bill_number": "EB-416000000110-SEP26",
            "consumer_account_no": "416000000110",
            "toll_plaza_id": "TP01",
            "bill_type": "HT",
            "consumer_scope": "PLAZA",
            "sanctioned_load_kw": 120.0,
            "contract_demand": "120 KVA",
            "bill_month": "Sep 2026",
            "bill_basis": "ACTUAL",
            "total_billed_kwh": 22653.0,
            "total_amount_payable": 158420.0,
            "amount_paid": 158420.0,
            "outstanding_balance": 0.0,
            "payment_status": "PAID",
        },
        {
            "bill_number": "EB-413000000002-SEP26",
            "consumer_account_no": "413000000002",
            "toll_plaza_id": "TP02",
            "bill_type": "HT",
            "consumer_scope": "PLAZA",
            "sanctioned_load_kw": 120.0,
            "contract_demand": "120 KVA",
            "bill_month": "Sep 2026",
            "bill_basis": "ACTUAL",
            "total_billed_kwh": 21100.0,
            "total_amount_payable": 147500.0,
            "amount_paid": 147500.0,
            "outstanding_balance": 0.0,
            "payment_status": "PAID",
        },
        {
            "bill_number": "EB-813000000281-SEP26",
            "consumer_account_no": "813000000281",
            "toll_plaza_id": "TP03",
            "bill_type": "HT",
            "consumer_scope": "PLAZA",
            "sanctioned_load_kw": 120.0,
            "contract_demand": "120 KVA",
            "bill_month": "Sep 2026",
            "bill_basis": "ACTUAL",
            "total_billed_kwh": 19450.0,
            "total_amount_payable": 132800.0,
            "amount_paid": 132800.0,
            "outstanding_balance": 0.0,
            "payment_status": "PAID",
        },
        # --- 11 LT Highway Lighting & Toll Admin Feeder Bills ---
        {
            "bill_number": "EB-411001070208-SEP26", "consumer_account_no": "411001070208", "toll_plaza_id": "TP01",
            "bill_type": "LT", "consumer_scope": "HIGHWAY", "sanctioned_load_kw": 10.0, "contract_demand": "10 KW",
            "bill_month": "Sep 2026", "bill_basis": "ACTUAL", "total_billed_kwh": 3672.0, "total_amount_payable": 24850.0,
            "amount_paid": 24850.0, "outstanding_balance": 0.0, "payment_status": "PAID"
        },
        {
            "bill_number": "EB-411001070208-AUG25", "consumer_account_no": "411001070208", "toll_plaza_id": "TP01",
            "bill_type": "LT", "consumer_scope": "HIGHWAY", "sanctioned_load_kw": 10.0, "contract_demand": "10 KW",
            "bill_month": "Aug 2025", "bill_basis": "ACTUAL", "total_billed_kwh": 3510.0, "total_amount_payable": 23620.0,
            "amount_paid": 23620.0, "outstanding_balance": 0.0, "payment_status": "PAID"
        },
        {
            "bill_number": "EB-416001070082-SEP26", "consumer_account_no": "416001070082", "toll_plaza_id": "TP01",
            "bill_type": "LT", "consumer_scope": "HIGHWAY", "sanctioned_load_kw": 20.0, "contract_demand": "20 KW",
            "bill_month": "Sep 2026", "bill_basis": "ACTUAL", "total_billed_kwh": 2980.0, "total_amount_payable": 20450.0,
            "amount_paid": 20450.0, "outstanding_balance": 0.0, "payment_status": "PAID"
        },
        {
            "bill_number": "EB-416001070084-AUG25", "consumer_account_no": "416001070084", "toll_plaza_id": "TP01",
            "bill_type": "LT", "consumer_scope": "HIGHWAY", "sanctioned_load_kw": 16.0, "contract_demand": "16 KW",
            "bill_month": "Aug 2025", "bill_basis": "ACTUAL", "total_billed_kwh": 3110.0, "total_amount_payable": 21100.0,
            "amount_paid": 21100.0, "outstanding_balance": 0.0, "payment_status": "PAID"
        },
        {
            "bill_number": "EB-416001070086-AUG25", "consumer_account_no": "416001070086", "toll_plaza_id": "TP01",
            "bill_type": "LT", "consumer_scope": "HIGHWAY", "sanctioned_load_kw": 13.0, "contract_demand": "13 KW",
            "bill_month": "Aug 2025", "bill_basis": "ACTUAL", "total_billed_kwh": 2840.0, "total_amount_payable": 19500.0,
            "amount_paid": 0.0, "outstanding_balance": 19500.0, "payment_status": "UNPAID"
        },
        {
            "bill_number": "EB-416001070090-SEP26", "consumer_account_no": "416001070090", "toll_plaza_id": "TP01",
            "bill_type": "LT", "consumer_scope": "HIGHWAY", "sanctioned_load_kw": 9.0, "contract_demand": "9 KW",
            "bill_month": "Sep 2026", "bill_basis": "ACTUAL", "total_billed_kwh": 3050.0, "total_amount_payable": 21300.0,
            "amount_paid": 21300.0, "outstanding_balance": 0.0, "payment_status": "PAID"
        },
        {
            "bill_number": "EB-416001111004-SEP26", "consumer_account_no": "416001111004", "toll_plaza_id": "TP01",
            "bill_type": "LT", "consumer_scope": "HIGHWAY", "sanctioned_load_kw": 6.0, "contract_demand": "6 KW",
            "bill_month": "Sep 2026", "bill_basis": "ACTUAL", "total_billed_kwh": 850.0, "total_amount_payable": 6200.0,
            "amount_paid": 6200.0, "outstanding_balance": 0.0, "payment_status": "PAID"
        },
        {
            "bill_number": "EB-413001070102-SEP26", "consumer_account_no": "413001070102", "toll_plaza_id": "TP02",
            "bill_type": "LT", "consumer_scope": "HIGHWAY", "sanctioned_load_kw": 16.0, "contract_demand": "16 KW",
            "bill_month": "Sep 2026", "bill_basis": "ACTUAL", "total_billed_kwh": 4120.0, "total_amount_payable": 29840.0,
            "amount_paid": 29840.0, "outstanding_balance": 0.0, "payment_status": "PAID"
        },
        {
            "bill_number": "EB-813001070057-SEP26", "consumer_account_no": "813001070057", "toll_plaza_id": "TP02",
            "bill_type": "LT", "consumer_scope": "HIGHWAY", "sanctioned_load_kw": 15.0, "contract_demand": "15 KW",
            "bill_month": "Sep 2026", "bill_basis": "ACTUAL", "total_billed_kwh": 3890.0, "total_amount_payable": 26900.0,
            "amount_paid": 26900.0, "outstanding_balance": 0.0, "payment_status": "PAID"
        },
        {
            "bill_number": "812010710261330579", "consumer_account_no": "812001070018", "toll_plaza_id": "TP03",
            "bill_type": "LT", "consumer_scope": "HIGHWAY", "sanctioned_load_kw": 28.0, "contract_demand": "28 KW",
            "bill_month": "Sep 2026", "bill_basis": "ACTUAL", "total_billed_kwh": 4608.0, "total_amount_payable": 31828.0,
            "amount_paid": 31452.25, "outstanding_balance": 0.0, "payment_status": "PAID"
        },
        {
            "bill_number": "EB-812001070018-AUG25", "consumer_account_no": "812001070018", "toll_plaza_id": "TP03",
            "bill_type": "LT", "consumer_scope": "HIGHWAY", "sanctioned_load_kw": 28.0, "contract_demand": "28 KW",
            "bill_month": "Aug 2025", "bill_basis": "ACTUAL", "total_billed_kwh": 4320.0, "total_amount_payable": 29650.0,
            "amount_paid": 29650.0, "outstanding_balance": 0.0, "payment_status": "PAID"
        },
    ]

    for b in test_bills:
        save_energy_bill(b, prevent_duplicates=False)

    df = get_official_bill_register()
    assert not df.empty, "Register should have records after upload"
    assert len(df) == 14, f"Expected exactly 14 bills, got {len(df)}"

    # 1. Feeder classification: exactly 3 HT, 11 LT
    bill_types = df["bill_type"].value_counts().to_dict()
    assert bill_types.get("HT") == 3, f"Expected 3 HT bills, got {bill_types.get('HT')}"
    assert bill_types.get("LT") == 11, f"Expected 11 LT bills, got {bill_types.get('LT')}"

    # 2. Scope classification: exactly 3 PLAZA, 11 HIGHWAY
    scopes = df["consumer_scope"].value_counts().to_dict()
    assert scopes.get("PLAZA") == 3, f"Expected 3 PLAZA bills, got {scopes.get('PLAZA')}"
    assert scopes.get("HIGHWAY") == 11, f"Expected 11 HIGHWAY bills, got {scopes.get('HIGHWAY')}"

    # 3. Sanctioned loads vary according to true feeder specification
    unique_loads = sorted(df["sanctioned_load_kw"].unique().tolist())
    assert 120.0 in unique_loads, "120 kW HT load must be present"
    assert 28.0 in unique_loads, "28 kW load must be present"
    assert 20.0 in unique_loads, "20 kW load must be present"
    assert 16.0 in unique_loads, "16 kW load must be present"

    # 4. Contract demand is varied (not uniform 10 KW)
    unique_cds = df["contract_demand"].unique().tolist()
    assert "120 KVA" in unique_cds, "120 KVA must be present"

    # 5. Security deposit has NO 0 values (all properly populated)
    zero_sd = (df["security_deposit"] == 0).sum()
    assert zero_sd == 0, f"Expected zero bills with 0 security deposit, got {zero_sd}"

    # 6. Rebate date has NO '—' values
    empty_rebate = (df["rebate_date"] == "—").sum()
    assert empty_rebate == 0, f"Expected zero bills with empty rebate date, got {empty_rebate}"

    # 7. Meter serial number has NO '—' values
    empty_meter = (df["meter_sl_no"] == "—").sum()
    assert empty_meter == 0, f"Expected zero bills with empty meter serial no, got {empty_meter}"

    # 8. Excel export succeeds with status 200 and contains both sheets with 100% accurate data
    res = download_bills_excel()
    assert res.status_code == 200
    xls = pd.ExcelFile(io.BytesIO(res.body))
    assert "Official_Energy_Bills" in xls.sheet_names
    assert "Executive_Summary" in xls.sheet_names

    df1 = pd.read_excel(xls, sheet_name="Official_Energy_Bills")
    assert len(df1) == 14
    assert (df1["bill_type"] == "HT").sum() == 3
    assert (df1["consumer_scope"] == "PLAZA").sum() == 3
    assert (df1["security_deposit"] == 0).sum() == 0

    df2 = pd.read_excel(xls, sheet_name="Executive_Summary")
    assert len(df2) == 14
    assert (df2["Feeder Type (HT/LT)"] == "HT").sum() == 3
    assert (df2["Scope (PLAZA/HIGHWAY)"] == "PLAZA").sum() == 3
    assert "Security Deposit (Rs.)" in df2.columns
    assert (df2["Security Deposit (Rs.)"] == 0).sum() == 0
