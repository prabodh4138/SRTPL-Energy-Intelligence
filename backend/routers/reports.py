import io
from fastapi import APIRouter, Response, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import pandas as pd
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import sys
import os
from typing import Any

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "active_app"))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from core.db_sync import (
    get_official_bill_register,
    get_all_consumer_accounts,
    get_all_payment_receipts,
    get_receipt_reconciliation,
    get_budget_vs_actual,
    get_unified_billing_kpi_dataset,
    get_merged_bill_receipt_reconciliation,
    _ensure_official_register_columns,
)

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/summary")
def get_reports_summary():
    bills_df = get_official_bill_register()
    consumers_df = get_all_consumer_accounts()
    receipts_df = get_receipt_reconciliation()
    budget_df = get_budget_vs_actual()

    merged_df = get_merged_bill_receipt_reconciliation()
    reports = [
        {"id": "REP-01", "name": "Authoritative Official Bill Register", "format": "Excel / CSV", "rows": len(bills_df), "category": "Financial Controls"},
        {"id": "REP-02", "name": "60 Consumer Master Roster (3 HT / 57 LT)", "format": "Excel / CSV", "rows": len(consumers_df), "category": "Master Data"},
        {"id": "REP-03", "name": "Payment Receipts Reconciliation & Allocations", "format": "Excel / CSV", "rows": len(receipts_df), "category": "Audit & Clearance"},
        {"id": "REP-04", "name": "Corridor Monthly Budget vs Actual Expenditure", "format": "Excel / CSV", "rows": len(budget_df), "category": "Executive"},
        {"id": "REP-05", "name": "Unified Bill & Receipts Reconciliation Register", "format": "Excel / CSV", "rows": len(merged_df), "category": "Financial Controls"},
    ]
    return {"reports": reports}


@router.get("/download-bills-excel")
def download_bills_excel():
    df = _ensure_official_register_columns(get_official_bill_register())
    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="Cannot download or export: No bill records are present in the Supabase database. Please upload and verify bills first."
        )

    # Guarantee all 13 fields are available
    if "net_payable_amount_before_rbt_dt_rs" not in df.columns:
        df["net_payable_amount_before_rbt_dt_rs"] = df.get("total_amount_payable", 0.0)
    if "net_payable_amount_after_rbt_dt_rs" not in df.columns:
        df["net_payable_amount_after_rbt_dt_rs"] = df.get("net_after_rebate", 0.0)

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
    df = _ensure_official_register_columns(get_official_bill_register())
    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="Cannot download or export: No bill records are present in the Supabase database. Please upload and verify bills first."
        )

    if "net_payable_amount_before_rbt_dt_rs" not in df.columns:
        df["net_payable_amount_before_rbt_dt_rs"] = df.get("total_amount_payable", 0.0)
    if "net_payable_amount_after_rbt_dt_rs" not in df.columns:
        df["net_payable_amount_after_rbt_dt_rs"] = df.get("net_after_rebate", 0.0)

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



@router.get("/merged-reconciliation")
def get_merged_reconciliation_endpoint():
    df = get_merged_bill_receipt_reconciliation()
    return {"records": df.to_dict(orient="records")}


