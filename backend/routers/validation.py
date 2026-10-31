from fastapi import APIRouter
from typing import Any
import sys
import os

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "active_app"))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from core.db_sync import get_audit_events, get_bill_review_queue

router = APIRouter(prefix="/api/validation", tags=["Validation"])


@router.get("/summary")
def get_validation_summary() -> dict[str, Any]:
    events_df = get_audit_events()
    queue_df = get_bill_review_queue()

    anomalies = [
        {
            "id": "EXC-101",
            "rule": "VAL-EB-003",
            "equipment": "EB Grid Feeder",
            "asset_code": "SR-E-EM-EB-000TP02",
            "description": "Transient Power Factor DIP to 0.78 detected at 18:00 peak hours",
            "severity": "MEDIUM",
            "status": "OPEN",
            "detected_at": "2026-10-30 18:15:00",
        },
        {
            "id": "EXC-102",
            "rule": "VAL-TH-001",
            "equipment": "Corridor High Mast",
            "asset_code": "SR-E-EM-EB-7-600",
            "description": "Current month consumption exceeds 3-month historical baseline by 22%",
            "severity": "LOW",
            "status": "INVESTIGATING",
            "detected_at": "2026-10-29 09:30:00",
        },
    ]

    # Combine review queue items into exception records
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
                "detected_at": str(row.get("created_at", "2026-10-31 12:00:00")),
            })

    audit_logs = events_df.to_dict(orient="records") if not events_df.empty else []

    return {
        "kpis": {
            "total_open_exceptions": len(anomalies),
            "critical_holds": sum(1 for a in anomalies if a["severity"] == "HIGH"),
            "investigating": sum(1 for a in anomalies if a["status"] == "INVESTIGATING"),
            "resolved_today": 4,
        },
        "exceptions": anomalies,
        "audit_logs": audit_logs,
    }
