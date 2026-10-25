import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from core.db_sync import (
    format_bill_for_db,
    save_energy_bill,
    batch_save_energy_bills,
    get_existing_bill_numbers,
    delete_energy_bill,
)


def test_get_existing_bill_numbers():
    with patch("core.db_sync.get_supabase_client") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_table = MagicMock()
        mock_instance.table.return_value = mock_table
        mock_table.select.return_value.execute.return_value = MagicMock(
            data=[{"bill_number": "BILL-1001"}, {"bill_number": "BILL-1002"}]
        )
        
        existing = get_existing_bill_numbers()
        assert "BILL-1001" in existing
        assert "BILL-1002" in existing
        assert "BILL-9999" not in existing


def test_batch_save_energy_bills_duplicate_prevention():
    sample_bills = [
        {"Bill Number": "BILL-DUP-01", "Tariff Category": "GPS (< 110 kVA)", "Current Total (o)": "5000"},
        {"Bill Number": "BILL-NEW-02", "Tariff Category": "GPS (< 110 kVA)", "Current Total (o)": "7500"},
        {"Bill Number": "BILL-NEW-02", "Tariff Category": "GPS (< 110 kVA)", "Current Total (o)": "7500"}, # Intra-batch duplicate
    ]

    with patch("core.db_sync.get_supabase_client") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_table = MagicMock()
        mock_instance.table.return_value = mock_table
        
        # Suppose BILL-DUP-01 already in database
        mock_table.select.return_value.execute.return_value = MagicMock(
            data=[{"bill_number": "BILL-DUP-01"}]
        )
        mock_table.upsert.return_value.execute.return_value = MagicMock()

        res = batch_save_energy_bills(sample_bills, prevent_duplicates=True)
        assert res["status"] == "SUCCESS"
        assert res["saved_count"] == 1  # Only BILL-NEW-02 saved once
        assert res["skipped_count"] == 2  # BILL-DUP-01 and intra-batch BILL-NEW-02
        assert "BILL-DUP-01" in res["skipped_duplicates"]


def test_bucket_segregation_logic():
    existing_db = {"BILL-EXISTS-01"}
    batch_records = [
        {"Bill Number": "BILL-EXISTS-01", "Audit Verdict": "VERIFIED_MATCH", "Discrepancy Details": "None (Exact Match)"},
        {"Bill Number": "BILL-CLEAN-02", "Audit Verdict": "VERIFIED_MATCH", "Discrepancy Details": "None (Exact Match)"},
        {"Bill Number": "BILL-FAULT-03", "Audit Verdict": "MISMATCH ⚠️", "Discrepancy Details": "Energy Charges Diff: +₹500.00"},
    ]

    match_rows = []
    mismatch_rows = []
    dup_rows = []
    seen = set()

    for r in batch_records:
        bn = r["Bill Number"]
        is_dup = False
        if bn in existing_db or bn in seen:
            is_dup = True
        if bn:
            seen.add(bn)

        verdict = r.get("Audit Verdict", "").upper()
        is_mis = ("MISMATCH" in verdict) or (r.get("Discrepancy Details") != "None (Exact Match)")

        if is_dup:
            r["Bucket"] = "DUPLICATE"
            dup_rows.append(r)
        elif is_mis:
            r["Bucket"] = "MISMATCH"
            mismatch_rows.append(r)
        else:
            r["Bucket"] = "VERIFIED_MATCH"
            match_rows.append(r)

    assert len(match_rows) == 1
    assert match_rows[0]["Bill Number"] == "BILL-CLEAN-02"

    assert len(mismatch_rows) == 1
    assert mismatch_rows[0]["Bill Number"] == "BILL-FAULT-03"

    assert len(dup_rows) == 1
    assert dup_rows[0]["Bill Number"] == "BILL-EXISTS-01"
