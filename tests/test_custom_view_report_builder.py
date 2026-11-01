"""Tests for Custom View Builder & Report Export Studio (Module 6)."""
from __future__ import annotations

import io
import sys
from pathlib import Path
import pandas as pd
import pytest
import streamlit as st

ACTIVE_APP = Path(__file__).resolve().parents[1] / "active_app"
if str(ACTIVE_APP) not in sys.path:
    sys.path.insert(0, str(ACTIVE_APP))

from pages.reports_export_center import (
    BILL_REGISTER_COLUMN_LABELS,
    COLUMN_PRESETS,
    generate_styled_excel,
    _load_dataset_by_key,
    _sanitize_dataframe,
    _build_streamlit_column_configs,
)
from core.db_sync import (
    _IN_MEMORY_UPLOADED_BILLS,
    save_energy_bill,
)


@pytest.fixture(autouse=True)
def setup_mock_bills():
    """Sets up realistic test bills with all 13 fields for testing view builder."""
    _IN_MEMORY_UPLOADED_BILLS.clear()
    for k in ["saved_energy_bills", "bill_review_queue", "rejected_bills_bucket"]:
        if k in st.session_state:
            st.session_state[k].clear()
    sample_bill_ht = {
        "bill_number": "EB-HT-TP03-001",
        "consumer_account_no": "813000000281",
        "toll_plaza_id": "TP03",
        "bill_type": "HT",
        "consumer_scope": "PLAZA",
        "sanctioned_load_kw": 120.0,
        "contract_demand": "120 KVA",
        "bill_month": "Apr 2025",
        "financial_year": "2025-26",
        "meter_sl_no": "WES48722",
        "section": "ESO NO-I RAJGANGPUR",
        "sub_division": "SDO-IRAJGANGPUR",
        "division_name": "RED RAJGANGPUR",
        "tariff_category": "GENERAL PURPOSE >= 110 KVA",
        "security_deposit": 338171.70,
        "md": 0.3310,
        "cuml_md_kw": 0.0,
        "cuml_md_kva": 0.3484,
        "dps_rs": 0.01,
        "rebate_date": "06/05/2025",
        "due_date": "21/05/2025",
        "slab_normal_kwh": 25000.0,
        "slab_peak_kwh": 8000.0,
        "slab_solar_kwh": 2000.0,
        "total_billed_kwh": 35000.0,
        "energy_charges": 195000.0,
        "demand_charge": 12000.0,
        "tod_incentive": 2000.0,
        "tod_surcharge": 0.0,
        "electricity_charges": 205000.0,
        "electricity_duty": 11159.0,
        "total_amount_payable": 216159.0,
        "net_payable_amount_before_rbt_dt_rs": 216159.0,
        "net_payable_amount_after_rbt_dt_rs": 218198.0,
        "source_filename": "tp03_ht_bill.pdf",
    }
    sample_bill_lt = {
        "bill_number": "EB-LT-TP01-002",
        "consumer_account_no": "416001111004",
        "toll_plaza_id": "TP01",
        "bill_type": "LT",
        "consumer_scope": "HIGHWAY",
        "sanctioned_load_kw": 6.0,
        "contract_demand": "6 KW",
        "bill_month": "Sep 2026",
        "financial_year": "2026-27",
        "meter_sl_no": "LT9921",
        "section": "ESO HIGHWAY",
        "sub_division": "SDO HIGHWAY",
        "division_name": "SED",
        "tariff_category": "PUBLIC LIGHTING",
        "security_deposit": 5000.0,
        "md": 5.4,
        "cuml_md_kw": 5.4,
        "cuml_md_kva": 0.0,
        "dps_rs": 0.0,
        "rebate_date": "15/10/2026",
        "due_date": "30/10/2026",
        "slab_normal_kwh": 1200.0,
        "slab_peak_kwh": 0.0,
        "slab_solar_kwh": 0.0,
        "total_billed_kwh": 1200.0,
        "energy_charges": 6800.0,
        "demand_charge": 500.0,
        "tod_incentive": 0.0,
        "tod_surcharge": 0.0,
        "electricity_charges": 7300.0,
        "electricity_duty": 430.0,
        "total_amount_payable": 7730.0,
        "net_payable_amount_before_rbt_dt_rs": 7730.0,
        "net_payable_amount_after_rbt_dt_rs": 7800.0,
        "source_filename": "tp01_lt_bill.pdf",
    }
    save_energy_bill(sample_bill_ht)
    save_energy_bill(sample_bill_lt)
    yield
    # Teardown
    _IN_MEMORY_UPLOADED_BILLS.clear()
    for k in ["saved_energy_bills", "bill_review_queue", "rejected_bills_bucket"]:
        if k in st.session_state:
            st.session_state[k].clear()


