"""
Comprehensive Verification Test Suite for SRTPL Energy Command Center
Matches all requirements and Acceptance Checklist in:
'SRTPL ENERGY COMMAND CENTER - Application Requirements, Dashboard Design & Scope-Control Summary'
"""
import os
import sys
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import json
from backend.routers.energy_command import (
    get_energy_overview,
    get_assets,
    create_asset,
    update_asset,
    deactivate_asset,
    get_readings,
    correct_reading,
    add_manual_reading,
    get_exceptions,
    review_exception,
    export_energy_excel,
    export_energy_pdf,
    export_backup,
    restore_backup,
    get_audit_log,
    AssetCreatePayload,
    AssetEditPayload,
    ReadingCorrectionPayload,
    ReadingManualEntryPayload,
    ExceptionReviewPayload,
    RestorePayload,
)

def test_acceptance_checklist_energy_overview_separate_and_honest_metrics():
    """
    Acceptance Criteria:
    - Energy Overview is separate from existing Bill/Reconciliation.
    - Use TP01, TP02, TP03 only until plaza names are verified.
    - KPI values use approved calculation rules and show reporting period/status.
    - TP02/TP03 DG absence shows unavailable, not zero.
    - Solar capacity uses kWp, not kVA (121.38 kWp total).
    - Energy Cost and Solar Saving remain unavailable until inputs verified.
    """
    data = get_energy_overview(plaza_id="ALL", period="reviewed_baseline")
    assert data["status"] == "SUCCESS"
    assert data["title"] == "SRTPL ENERGY COMMAND CENTER"

    # 1. EB Consumption
    eb = data["kpis"]["eb"]
    assert eb["value"] == 2672.4
    assert eb["total"] == 2672.4
    assert eb["tp01"] == 926.20
    assert eb["tp02"] == 945.70
    assert eb["tp03"] == 800.50
    assert eb["unit"] == "kWh"
    assert "08:00" in eb["schedule"]

    # 2. DG Generation & Honest Metrics (TP02/TP03 DG shows unavailable, not zero!)
    dg = data["kpis"]["dg"]
    assert dg["confirmed_kwh"] == 11590.60
    assert dg["unverified_kwh"] == 3.00
    assert dg["runtime_hours"] == 441.18
    assert dg["runtime_minutes"] == 26471

    plazas = {p["plaza_id"]: p for p in data["plaza_comparison"]}
    assert "TP01" in plazas and "TP02" in plazas and "TP03" in plazas
    assert plazas["TP01"]["dg_available"] is True
    assert plazas["TP01"]["dg_kwh"] == 11590.60
    assert plazas["TP02"]["dg_available"] is False
    assert plazas["TP02"]["dg_kwh"] is None
    assert plazas["TP02"]["dg_display"] == "No DG readings available"
    assert plazas["TP03"]["dg_available"] is False
    assert plazas["TP03"]["dg_kwh"] is None
    assert plazas["TP03"]["dg_display"] == "No DG readings available"

    # 3. Solar Generation (capacity in kWp, not kVA; daily interval vs month-end snapshot kept strictly separate)
    solar = data["kpis"]["solar"]
    assert solar["daily_interval_total_kwh"] == 54380
    assert solar["tp01"] == 18440
    assert solar["tp02"] == 17921
    assert solar["tp03"] == 18019
    assert solar["month_end_snapshot_total_kwh"] == 27502
    assert solar["total_capacity_kwp"] == 121.38
    assert solar["per_asset_capacity_kwp"] == 40.46
    assert solar["capacity_unit"] == "kWp"

    # 4. Energy Cost and Solar Saving unavailable until inputs verified
    assert data["kpis"]["energy_cost"]["value"] is None
    assert data["kpis"]["energy_cost"]["display_value"] == "Unavailable"
    assert "tariff pending" in data["kpis"]["energy_cost"]["subtitle"].lower()
    assert data["kpis"]["solar_saving"]["value"] is None
    assert data["kpis"]["solar_saving"]["display_value"] == "Unavailable"

    # 5. Operations Snapshot
    snap = data["operations_snapshot"]
    assert snap["dg_running_time"] == "441.18 h"
    assert snap["solar_capacity"] == "121.38 kWp"
    assert snap["open_exceptions"] >= 25
    assert snap["cost_saving"] == "Await verified inputs"
    assert snap["plaza_ids"] == ["TP01", "TP02", "TP03"]

    # 6. Transformer Rules
    trf = data["transformer_rules"]
    assert "49–51 Hz" in trf["frequency_range"]
    assert "9,800–11,800 V" in trf["primary_voltage"]
    assert "380–450 V" in trf["secondary_voltage"]
    assert "5%" in trf["clean_voltage_imbalance"]
    assert "30%" in trf["clean_current_imbalance"]


