"""Cloud-Level & SQL View Tests for Equipment Reading Dashboard & In-Memory Extraction.

Verifies:
1. All 11 SQL Views exist and return authoritative KPIs and latest asset readings.
2. Every inventoried asset (27 total across EB, DG, Solar, Transformer, UPS) has a latest reading record.
3. KPIs are strictly fetched from SQL Views (vw_<module>_reading_kpis).
4. In-memory data extraction generates valid CSV and Excel files with ZERO temporary files on disk.
5. Cloud Supabase client queries and fallback mechanisms function correctly.
6. FastAPI endpoints for SQL KPIs, Latest Assets, and In-Memory Export.
"""
from __future__ import annotations

import io
from pathlib import Path
import sys
from typing import Any
from unittest.mock import MagicMock
import pandas as pd
import pytest

ACTIVE_APP = Path(__file__).resolve().parents[1]
if str(ACTIVE_APP) not in sys.path:
    sys.path.insert(0, str(ACTIVE_APP))

from core.cloud_views_service import (
    fetch_module_kpis_from_sql_view,
    fetch_asset_latest_readings_from_sql_view,
    extract_equipment_readings_in_memory,
)
from core.local_db import get_sqlite_connection, init_local_db
from backend.routers.readings import get_sql_kpis, get_latest_assets, export_readings


@pytest.fixture(autouse=True)
def ensure_db_initialized():
    """Ensure local SQLite schema and views are initialized."""
    init_local_db()


def test_sql_views_exist_in_db():
    """Verify that all 11 required SQL views exist and can be queried."""
    expected_views = [
        "vw_eb_reading_kpis",
        "vw_eb_asset_latest_reading",
        "vw_dg_reading_kpis",
        "vw_dg_asset_latest_reading",
        "vw_solar_reading_kpis",
        "vw_solar_asset_latest_reading",
        "vw_transformer_reading_kpis",
        "vw_transformer_asset_latest_reading",
        "vw_ups_reading_kpis",
        "vw_ups_asset_latest_reading",
        "vw_all_assets_latest_reading",
    ]

    conn = get_sqlite_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='view'")
    existing_views = {row[0] for row in cur.fetchall()}
    conn.close()

    for view_name in expected_views:
        assert view_name in existing_views, f"View '{view_name}' is missing from database schema!"


@pytest.mark.parametrize("module", ["eb", "dg", "solar", "transformer", "ups"])
def test_kpis_fetched_from_sql_views(module: str):
    """Verify that executive KPIs are fetched directly from SQL Views."""
    res = fetch_module_kpis_from_sql_view(module)
    assert res is not None
    assert res.get("source_type") == module.upper()

    raw = res.get("raw_record")
    assert isinstance(raw, dict), "raw_record must be a dict returned from the SQL view"
    assert "source_type" in raw, f"SQL view vw_{module}_reading_kpis must return source_type column"

    cards = res.get("cards")
    assert isinstance(cards, list)
    assert len(cards) >= 4, f"{module.upper()} must have at least 4 executive KPI display cards"

    for card in cards:
        assert "label" in card
        assert "value" in card
        assert card["value"] != ""
        assert card.get("sub") is not None


@pytest.mark.parametrize("module, expected_count", [
    ("eb", 9),
    ("dg", 6),
    ("solar", 3),
    ("transformer", 3),
    ("ups", 6),
])
def test_last_reading_of_each_asset_completeness(module: str, expected_count: int):
    """Verify that every inventoried asset is present in the latest reading view."""
    df = fetch_asset_latest_readings_from_sql_view(module)
    assert not df.empty, f"Latest readings DataFrame for {module} must not be empty"
    assert len(df) == expected_count, f"Expected {expected_count} assets for {module}, found {len(df)}"

    required_cols = ["asset_id", "asset_code", "asset_name", "plaza_id", "capacity_kva", "reading_datetime"]
    for col in required_cols:
        assert col in df.columns, f"Column '{col}' must be present in vw_{module}_asset_latest_reading"

    # All assets must have non-blank codes and plazas
    assert df["asset_code"].str.len().gt(0).all()
    assert df["plaza_id"].isin(["TP01", "TP02", "TP03"]).all()

    # Test filtering by toll plaza
    tp01_df = fetch_asset_latest_readings_from_sql_view(module, plaza="TP01")
    assert not tp01_df.empty
    assert (tp01_df["plaza_id"] == "TP01").all()


def test_vw_all_assets_latest_reading_returns_27_assets():
    """Verify that the master unified view aggregates all 27 assets across the corridor."""
    conn = get_sqlite_connection()
    df = pd.read_sql_query("SELECT * FROM vw_all_assets_latest_reading", conn)
    conn.close()

    assert len(df) == 27, f"Expected 27 total corridor assets, found {len(df)}"
    source_counts = df["source_type"].value_counts().to_dict()
    assert source_counts.get("EB") == 9
    assert source_counts.get("DG") == 6
    assert source_counts.get("SOLAR") == 3
    assert source_counts.get("TRANSFORMER") == 3
    assert source_counts.get("UPS") == 6