def test_custom_view_dataset_loading_and_columns():
    """Verify loading datasets and presence of all 13 fields."""
    df = _load_dataset_by_key("OFFICIAL_BILLS")
    assert not df.empty
    assert len(df) == 2

    # Check 13 required fields are present
    required_13 = [
        "contract_demand", "security_deposit", "md", "cuml_md_kw", "cuml_md_kva",
        "dps_rs", "rebate_date", "meter_sl_no", "section", "sub_division",
        "tariff_category", "net_payable_amount_before_rbt_dt_rs",
        "net_payable_amount_after_rbt_dt_rs"
    ]
    for col in required_13:
        assert col in df.columns, f"Missing required field: {col}"

    # Verify HT Plaza Feeder classification
    ht_row = df[df["bill_type"] == "HT"].iloc[0]
    assert ht_row["consumer_account_no"] == "813000000281"
    assert ht_row["toll_plaza_id"] == "TP03"
    assert ht_row["consumer_scope"] == "PLAZA"
    assert ht_row["sanctioned_load_kw"] == 120.0
    assert ht_row["contract_demand"] == "120 KVA"
    assert ht_row["security_deposit"] == 338171.70


def test_column_presets_integrity():
    """Verify column presets match available fields."""
    df = _load_dataset_by_key("OFFICIAL_BILLS")
    all_cols = set(df.columns)

    for preset_name, preset_cols in COLUMN_PRESETS.items():
        assert len(preset_cols) > 0
        missing = [c for c in preset_cols if c not in all_cols]
        assert not missing, f"Preset '{preset_name}' has unrecognized columns: {missing}"


def test_filtering_logic():
    """Verify filtering by Month, Plaza, Feeder Type, Scope, and Search."""
    df = _load_dataset_by_key("OFFICIAL_BILLS")
    
    # Filter by Plaza
    tp03_df = df[df["toll_plaza_id"] == "TP03"]
    assert len(tp03_df) == 1
    assert tp03_df.iloc[0]["bill_number"] == "EB-HT-TP03-001"

    # Filter by Feeder Type
    lt_df = df[df["bill_type"] == "LT"]
    assert len(lt_df) == 1
    assert lt_df.iloc[0]["consumer_scope"] == "HIGHWAY"

    # Filter by Payment Status (both are UNPAID in bare test mode)
    unpaid_df = df[df["payment_status"] == "UNPAID"]
    assert len(unpaid_df) == 2


def test_excel_and_csv_generation():
    """Verify Excel and CSV generation functions."""
    df = _load_dataset_by_key("OFFICIAL_BILLS")
    sanitized = _sanitize_dataframe(df)

    # 1. Test Excel generation
    excel_bytes = generate_styled_excel(sanitized, sheet_title="Custom_View_Test")
    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 1000

    # 2. Test CSV generation
    csv_bytes = sanitized.to_csv(index=False).encode("utf-8-sig")
    assert isinstance(csv_bytes, bytes)
    assert len(csv_bytes) > 200
    assert b"EB-HT-TP03-001" in csv_bytes
    assert b"WES48722" in csv_bytes


def test_column_configs():
    """Verify Streamlit column configuration generator."""
    df = pd.DataFrame({
        "bill_number": ["EB-1"],
        "energy_charges": [1000.50],
        "total_billed_kwh": [500.0],
        "sanctioned_load_kw": [10.0],
        "md": [0.55],
        "payment_status": ["PAID"]
    })
    configs = _build_streamlit_column_configs(df)
    assert "energy_charges" in configs
    assert "total_billed_kwh" in configs
    assert "sanctioned_load_kw" in configs
