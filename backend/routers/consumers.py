from fastapi import APIRouter
import sys
import os
from typing import Any

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "active_app"))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from core.db_sync import get_all_consumer_accounts

router = APIRouter(prefix="/api/consumers", tags=["Consumers"])


@router.get("/")
def get_consumers(plaza: str = "ALL", bill_type: str = "ALL") -> dict[str, Any]:
    c_df = get_all_consumer_accounts()
    if c_df.empty:
        return {"total": 0, "ht_count": 0, "lt_count": 0, "consumers": []}

    filtered = c_df.copy()
    if plaza != "ALL" and "toll_plaza_id" in filtered.columns:
        filtered = filtered[filtered["toll_plaza_id"] == plaza]
    if bill_type != "ALL" and "bill_type" in filtered.columns:
        filtered = filtered[filtered["bill_type"] == bill_type]

    ht_count = len(c_df[c_df["bill_type"] == "HT"]) if "bill_type" in c_df.columns else 3
    lt_count = len(c_df[c_df["bill_type"] == "LT"]) if "bill_type" in c_df.columns else 57

    return {
        "total": len(c_df),
        "ht_count": ht_count,
        "lt_count": lt_count,
        "filtered_count": len(filtered),
        "consumers": filtered.to_dict(orient="records"),
    }