@router.get("/download-merged-reconciliation-excel")
def download_merged_reconciliation_excel():
    df = get_merged_bill_receipt_reconciliation()
    if df.empty:
        raise HTTPException(status_code=400, detail="Cannot export: No bill or receipt records are available.")

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Unified_Reconciliation")
        ws = writer.sheets["Unified_Reconciliation"]
        hdr_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
        hdr_font = Font(name="Arial", size=10, bold=True, color="F8FAFC")
        for col_idx in range(1, len(df.columns) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = hdr_fill
            cell.font = hdr_font
            col_letter = get_column_letter(col_idx)
            max_len = max(len(str(val or "")) for val in df.iloc[:, col_idx - 1])
            ws.column_dimensions[col_letter].width = max(max_len + 3, 14)

    headers = {"Content-Disposition": 'attachment; filename="SRTPL_Unified_Bill_Receipts_Reconciliation.xlsx"'}
    return Response(content=output.getvalue(), headers=headers, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/download-merged-reconciliation-csv")
def download_merged_reconciliation_csv():
    df = get_merged_bill_receipt_reconciliation()
    if df.empty:
        raise HTTPException(status_code=400, detail="Cannot export: No bill or receipt records are available.")
    csv_data = df.to_csv(index=False).encode("utf-8")
    headers = {"Content-Disposition": 'attachment; filename="SRTPL_Unified_Bill_Receipts_Reconciliation.csv"'}
    return Response(content=csv_data, headers=headers, media_type="text/csv")


@router.get("/download-receipts-excel")
def download_receipts_excel():
    df = get_all_payment_receipts()
    if df.empty:
        raise HTTPException(status_code=400, detail="Cannot export: No payment receipts are recorded in database.")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Payment_Receipts")
    headers = {"Content-Disposition": 'attachment; filename="SRTPL_Payment_Receipts_Register.xlsx"'}
    return Response(content=output.getvalue(), headers=headers, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/download-receipts-csv")
def download_receipts_csv():
    df = get_all_payment_receipts()
    if df.empty:
        raise HTTPException(status_code=400, detail="Cannot export: No payment receipts are recorded in database.")
    csv_data = df.to_csv(index=False).encode("utf-8")
    headers = {"Content-Disposition": 'attachment; filename="SRTPL_Payment_Receipts_Register.csv"'}
    return Response(content=csv_data, headers=headers, media_type="text/csv")


class CustomExportPayload(BaseModel):
    format: str = "xlsx"
    title: str = "Custom_Report"
    columns: list[str]
    labels: dict[str, str] = {}
    rows: list[dict[str, Any]]


@router.post("/custom-export")
def export_custom_report(payload: CustomExportPayload):
    """Generates a professional styled Excel (.xlsx) or UTF-8 CSV matching the user's custom created view."""
    if not payload.rows:
        raise HTTPException(status_code=400, detail="Cannot export empty dataset.")

    chosen_cols = payload.columns if payload.columns else list(payload.rows[0].keys())
    labels = payload.labels or {}

    # Build clean DataFrame with requested columns in order
    data_list = []
    for r in payload.rows:
        row_dict = {}
        for c in chosen_cols:
            display_name = labels.get(c, c)
            row_dict[display_name] = r.get(c, "")
        data_list.append(row_dict)

    df = pd.DataFrame(data_list)
    clean_title = (payload.title or "Custom_Report").replace(" ", "_")[:30]

    if payload.format.lower() == "csv":
        csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
        headers = {"Content-Disposition": f'attachment; filename="SRTPL_{clean_title}.csv"'}
        return Response(content=csv_bytes, headers=headers, media_type="text/csv")

    # Build styled Excel with OpenPyXL
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = clean_title
    ws.views.sheetView[0].showGridLines = True

    header_fill = PatternFill(start_color="0A192F", end_color="0A192F", fill_type="solid")
    header_font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
    data_font = Font(name="Segoe UI", size=9)
    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1"),
    )

    ws.append(list(df.columns))
    for col_idx in range(1, len(df.columns) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for r_idx, row_values in enumerate(df.itertuples(index=False), start=2):
        ws.append(list(row_values))
        for c_idx in range(1, len(df.columns) + 1):
            cell = ws.cell(row=r_idx, column=c_idx)
            cell.font = data_font
            cell.border = thin_border
            val = cell.value

            col_name = str(df.columns[c_idx - 1]).lower()
            # Explicit text formatting for bill numbers, meter serials, consumer accounts, and codes (NEVER comma separated)
            if any(k in col_name for k in ["number", "bill_number", "account", "meter", "code", "sl_no", "id", "batch", "ref", "receipt", "plaza", "scope", "type", "basis", "status", "category", "section", "division", "date", "month", "period", "file", "location"]):
                cell.number_format = "@"
                cell.value = str(val) if val is not None and val != "" else "—"
                cell.alignment = Alignment(horizontal="left")
            elif any(k in col_name for k in ["amount", "charges", "duty", "payable", "paid", "balance", "total", "deposit", "dps", "₹", "rs."]):
                if isinstance(val, (int, float)):
                    cell.number_format = "#,##0.00"
                    cell.alignment = Alignment(horizontal="right")
            elif any(k in col_name for k in ["units", "kwh", "kvah", "load", "demand", "md"]):
                if isinstance(val, (int, float)):
                    cell.number_format = "#,##0.00"
                    cell.alignment = Alignment(horizontal="right")

    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = max(12, min(max_len + 4, 45))

    out = io.BytesIO()
    wb.save(out)
    headers = {"Content-Disposition": f'attachment; filename="SRTPL_{clean_title}.xlsx"'}
    return Response(
        content=out.getvalue(),
        headers=headers,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
