from __future__ import annotations

from pathlib import Path
import pytest

from core.live_pipeline import (
    execute_live_juno_ingestion,
    clear_local_ingestion_hashes,
)
from core.supabase_manager import remove_all_database_data

ROOT = Path(__file__).resolve().parents[2]
SAMPLE_EB = ROOT / "source_data" / "raw" / "EB" / "SRTPL_Test_JUNO_EB.csv"
SAMPLE_DG = ROOT / "source_data" / "raw" / "DG" / "DGDailyLogReport_25thSep2026_443_DG Log.csv"
SAMPLE_SOLAR = ROOT / "source_data" / "raw" / "Solar" / "Solar_Plant_Log_25thSep2026_2719_Solar Log.csv"
SAMPLE_TRF = ROOT / "source_data" / "raw" / "Transformer" / "TransformerDailyReport_25thSep2026_2116_Transformer Daily Log Report.csv"
SAMPLE_UPS = ROOT / "source_data" / "raw" / "UPS" / "UPSDailyLogReport_25thSep2026_2140_UPS Daily Log Report.csv"


def test_eb_ingestion_and_duplicate_prevention():
    clear_local_ingestion_hashes()

    # First ingestion -> SUCCESS
    res1 = execute_live_juno_ingestion(SAMPLE_EB, expected_type="EB")
    assert res1["status"] == "SUCCESS"
    assert res1["success"] is True
    assert res1["report_type"] == "EB"
    assert res1["total_records"] == 7
    assert len(res1["kpis"]) > 0

    # Second ingestion of exact same file -> DUPLICATE_FILE (Level 1 rejection)
    res2 = execute_live_juno_ingestion(SAMPLE_EB, expected_type="EB")
    assert res2["status"] == "DUPLICATE_FILE"
    assert res2["success"] is False
    assert "DUPLICATE FILE REJECTED" in res2["message"]


def test_dg_ingestion():
    clear_local_ingestion_hashes()
    res = execute_live_juno_ingestion(SAMPLE_DG, expected_type="DG")
    assert res["status"] == "SUCCESS"
    assert res["success"] is True
    assert res["report_type"] == "DG"
    assert res["total_records"] > 0
    assert res["valid_rows"] > 0


def test_solar_ingestion():
    clear_local_ingestion_hashes()
    res = execute_live_juno_ingestion(SAMPLE_SOLAR, expected_type="SOLAR")
    assert res["status"] == "SUCCESS"
    assert res["success"] is True
    assert res["report_type"] == "SOLAR"
    assert res["total_records"] > 0


def test_transformer_ingestion():
    clear_local_ingestion_hashes()
    res = execute_live_juno_ingestion(SAMPLE_TRF, expected_type="TRANSFORMER")
    assert res["status"] == "SUCCESS"
    assert res["success"] is True
    assert res["report_type"] == "TRANSFORMER"
    assert res["total_records"] > 0


def test_ups_ingestion():
    clear_local_ingestion_hashes()
    res = execute_live_juno_ingestion(SAMPLE_UPS, expected_type="UPS")
    assert res["status"] == "SUCCESS"
    assert res["success"] is True
    assert res["report_type"] == "UPS"
    assert res["total_records"] > 0


def test_wipe_and_reset_clears_hashes():
    clear_local_ingestion_hashes()
    res1 = execute_live_juno_ingestion(SAMPLE_EB, expected_type="EB")
    assert res1["status"] == "SUCCESS"

    # Wiping data clears hashes
    wipe_res = remove_all_database_data()
    assert wipe_res["status"] == "SUCCESS"

    # Now the file can be ingested again after clean wipe
    res2 = execute_live_juno_ingestion(SAMPLE_EB, expected_type="EB")
    assert res2["status"] == "SUCCESS"


def test_import_repository_generates_batch_id():
    from unittest.mock import MagicMock
    from supabase_import.repository import ImportRepository

    mock_db = MagicMock()
    # Mock insert failure or success to test fallback behavior
    mock_db.table.side_effect = Exception("Not connected")
    mock_db.schema.side_effect = Exception("Not connected")

    repo = ImportRepository(mock_db)
    payload = {"source_system": "JUNO", "report_type": "EB"}
    batch = repo.create_batch(payload)
    assert "import_batch_id" in batch
    assert batch["import_batch_id"] is not None
    assert len(batch["import_batch_id"]) > 0

    file_payload = {"original_filename": "test.csv"}
    file_record = repo.create_file(file_payload)
    assert "import_file_id" in file_record
    assert file_record["import_file_id"] is not None

    rows = [{"raw_payload": {"test": 1}}]
    created_rows = repo.create_rows(rows)
    assert len(created_rows) == 1
    assert "import_row_id" in created_rows[0]