@pytest.mark.parametrize("module", ["eb", "dg", "solar", "transformer", "ups"])
def test_in_memory_csv_extraction_no_temporary_file(module: str, monkeypatch):
    """Verify CSV extraction is 100% in-memory with zero disk temporary files."""
    orig_open = open
    opened_files = []

    def mock_open(*args, **kwargs):
        file = args[0] if args else kwargs.get("file")
        mode = kwargs.get("mode") or (args[1] if len(args) > 1 else "r")
        if any(m in mode for m in ("w", "a", "x")):
            opened_files.append(str(file))
        return orig_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", mock_open)

    csv_bytes, filename = extract_equipment_readings_in_memory(module, format_type="csv")

    assert isinstance(csv_bytes, bytes)
    assert len(csv_bytes) > 0
    assert filename.endswith(".csv")
    assert module.upper() in filename

    # Parse in-memory bytes back to verify valid CSV
    df = pd.read_csv(io.BytesIO(csv_bytes))
    assert not df.empty
    assert "asset_code" in df.columns

    # Verify ZERO disk files were created
    assert len(opened_files) == 0, f"Temporary file was written to disk: {opened_files}"


@pytest.mark.parametrize("module", ["eb", "dg", "solar", "transformer", "ups"])
def test_in_memory_excel_extraction_no_temporary_file(module: str, monkeypatch):
    """Verify Excel extraction is 100% in-memory with zero disk temporary files."""
    orig_open = open
    opened_files = []

    def mock_open(*args, **kwargs):
        file = args[0] if args else kwargs.get("file")
        mode = kwargs.get("mode") or (args[1] if len(args) > 1 else "r")
        if any(m in mode for m in ("w", "a", "x")):
            opened_files.append(str(file))
        return orig_open(*args, **kwargs)

    monkeypatch.setattr("builtins.open", mock_open)

    xlsx_bytes, filename = extract_equipment_readings_in_memory(module, format_type="excel")

    assert isinstance(xlsx_bytes, bytes)
    assert len(xlsx_bytes) > 0
    assert filename.endswith(".xlsx")
    # Check ZIP/Excel magic bytes (PK..)
    assert xlsx_bytes[:2] == b"PK"

    # Read back directly in-memory
    excel_file = pd.ExcelFile(io.BytesIO(xlsx_bytes), engine="openpyxl")
    assert "Latest_Per_Asset" in excel_file.sheet_names
    assert "Historical_Logs" in excel_file.sheet_names

    latest_sheet = pd.read_excel(excel_file, sheet_name="Latest_Per_Asset")
    assert not latest_sheet.empty
    assert "asset_code" in latest_sheet.columns

    # Verify ZERO disk files were created
    assert len(opened_files) == 0, f"Temporary file was written to disk: {opened_files}"


def test_cloud_supabase_client_mock_integration(monkeypatch):
    """Verify that when Supabase client is connected, cloud views are queried first."""
    mock_client = MagicMock()
    mock_query = MagicMock()
    mock_response = MagicMock()

    mock_response.data = [{
        "source_type": "DG",
        "active_generators": 6,
        "total_cumulative_kwh": 120500.0,
        "total_interval_kwh": 450.0,
        "total_cumulative_run_hours": 1820.0,
        "total_interval_run_hours": 12.5,
        "total_fuel_level": 5400.0,
        "avg_power_factor": 0.98,
        "total_log_count": 950,
        "valid_count": 948,
        "exception_count": 2,
    }]
    mock_query.execute.return_value = mock_response
    mock_query.select.return_value = mock_query
    mock_client.table.return_value = mock_query

    monkeypatch.setattr("core.cloud_views_service.get_supabase_client", lambda: mock_client)

    res = fetch_module_kpis_from_sql_view("dg")
    assert res["raw_record"]["total_cumulative_kwh"] == 120500.0
    assert mock_client.table.called
    assert mock_client.table.call_args[0][0] == "vw_dg_reading_kpis"


def test_cloud_supabase_fallback_on_network_error(monkeypatch):
    """Verify that if cloud Supabase query fails, system falls back to local SQLite view parity."""
    mock_client = MagicMock()
    mock_client.table.side_effect = Exception("Cloud network unreachable")
    mock_client.schema.side_effect = Exception("Cloud network unreachable")

    monkeypatch.setattr("core.cloud_views_service.get_supabase_client", lambda: mock_client)

    res = fetch_module_kpis_from_sql_view("dg")
    assert res is not None
    # Fallback to local SQLite succeeds
    assert "raw_record" in res
    assert res["raw_record"].get("source_type") == "DG"


def test_fastapi_reading_endpoints():
    """Verify FastAPI backend endpoints for SQL KPIs, Latest Assets, and Export."""
    # 1. SQL KPIs endpoint
    kpi_res = get_sql_kpis("dg")
    assert kpi_res["source_type"] == "DG"
    assert len(kpi_res["cards"]) >= 4

    # 2. Latest Assets endpoint
    assets_res = get_latest_assets("dg")
    assert assets_res["source_type"] == "DG"
    assert assets_res["count"] == 6
    assert len(assets_res["assets"]) == 6

    # 3. In-memory CSV Export endpoint
    csv_resp = export_readings("dg", format="csv")
    assert csv_resp.media_type == "text/csv"
    assert "attachment; filename=DG_Readings_" in csv_resp.headers["Content-Disposition"]
    assert len(csv_resp.body) > 0

    # 4. In-memory Excel Export endpoint
    xlsx_resp = export_readings("dg", format="excel")
    assert xlsx_resp.media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "attachment; filename=DG_Readings_and_Last_Asset_Status_" in xlsx_resp.headers["Content-Disposition"]
    assert len(xlsx_resp.body) > 0
