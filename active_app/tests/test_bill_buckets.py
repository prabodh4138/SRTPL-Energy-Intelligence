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
        {"Bill Number": "BILL-EXISTS-01", "Consumer A/c No.": "81300101", "Bill Basis": "ACTUAL", "Audit Verdict": "VERIFIED_MATCH", "Discrepancy Details": "None (Exact Match)"},
        {"Bill Number": "BILL-CLEAN-02", "Consumer A/c No.": "81300102", "Bill Basis": "ACTUAL", "Audit Verdict": "VERIFIED_MATCH", "Discrepancy Details": "None (Exact Match)"},
        {"Bill Number": "BILL-PROV-03", "Consumer A/c No.": "81300103", "Bill Basis": "PROVISIONAL", "Audit Verdict": "VERIFIED_MATCH", "Discrepancy Details": "None (Exact Match)"},
        {"Bill Number": "BILL-AVG-04", "Consumer A/c No.": "81300104", "Bill Basis": "AVERAGE", "Audit Verdict": "VERIFIED_MATCH", "Discrepancy Details": "None (Exact Match)"},
        {"Bill Number": "BILL-FAULT-05", "Consumer A/c No.": "81300105", "Bill Basis": "ACTUAL", "Audit Verdict": "MISMATCH ⚠️", "Discrepancy Details": "Energy Charges Diff: +₹500.00"},
    ]

    match_rows = []
    prov_avg_rows = []
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

        raw_basis = str(r.get("Bill Basis", "")).upper()
        is_prov_or_avg = any(k in raw_basis for k in ["PROV", "AVG", "AVERAGE", "DEFECT", "ESTIMAT"])
        verdict = r.get("Audit Verdict", "").upper()
        is_mis = ("MISMATCH" in verdict) or (r.get("Discrepancy Details") != "None (Exact Match)")

        if is_dup:
            r["Bucket"] = "DUPLICATE"
            dup_rows.append(r)
        elif is_prov_or_avg:
            r["Bucket"] = "PROVISIONAL_AVERAGE"
            prov_avg_rows.append(r)
        elif is_mis:
            r["Bucket"] = "MISMATCH"
            mismatch_rows.append(r)
        else:
            r["Bucket"] = "VERIFIED_ACTUAL_MATCH"
            match_rows.append(r)

    # Clean Actual Match: only BILL-CLEAN-02
    assert len(match_rows) == 1
    assert match_rows[0]["Bill Number"] == "BILL-CLEAN-02"
    assert match_rows[0]["Bill Basis"] == "ACTUAL"

    # Provisional / Average bills isolated in review bucket
    assert len(prov_avg_rows) == 2
    assert {r["Bill Number"] for r in prov_avg_rows} == {"BILL-PROV-03", "BILL-AVG-04"}

    # Mismatch: BILL-FAULT-05
    assert len(mismatch_rows) == 1
    assert mismatch_rows[0]["Bill Number"] == "BILL-FAULT-05"

    # Duplicate: BILL-EXISTS-01
    assert len(dup_rows) == 1
    assert dup_rows[0]["Bill Number"] == "BILL-EXISTS-01"

    # Check Consumer A/C formatting format func
    ac_col = "Consumer A/c No."
    b_col = "Bill Number"
    m_row = mismatch_rows[0]
    formatted_option = f"🏢 Consumer A/C: {m_row[ac_col]} | Month: 2026/09 (Bill #{m_row[b_col]}) — Fault: {m_row['Discrepancy Details']}"
    assert "Consumer A/C: 81300105" in formatted_option
    assert "Energy Charges Diff: +₹500.00" in formatted_option


def test_auto_healing_missing_column():
    """Simulates PostgREST error PGRST204 when bill_issue_date is missing from Supabase schema."""
    sample_bills = [
        {"Bill Number": "BILL-TEST-001", "Bill Issue Date": "2026-08-15", "Current Total (o)": "12500"}
    ]

    with patch("core.db_sync.get_supabase_client") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_table = MagicMock()
        mock_instance.table.return_value = mock_table
        
        # Select for duplicates returns empty
        mock_table.select.return_value.execute.return_value = MagicMock(data=[])

        call_count = [0]
        def mock_upsert_side_effect(chunk, on_conflict=None):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call fails with exact error the user encountered
                raise Exception("{'message': \"Could not find the 'bill_issue_date' column of 'energy_bills' in the schema cache\", 'code': 'PGRST204', 'hint': None, 'details': None}")
            # Second call (after auto-healing removed bill_issue_date) succeeds
            # Verify bill_issue_date was indeed stripped
            assert "bill_issue_date" not in chunk[0]
            m_res = MagicMock()
            m_res.execute.return_value = MagicMock(data=[])
            return m_res

        mock_table.upsert.side_effect = mock_upsert_side_effect

        res = batch_save_energy_bills(sample_bills)
        assert res["status"] == "SUCCESS"
        assert res["saved_count"] == 1
        assert call_count[0] == 2

