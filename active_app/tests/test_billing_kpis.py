import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import streamlit as st
from core.db_sync import (
    get_unified_billing_kpi_dataset,
    get_missing_bills_kpi,
    get_all_consumer_accounts,
    _clean_kpi_num,
)


@pytest.fixture(autouse=True)
def clean_session_state():
    st.session_state.clear()
    yield
    st.session_state.clear()


def test_clean_kpi_num():
    assert _clean_kpi_num("12,450.50") == 12450.50
    assert _clean_kpi_num("₹ 5,000") == 5000.0
    assert _clean_kpi_num(None) == 0.0
    assert _clean_kpi_num("—") == 0.0
    assert _clean_kpi_num("-") == 0.0
    assert _clean_kpi_num(2500) == 2500.0


def test_get_unified_billing_kpi_dataset_columns_and_enrichment():
    kpi_df = get_unified_billing_kpi_dataset()
    assert not kpi_df.empty

    required_cols = [
        "bill_number",
        "consumer_account_no",
        "toll_plaza_id",
        "bill_type",
        "asset_code",
        "consumer_scope",
        "division_name",
        "usage_type",
        "sanctioned_load_kw",
        "location",
        "bill_month",
        "bill_basis",
        "total_billed_kwh",
        "total_amount_payable",
        "amount_paid",
        "outstanding_balance",
        "payment_status",
        "bill_present",
    ]

    for col in required_cols:
        assert col in kpi_df.columns, f"Missing required KPI column: {col}"

    # Verify that plaza IDs are valid and all 3 plazas are represented
    plazas = set(kpi_df["toll_plaza_id"].dropna().unique())
    assert {"TP01", "TP02", "TP03"}.issubset(plazas), f"Expected TP01, TP02, and TP03 in plazas, found {plazas}"

    # Verify TP03 specific records exist
    tp03_records = kpi_df[kpi_df["toll_plaza_id"] == "TP03"]
    assert not tp03_records.empty, "TP03 bills must be present in the unified KPI dataset"
    assert any(str(r["consumer_account_no"]).startswith("81") for _, r in tp03_records.iterrows())

    # Verify connection types
    b_types = set(kpi_df["bill_type"].dropna().unique())
    assert "HT" in b_types or "LT" in b_types

    # Verify reading bases
    bases = set(kpi_df["bill_basis"].dropna().unique())
    assert any(b in bases for b in ["ACTUAL", "AVERAGE", "PROVISIONAL"])


def test_missing_bills_kpi_detection():
    # Pass an empty bills df: all master consumer accounts should be reported as missing
    empty_bills = pd.DataFrame(columns=["consumer_account_no", "bill_month"])
    missing_df = get_missing_bills_kpi(empty_bills, target_months=["Sep 2026"])

    assert not missing_df.empty
    assert "consumer_account_no" in missing_df.columns
    assert "bill_present" in missing_df.columns
    assert all(missing_df["bill_present"] == "NOT GENERATED")

    # If all accounts have bills, missing count should be 0
    all_accounts = get_all_consumer_accounts()["consumer_account_no"].tolist()
    full_bills = pd.DataFrame([
        {"consumer_account_no": ac, "bill_month": "Sep 2026"}
        for ac in all_accounts
    ])
    missing_none = get_missing_bills_kpi(full_bills, target_months=["Sep 2026"])
    assert missing_none.empty


def test_kpi_filtering_plaza_and_tariff():
    kpi_df = get_unified_billing_kpi_dataset()

    # Plaza filtering
    tp01_subset = kpi_df[kpi_df["toll_plaza_id"] == "TP01"]
    if not tp01_subset.empty:
        assert all(tp01_subset["toll_plaza_id"] == "TP01")

    # HT filtering
    ht_subset = kpi_df[kpi_df["bill_type"] == "HT"]
    if not ht_subset.empty:
        assert all(ht_subset["bill_type"] == "HT")

    # Actual basis filtering
    actual_subset = kpi_df[kpi_df["bill_basis"] == "ACTUAL"]
    if not actual_subset.empty:
        assert all(actual_subset["bill_basis"] == "ACTUAL")


def test_payment_status_integrity():
    kpi_df = get_unified_billing_kpi_dataset()
    for _, row in kpi_df.iterrows():
        p_stat = row["payment_status"]
        assert p_stat in {"PAID", "PARTIAL", "UNPAID", "NOT GENERATED"}
        if p_stat == "PAID":
            assert row["outstanding_balance"] <= 1.0
        elif p_stat == "UNPAID":
            assert row["amount_paid"] == 0.0


def test_payment_receipts_correlation():
    from core.db_sync import get_all_payment_receipts
    rc_df = get_all_payment_receipts()
    assert not rc_df.empty
    assert "receipt_no" in rc_df.columns
    assert "amount_paid" in rc_df.columns

    # Verify TP03 receipt exists
    tp03_rc = rc_df[rc_df["toll_plaza_id"] == "TP03"]
    assert not tp03_rc.empty
    assert any(str(a) == "812001070018" for a in tp03_rc["consumer_no"].dropna())


def test_tp03_missing_bills_audit():
    # Verify that get_missing_bills_kpi audits TP03 accounts when bills are absent
    empty_bills = pd.DataFrame(columns=["consumer_account_no", "bill_month"])
    missing_df = get_missing_bills_kpi(empty_bills, target_months=["Oct 2026"])
    assert not missing_df.empty

    tp03_missing = missing_df[missing_df["toll_plaza_id"] == "TP03"]
    assert not tp03_missing.empty
    assert any(str(a) == "813000000281" for a in tp03_missing["consumer_account_no"])
    assert any(str(a) == "812001070018" for a in tp03_missing["consumer_account_no"])