def test_asset_master_solar_capacity_rule():
    """
    Acceptance Criteria:
    - Search assets, inspect verified capacities.
    - Solar capacity uses kWp, not kVA (Three Solar assets, each 40.46 kWp; total 121.38 kWp).
    """
    data = get_assets(plaza_id=None, source_type=None, search=None)
    assert data["status"] == "SUCCESS"
    assert data["solar_capacity_total_kwp"] == 121.38
    assert len(data["assets"]) >= 27

    solar_assets = [a for a in data["assets"] if a["source_type"] == "SOLAR"]
    assert len(solar_assets) == 3
    for s in solar_assets:
        assert s["capacity"] == 40.46
        assert s["capacity_unit"] == "kWp"


def test_controlled_reading_correction_and_audit():
    """
    Acceptance Criteria:
    - Search reading -> compare original and proposed values -> enter mandatory reason -> confirm
    - Backend records timestamp, actor, old/new values.
    - No automatic correction; source records preserved.
    """
    payload = ReadingCorrectionPayload(
        reading_id="TEST-EB-001",
        module="eb",
        asset_code="SR-E-EM-EB-000TP01",
        plaza_id="TP01",
        field_name="cumulative_kwh",
        original_value=92600.0,
        proposed_value=92620.0,
        reason="Calibration certificate correction for TP01 meter",
        actor="admin@srtpl.com"
    )
    data = correct_reading(payload)
    assert data["status"] == "SUCCESS"
    assert "correction_id" in data

    # Verify audit log recorded this event
    res_aud = get_audit_log(limit=100)
    assert res_aud["status"] == "SUCCESS"
    logs = res_aud["logs"]
    matching = [l for l in logs if l["action_type"] == "READING_CORRECTION" and l["entity_id"] == "TEST-EB-001"]
    assert len(matching) > 0
    assert matching[0]["actor"] == "admin@srtpl.com"
    assert matching[0]["reason"] == "Calibration certificate correction for TP01 meter"
    assert "92600.0" in matching[0]["old_value"]
    assert "92620.0" in matching[0]["new_value"]


def test_reviewed_open_exceptions_snapshot():
    """
    Acceptance Criteria:
    - 28 open exceptions in the reviewed snapshot:
      * 1 critical DG cumulative decrease
      * 16 DG source exceptions (warnings)
      * 11 Transformer cumulative decreases (warnings)
    - Review exception: inspect source values, propose correction or mark reviewed with mandatory reason.
    """
    data = get_exceptions(severity="ALL", status="ALL", plaza_id="ALL", module="ALL")
    assert data["status"] == "SUCCESS"
    assert data["total_exceptions"] >= 28
    assert data["critical_count"] >= 1
    assert data["warning_count"] >= 27

    # Check the 1 critical DG decrease
    crit_dg = [e for e in data["exceptions"] if e["severity"] == "CRITICAL" and "DG" in e["rule_code"]]
    assert len(crit_dg) >= 1
    assert "VAL-DG-001" in crit_dg[0]["rule_code"]

    # Review the exception with mandatory reason
    exc_id = crit_dg[0]["exception_id"]
    rev_payload = ExceptionReviewPayload(
        action="MARK_REVIEWED",
        reason="Supervisor reviewed cumulative decrement; logged for field inspection",
        actor="admin@srtpl.com"
    )
    res_rev = review_exception(exc_id, rev_payload)
    assert res_rev["status"] == "SUCCESS"
    assert res_rev["new_status"] == "REVIEWED"


def test_energy_specific_exports_and_verifiable_backup():
    """
    Acceptance Criteria:
    - New energy-only Excel/PDF exports; existing Reports module remains untouched.
    - Backup/export, restore procedure, audit log.
    - Restore requires explicit confirmation (confirm: true).
    """
    # 1. Excel export
    res_xl = export_energy_excel()
    assert res_xl.status_code == 200
    assert "spreadsheetml" in res_xl.media_type

    # 2. PDF/Text report
    res_pdf = export_energy_pdf()
    assert res_pdf.status_code == 200
    assert b"SRTPL ENERGY COMMAND CENTER" in res_pdf.body
    assert b"2,672.40 kWh" in res_pdf.body
    assert b"11,590.60 confirmed kWh" in res_pdf.body

    # 3. Verifiable Backup
    res_bak = export_backup()
    assert res_bak.status_code == 200
    bak_data = json.loads(res_bak.body.decode("utf-8"))
    assert "sha256_checksum" in bak_data
    assert "record_counts" in bak_data

    # 4. Restore requires explicit confirmation
    import fastapi
    try:
        restore_backup(RestorePayload(
            confirm=False,
            reason="Test without confirmation",
            actor="admin@srtpl.com",
            backup_json=json.dumps(bak_data)
        ))
        assert False, "Should have raised HTTPException"
    except fastapi.HTTPException as exc:
        assert exc.status_code == 400

    # With confirmation
    res_rest_ok = restore_backup(RestorePayload(
        confirm=True,
        reason="Emergency recovery test procedure",
        actor="admin@srtpl.com",
        backup_json=json.dumps(bak_data)
    ))
    assert res_rest_ok["status"] == "SUCCESS"


