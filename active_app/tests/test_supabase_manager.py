"""Unit tests for Supabase & Database Management and Network URL detection."""
import pytest
from core.supabase_manager import (
    get_network_info,
    test_database_connection as check_db_conn,
    inject_master_and_sample_data,
    remove_all_database_data,
)
from core.demo_store import is_demo_mode, set_demo_mode, get_demo_bills, get_demo_monthly_eb_consumption


def test_get_network_info():
    net = get_network_info(port=8501)
    assert "local_url" in net
    assert "network_url" in net
    assert "ip" in net
    assert net["port"] == "8501"
    assert "http://localhost:8501" == net["local_url"]
    assert net["network_url"].startswith("http://")


def test_database_connection_status():
    conn = check_db_conn()
    assert "connected" in conn
    assert "status" in conn
    assert "message" in conn
    assert "message" in conn


def test_data_injection():
    progress_calls = []
    def _cb(msg, frac):
        progress_calls.append((msg, frac))

    result = inject_master_and_sample_data(_cb)
    assert result["plazas"] == 3
    assert result["assets"] >= 18
    assert result["bills"] == 13
    assert result["receipts"] == 4
    assert len(progress_calls) >= 3


def test_database_wipe():
    res = remove_all_database_data()
    assert res["status"] == "SUCCESS"
    assert len(res["cleared_tables"]) >= 5


def test_clean_production_mode_empty_slate():
    # When demo mode is disabled (production clean state), store returns empty frames
    set_demo_mode(False)
    assert not is_demo_mode()
    bills_df = get_demo_bills()
    assert bills_df.empty, "In clean production mode, bills dataframe must be empty"
    monthly_df = get_demo_monthly_eb_consumption()
    assert monthly_df.empty, "In clean production mode, monthly consumption must be empty"

    # Reset back to demo mode for tests
    set_demo_mode(True)
    assert is_demo_mode()
    bills_demo = get_demo_bills()
    assert not bills_demo.empty, "In demo mode, bills dataframe must contain sample bills"
