import io
import pandas as pd
import pytest
from backend.routers.reports import download_bills_excel
from active_app.core.db_sync import (
    get_official_bill_register,
    KNOWN_CONSUMER_EXTRACTION_PROFILES,
    _IN_MEMORY_UPLOADED_BILLS,
    save_energy_bill
)

def test_official_bill_register_accuracy():
    df = get_official_bill_register()
    assert not df.empty, "Register should not be empty"
    assert len(df) >= 14, "Should have at least 14 actual bills"

    # 1. Feeder classification: 3 HT, 11 LT
    bill_types = df["bill_type"].value_counts().to_dict()
    assert bill_types.get("HT") == 3, f"Expected 3 HT bills, got {bill_types.get('HT')}"
    assert bill_types.get("LT") == 11, f"Expected 11 LT bills, got {bill_types.get('LT')}"

    # 2. Scope classification: 3 PLAZA, 11 HIGHWAY
    scopes = df["consumer_scope"].value_counts().to_dict()
    assert scopes.get("PLAZA") == 3, f"Expected 3 PLAZA bills, got {scopes.get('PLAZA')}"
    assert scopes.get("HIGHWAY") == 11, f"Expected 11 HIGHWAY bills, got {scopes.get('HIGHWAY')}"

    # 3. Sanctioned loads are NOT uniform 10 kW
    unique_loads = sorted(df["sanctioned_load_kw"].unique().tolist())
    assert len(unique_loads) >= 7, f"Expected varied loads, got {unique_loads}"
    assert 120.0 in unique_loads, "120 kW HT load should be present"
    assert 28.0 in unique_loads, "28 kW load should be present"
    assert 20.0 in unique_loads, "20 kW load should be present"
    assert 16.0 in unique_loads, "16 kW load should be present"

    # 4. Contract demand is NOT uniform 10 KW
    unique_cds = df["contract_demand"].unique().tolist()
    assert len(unique_cds) >= 6, f"Expected multiple contract demands, got {unique_cds}"
    assert "120 KVA" in unique_cds, "120 KVA should be present"

    # 5. Security deposit has NO 0 values
    zero_sd = (df["security_deposit"] == 0).sum()
    assert zero_sd == 0, f"Expected zero bills with 0 security deposit, got {zero_sd}"

    # 6. Rebate date has NO '—' values
    empty_rebate = (df["rebate_date"] == "—").sum()
    assert empty_rebate == 0, f"Expected zero bills with empty rebate date, got {empty_rebate}"

    # 7. Meter serial number has NO '—' values
    empty_meter = (df["meter_sl_no"] == "—").sum()
    assert empty_meter == 0, f"Expected zero bills with empty meter serial no, got {empty_meter}"


def test_excel_export_sheets():
    res = download_bills_excel()
    assert res.status_code == 200

    excel_data = io.BytesIO(res.body)
    xls = pd.ExcelFile(excel_data)
    assert "Official_Energy_Bills" in xls.sheet_names
    assert "Executive_Summary" in xls.sheet_names

    df1 = pd.read_excel(xls, sheet_name="Official_Energy_Bills")
    assert not df1.empty
    assert (df1["bill_type"] == "HT").sum() == 3
    assert (df1["consumer_scope"] == "PLAZA").sum() == 3
    assert (df1["security_deposit"] == 0).sum() == 0

    df2 = pd.read_excel(xls, sheet_name="Executive_Summary")
    assert not df2.empty
    assert (df2["Feeder Type (HT/LT)"] == "HT").sum() == 3
    assert (df2["Scope (PLAZA/HIGHWAY)"] == "PLAZA").sum() == 3
    assert "Security Deposit (Rs.)" in df2.columns
    assert (df2["Security Deposit (Rs.)"] == 0).sum() == 0
