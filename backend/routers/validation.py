from fastapi import APIRouter
from typing import Any
import sys
import os

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "active_app"))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from core.db_sync import get_audit_events, get_bill_review_queue
from core.supabase_manager import get_supabase_client

router = APIRouter(prefix="/api/validation", tags=["Validation"])


@router.get("/summary")
def get_validation_summary() -> dict[str, Any]:
    events_df = get_audit_events()
    queue_df = get_bill_review_queue()

    anomalies: list[dict[str, Any]] = []

    # Fetch live anomalies from Supabase exception table if connected
    client = get_supabase_client()
    if client:
        try:
            res = client.schema("energy_validation").table("exception_record").select("*").execute()
            if res and res.data:
                for r in res.data:
                    anomalies.append({
                        "id": str(r.get("id") or r.get("rule_code") or "EXC"),
                        "rule": str(r.get("rule_code") or "VALIDATION"),
                        "equipment": str(r.get("source_type") or "Telemetry"),
                        "asset_code": str(r.get("asset_id") or "—"),
                        "description": str(r.get("message") or "Anomaly detected"),
                        "severity": str(r.get("severity") or "MEDIUM"),
                        "status": str(r.get("status") or "OPEN"),
                        "detected_at": str(r.get("created_at") or ""),
                    })
        except Exception:
            pass

    # Combine review queue items into exception records (only when real held bills exist)
    if not queue_df.empty:
        for idx, row in queue_df.iterrows():
            anomalies.append({
                "id": f"BILL-HOLD-{idx+1}",
                "rule": row.get("hold_reason_code", "ARITHMETIC_MISMATCH"),
                "equipment": "Energy Bill",
                "asset_code": str(row.get("consumer_account_no", "—")),
                "description": str(row.get("exception_reason", "Bill held in review queue")),
                "severity": "HIGH",
                "status": "HELD_FOR_REVIEW",
                "detected_at": str(row.get("created_at", "")),
            })

    audit_logs = events_df.to_dict(orient="records") if not events_df.empty else []

    open_count = len([a for a in anomalies if a.get("status") in ["OPEN", "HELD_FOR_REVIEW"]])
    critical_count = sum(1 for a in anomalies if a.get("severity") == "HIGH")
    investigating_count = sum(1 for a in anomalies if a.get("status") == "INVESTIGATING")

    return {
        "kpis": {
            "total_open_exceptions": open_count,
            "critical_holds": critical_count,
            "investigating": investigating_count,
            "resolved_today": 0,
        },
        "exceptions": anomalies,
        "audit_logs": audit_logs,
    }
