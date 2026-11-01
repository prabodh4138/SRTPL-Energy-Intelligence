from fastapi import APIRouter
import sys
import os
import pandas as pd
from typing import Any

# Ensure active_app is in sys.path
APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "active_app"))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from core.db_sync import (
    get_unified_billing_kpi_dataset,
    get_all_consumer_accounts,
    get_bill_review_queue,
    get_audit_events,
    get_budget_vs_actual,
    _clean_kpi_num,
)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary")
def get_dashboard_summary(
    toll_plaza: str = "ALL",
    bill_month: str = "ALL",
    bill_type: str = "ALL",
) -> dict[str, Any]:
    raw_df = get_unified_billing_kpi_dataset()

    filtered_df = raw_df.copy() if not raw_df.empty else pd.DataFrame()
    if not filtered_df.empty:
        if toll_plaza != "ALL" and "toll_plaza_id" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["toll_plaza_id"] == toll_plaza]
        if bill_month != "ALL" and "bill_month" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["bill_month"] == bill_month]
        if bill_type != "ALL" and "bill_type" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["bill_type"] == bill_type]

    review_queue_df = get_bill_review_queue()
    audit_events_df = get_audit_events()
    budget_df = get_budget_vs_actual()

    official_posted = (
        filtered_df[
            (filtered_df.get("bill_basis", "ACTUAL") == "ACTUAL")
            & (~filtered_df.get("is_voided", False).astype(bool))
        ]
        if not filtered_df.empty
        else pd.DataFrame()
    )

    total_bills_found = len(filtered_df)
    held_review_count = len(review_queue_df)
    posted_count = len(official_posted)
    dup_rejected_count = (
        len(audit_events_df[audit_events_df["result"] == "DUPLICATE_REJECTED"])
        if not audit_events_df.empty
        else 0
    )
    total_bill_amount = (
        float(official_posted["total_amount_payable"].sum())
        if not official_posted.empty
        else 0.0
    )
    total_paid_amount = (
        float(official_posted["amount_paid"].sum())
        if not official_posted.empty
        else 0.0
    )
    total_outstanding = (
        float(official_posted["outstanding_balance"].sum())
        if not official_posted.empty
        else 0.0
    )

    # Plaza comparison
    plazas_summary = []
    for p in ["TP01", "TP02", "TP03"]:
        p_df = (
            official_posted[official_posted.get("toll_plaza_id") == p]
            if not official_posted.empty
            else pd.DataFrame()
        )
        p_amt = float(p_df["total_amount_payable"].sum()) if not p_df.empty else 0.0
        p_units = float(p_df["total_billed_kwh"].sum()) if not p_df.empty and "total_billed_kwh" in p_df.columns else 0.0
        plazas_summary.append({
            "plaza_id": p,
            "bill_count": len(p_df),
            "total_amount": round(p_amt, 2),
            "total_kwh": round(p_units, 2),
        })

    # Dynamic trend dataset for charts (returns empty list if no bills uploaded)
    trend = []
    if not official_posted.empty and "bill_month" in official_posted.columns:
        for m, grp in official_posted.groupby("bill_month", sort=False):
            trend.append({
                "month": str(m),
                "eb_units": round(float(grp["total_billed_kwh"].sum()) if "total_billed_kwh" in grp.columns else 0.0, 2),
                "dg_units": 0.0,
                "solar_units": 0.0,
                "billed_amount": round(float(grp["total_amount_payable"].sum()) if "total_amount_payable" in grp.columns else 0.0, 2),
            })

    return {
        "kpis": {
            "total_bills_found": total_bills_found,
            "held_for_review": held_review_count,
            "verified_posted": posted_count,
            "duplicates_rejected": dup_rejected_count,
            "total_bill_amount": round(total_bill_amount, 2),
            "total_paid_amount": round(total_paid_amount, 2),
            "total_outstanding": round(total_outstanding, 2),
        },
        "plazas": plazas_summary,
        "trend": trend,
    }
