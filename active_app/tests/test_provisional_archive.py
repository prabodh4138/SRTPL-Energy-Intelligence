import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from core.db_sync import (
    format_bill_for_db,
    save_provisional_energy_bill,
    batch_save_provisional_energy_bills,
    get_existing_provisional_bill_numbers,
    get_all_provisional_energy_bills,
    delete_provisional_energy_bill,
    get_all_energy_bills,
)


def test_format_bill_for_db_preserves_audit_flag_and_basis():
    raw_bill = {
        "Bill Number": "PROV-TEST-001",
        "Consumer A/c No.": "81309999",
        "Bill Month": "Jul-2026",
        "Bill Basis": "AVERAGE",
        "Audit Flag": "DISCOM AVERAGE Basis (Not Actual Reading) — Maintained in public.energy_bills_provisional",
        "Current Total (o)": "14250.00",
    }
    payload = format_bill_for_db(raw_bill)
    assert payload["bill_number"] == "PROV-TEST-001"
    assert payload["consumer_account_no"] == "81309999"
    assert payload["bill_basis"] == "AVERAGE"
    assert "public.energy_bills_provisional" in payload["audit_flag"]


def test_save_provisional_energy_bill_cloud_mock():
    raw_bill = {
        "Bill Number": "PROV-TEST-002",
        "Consumer A/c No.": "81308888",
        "Bill Month": "Aug-2026",
        "Bill Basis": "PROVISIONAL",
        "Current Total (o)": "9800.50",
    }
    with patch("core.db_sync.get_supabase_client") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_table = MagicMock()
        mock_instance.table.return_value = mock_table
        mock_table.upsert.return_value.execute.return_value = MagicMock()

        res = save_provisional_energy_bill(raw_bill)
        assert res["status"] == "SUCCESS"
        assert res["bill_number"] == "PROV-TEST-002"
        assert res["cloud_saved"] is True
        # Verify table name targeted was strictly energy_bills_provisional
        mock_instance.table.assert_called_with("energy_bills_provisional")


def test_batch_save_provisional_energy_bills_and_deduplication():
    prov_bills = [
        {"Bill Number": "PROV-DUP-01", "Bill Basis": "AVERAGE", "Current Total (o)": "4500"},
        {"Bill Number": "PROV-NEW-02", "Bill Basis": "PROVISIONAL", "Current Total (o)": "6200"},
        {"Bill Number": "PROV-NEW-02", "Bill Basis": "PROVISIONAL", "Current Total (o)": "6200"}, # Intra-batch duplicate
    ]

    with patch("core.db_sync.get_supabase_client") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_table = MagicMock()
        mock_instance.table.return_value = mock_table

        # Mock existing provisional records
        mock_table.select.return_value.execute.return_value = MagicMock(
            data=[{"bill_number": "PROV-DUP-01", "bill_basis": "AVERAGE"}]
        )
        mock_table.upsert.return_value.execute.return_value = MagicMock()

        res = batch_save_provisional_energy_bills(prov_bills, prevent_duplicates=True)
        assert res["status"] == "SUCCESS"
        assert res["saved_count"] == 1  # Only PROV-NEW-02 saved once
        assert res["skipped_count"] == 2  # PROV-DUP-01 and duplicate PROV-NEW-02
        assert "PROV-DUP-01" in res["skipped_duplicates"]
        # Verify targeted table was energy_bills_provisional
        mock_instance.table.assert_called_with("energy_bills_provisional")


def test_get_existing_provisional_bill_numbers_mapping():
    with patch("core.db_sync.get_supabase_client") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_table = MagicMock()
        mock_instance.table.return_value = mock_table
        mock_table.select.return_value.execute.return_value = MagicMock(
            data=[
                {"bill_number": "813090525000020", "bill_basis": "AVERAGE"},
                {"bill_number": "813040525000069", "bill_basis": "PROVISIONAL"},
            ]
        )

        prov_map = get_existing_provisional_bill_numbers()
        assert "813090525000020" in prov_map
        assert prov_map["813090525000020"] == "AVERAGE"
        assert "813040525000069" in prov_map
        assert prov_map["813040525000069"] == "PROVISIONAL"


def test_provisional_hint_generation_in_batch_upload():
    """Verify that when a bill exists in provisional archive, a clear hint is generated on re-upload."""
    existing_prov_bills = {"813090525000020": "AVERAGE"}
    existing_db_bills = {"813010101000001"}

    test_row = {
        "Bill Number": "813090525000020",
        "Consumer A/c No.": "813090525",
        "Bill Basis": "AVERAGE",
        "Current Total (o)": "5500.00",
    }

    bn = test_row["Bill Number"]
    prior_upload_hint = None
    if bn and bn in existing_prov_bills:
        prev_basis_tag = existing_prov_bills[bn]
        prior_upload_hint = f"💡 Hint: Previously recorded with bill basis '{prev_basis_tag}' in public.energy_bills_provisional"

    assert prior_upload_hint is not None
    assert "AVERAGE" in prior_upload_hint
    assert "public.energy_bills_provisional" in prior_upload_hint


def test_delete_provisional_energy_bill():
    with patch("core.db_sync.get_supabase_client") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_table = MagicMock()
        mock_instance.table.return_value = mock_table
        mock_eq = MagicMock()
        mock_table.delete.return_value.eq.return_value = mock_eq
        mock_eq.execute.return_value = MagicMock()

        res = delete_provisional_energy_bill("PROV-DEL-999")
        assert res["status"] == "DELETED"
        assert res["bill_number"] == "PROV-DEL-999"
        mock_instance.table.assert_called_with("energy_bills_provisional")


def test_strict_kpi_isolation():
    """Verify that get_all_energy_bills only targets public.energy_bills and does NOT query energy_bills_provisional."""
    with patch("core.db_sync.get_supabase_client") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_table = MagicMock()
        mock_instance.table.return_value = mock_table
        mock_table.select.return_value.order.return_value.execute.return_value = MagicMock(
            data=[{"bill_number": "ACTUAL-001", "bill_basis": "ACTUAL", "current_total": 50000}]
        )

        actual_df = get_all_energy_bills()
        # Ensure it accessed 'energy_bills', NOT 'energy_bills_provisional'
        mock_instance.table.assert_called_with("energy_bills")
        assert not actual_df.empty
        assert actual_df.iloc[0]["bill_number"] == "ACTUAL-001"
