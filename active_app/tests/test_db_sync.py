"""Unit tests for live database synchronization & CRUD operations."""
import pytest
from core.db_sync import (
    get_all_plazas,
    save_plaza,
    delete_plaza,
    get_all_assets,
    save_asset,
    delete_asset,
    delete_energy_bill,
    update_exception_in_database,
)


def test_plaza_crud():
    # 1. Fetch plazas
    df = get_all_plazas()
    assert not df.empty
    assert "plaza_id" in df.columns

    # 2. Add / update a test plaza
    res = save_plaza("TP99", "Toll Plaza 99 Test", "Km 999 Test Location", is_active=True)
    assert res["status"] == "SUCCESS"
    assert res["payload"]["plaza_id"] == "TP99"

    df_after = get_all_plazas()
    assert "TP99" in df_after["plaza_id"].values

    # 3. Delete the test plaza
    del_res = delete_plaza("TP99")
    assert del_res["status"] == "DELETED"
    df_clean = get_all_plazas()
    assert "TP99" not in df_clean["plaza_id"].values


def test_asset_crud():
    # 1. Fetch assets
    df = get_all_assets()
    assert not df.empty
    assert "asset_id" in df.columns

    # 2. Add a test asset
    res = save_asset(
        asset_id="AST-TEST-99",
        asset_code="SR-TEST-0099",
        asset_name="Test Generator 99",
        plaza_id="TP01",
        source_type="DG",
        capacity_kva=125.0,
        is_active=True,
    )
    assert res["status"] == "SUCCESS"
    assert res["payload"]["asset_id"] == "AST-TEST-99"

    df_after = get_all_assets()
    assert "AST-TEST-99" in df_after["asset_id"].values

    # 3. Delete the test asset
    del_res = delete_asset("AST-TEST-99")
    assert del_res["status"] == "DELETED"
    df_clean = get_all_assets()
    assert "AST-TEST-99" not in df_clean["asset_id"].values


def test_bill_and_exception_sync():
    # 1. Bill deletion sync
    bill_res = delete_energy_bill("TEST-BILL-999")
    assert bill_res["status"] == "DELETED"
    assert bill_res["bill_number"] == "TEST-BILL-999"

    # 2. Exception update sync
    exc_res = update_exception_in_database(
        exception_id="EXC-1001",
        status="RESOLVED",
        corrected_value=1325.0,
        note="Corrected via test suite",
    )
    assert exc_res["status"] == "UPDATED"
    assert exc_res["exception_id"] == "EXC-1001"