def test_module7_analytics_views_deployed_and_ready():
    """
    Acceptance Criteria:
    - Module 7 SQL views deployed and accessible:
      vw_dg71_daily_summary, vw_m7_entry_audit, vw_m7_exception_register, vw_m7_asset_latest_reading
    - All 5 submodules (DG, EB, SOLAR, TRANSFORMER, UPS) return READY with has_data=True
    - Total records equal valid + exception records (reconciliation diff == 0)
    - Non-existent plaza filter returns honest has_data=False
    """
    from backend.routers.energy_command import get_module_analytics

    # 1. DG Analytics & Required Views
    dg_res = get_module_analytics(module_name="DG", plaza_id="ALL", period="daily")
    assert dg_res["status"] == "SUCCESS"
    dg_data = dg_res["data"]
    assert dg_data["status"] == "READY"
    assert dg_data["has_data"] is True
    assert dg_data["summary"]["total_records"] == 1951
    assert dg_data["summary"]["reconciliation_difference"] == 0
    assert len(dg_data["latest_readings"]) == 6
    assert len(dg_data["technicians"]) > 0

    # Verify required views list
    assert "vw_dg71_daily_summary" in dg_data["required_views"]
    assert "vw_m7_entry_audit" in dg_data["required_views"]
    assert "vw_m7_exception_register" in dg_data["required_views"]
    assert "vw_m7_asset_latest_reading" in dg_data["required_views"]

    # 2. EB Analytics
    eb_res = get_module_analytics(module_name="EB", plaza_id="ALL", period="daily")
    assert eb_res["data"]["status"] == "READY"
    assert eb_res["data"]["has_data"] is True
    assert eb_res["data"]["summary"]["total_records"] == 206
    assert eb_res["data"]["summary"]["reconciliation_difference"] == 0

    # 3. Solar Analytics
    sol_res = get_module_analytics(module_name="SOLAR", plaza_id="ALL", period="daily")
    assert sol_res["data"]["status"] == "READY"
    assert sol_res["data"]["has_data"] is True
    assert sol_res["data"]["summary"]["total_records"] == 517
    assert sol_res["data"]["summary"]["reconciliation_difference"] == 0

    # 4. Transformer Analytics
    trf_res = get_module_analytics(module_name="TRANSFORMER", plaza_id="ALL", period="daily")
    assert trf_res["data"]["status"] == "READY"
    assert trf_res["data"]["has_data"] is True
    assert trf_res["data"]["summary"]["total_records"] == 1549
    assert trf_res["data"]["summary"]["reconciliation_difference"] == 0

    # 5. UPS Analytics
    ups_res = get_module_analytics(module_name="UPS", plaza_id="ALL", period="daily")
    assert ups_res["data"]["status"] == "READY"
    assert ups_res["data"]["has_data"] is True
    assert ups_res["data"]["summary"]["total_records"] == 9015
    assert ups_res["data"]["summary"]["reconciliation_difference"] == 0

    # 6. Honest No-Data Behavior for Non-Existent Filter
    nodata_res = get_module_analytics(module_name="DG", plaza_id="TP99")
    assert nodata_res["data"]["status"] == "READY"
    assert nodata_res["data"]["has_data"] is False
    assert "No readings found" in nodata_res["data"]["message"]


if __name__ == "__main__":
    test_acceptance_checklist_energy_overview_separate_and_honest_metrics()
    print("PASS: test_acceptance_checklist_energy_overview_separate_and_honest_metrics")
    test_asset_master_solar_capacity_rule()
    print("PASS: test_asset_master_solar_capacity_rule")
    test_controlled_reading_correction_and_audit()
    print("PASS: test_controlled_reading_correction_and_audit")
    test_reviewed_open_exceptions_snapshot()
    print("PASS: test_reviewed_open_exceptions_snapshot")
    test_energy_specific_exports_and_verifiable_backup()
    print("PASS: test_energy_specific_exports_and_verifiable_backup")
    test_module7_analytics_views_deployed_and_ready()
    print("PASS: test_module7_analytics_views_deployed_and_ready")
    print("\nALL TEST SUITE CHECKS PASSED 100%!")
