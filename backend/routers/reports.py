import io
from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse
import pandas as pd
import sys
import os

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "active_app"))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from core.db_sync import (
    get_official_bill_register,
    get_all_consumer_accounts,
    get_receipt_reconciliation,
    get_budget_vs_actual,
    get_unified_billing_kpi_dataset,
)

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/summary")
def get_reports_summary():
    bills_df = get_official_bill_register()
    consumers_df = get_all_consumer_accounts()
    receipts_df = get_receipt_reconciliation()
    budget_df = get_budget_vs_actual()

    reports = [
        {"id": "REP-01", "name": "Authoritative Official Bill Register", "format": "Excel / CSV / PDF", "rows": len(bills_df), "category": "Financial Controls"},
        {"id": "REP-02", "name": "60 Consumer Master Roster (3 HT / 57 LT)", "format": "Excel / CSV", "rows": len(consumers_df), "category": "Master Data"},
        {"id": "REP-03", "name": "Payment Receipts Reconciliation & Allocations", "format": "Excel / CSV", "rows": len(receipts_df), "category": "Audit & Clearance"},
        {"id": "REP-04", "name": "Corridor Monthly Budget vs Actual Expenditure", "format": "Excel / CSV", "rows": len(budget_df), "category": "Executive"},
    ]
    return {"reports": reports}


@router.get("/download-bills-excel")
def download_bills_excel():
    df = get_official_bill_register()
    if df.empty:
        df = pd.DataFrame([{"Message": "Official Bill Register is currently empty."}])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Sheet 1: Comprehensive official data (includes bill_type, consumer_scope, sanctioned_load_kw & all 13 fields)
        df.to_excel(writer, index=False, sheet_name="Official_Energy_Bills")

        # Sheet 2: Executive Presentation with Formatted Column Titles
        if not df.empty and "bill_number" in df.columns:
            column_map = {
                "bill_number": "Bill Number",
                "consumer_account_no": "Consumer A/C No.",
                "toll_plaza_id": "Toll Plaza",
                "bill_type": "Feeder Type (HT/LT)",
                "consumer_scope": "Scope (PLAZA/HIGHWAY)",
                "sanctioned_load_kw": "Sanctioned Load (kW)",
                "contract_demand": "Contract Demand",
                "tariff_category": "Tariff Category",
                "security_deposit": "Security Deposit (Rs.)",
                "md": "MD",
                "cuml_md_kva": "CUML MD-KVA",
                "cuml_md_kw": "CUML MD-KW",
                "section": "Section",
                "sub_division": "Sub-Division",
                "rebate_date": "Rebate Date",
                "meter_sl_no": "Meter Sl. No.",
                "dps_rs": "DPS (Rs.)",
                "net_payable_amount_before_rbt_dt_rs": "Net Payable Before Rbt. Dt. (Rs.)",
                "net_payable_amount_after_rbt_dt_rs": "Net Payable After Rbt. Dt. (Rs.)",
                "bill_month": "Bill Month",
                "bill_basis": "Bill Basis",
                "total_billed_kwh": "Total Units (kWh)",
                "energy_charges": "Energy Charges (Rs.)",
                "demand_charge": "Demand Charge (Rs.)",
                "total_amount_payable": "Total Payable (Rs.)",
                "amount_paid": "Amount Paid (Rs.)",
                "outstanding_balance": "Outstanding (Rs.)",
                "payment_status": "Payment Status",
                "ai_model_applied": "AI Model Fit (100%)",
                "audit_verdict": "Arithmetic Verdict",
            }
            exec_cols = [c for c in column_map.keys() if c in df.columns]
            exec_df = df[exec_cols].rename(columns=column_map)
            exec_df.to_excel(writer, index=False, sheet_name="Executive_Summary")

    headers = {"Content-Disposition": 'attachment; filename="SRTPL_Official_Energy_Bills.xlsx"'}
    return Response(content=output.getvalue(), headers=headers, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/download-bills-csv")
def download_bills_csv():
    df = get_official_bill_register()
    if df.empty:
        df = pd.DataFrame([{"Message": "Official Bill Register is currently empty."}])

    csv_data = df.to_csv(index=False).encode("utf-8")
    headers = {"Content-Disposition": 'attachment; filename="SRTPL_Official_Energy_Bills.csv"'}
    return Response(content=csv_data, headers=headers, media_type="text/csv")


@router.get("/download-consumers-excel")
def download_consumers_excel():
    df = get_all_consumer_accounts()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Consumer_Master_60")
    headers = {"Content-Disposition": 'attachment; filename="SRTPL_Consumer_Master_60.xlsx"'}
    return Response(content=output.getvalue(), headers=headers, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
