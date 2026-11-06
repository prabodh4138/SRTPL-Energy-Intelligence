"""SRTPL Power Intelligence — Custom View Builder & Report Export Center.

Provides dynamic view building, flexible multi-parameter filtering,
multi-item column selector with 'Select All', proper grilled-style data grid,
executive summary metrics, and instant Excel / CSV export.
"""
from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import streamlit as st

try:
    import openpyxl
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

from core.db_sync import (
    _ensure_official_register_columns,
    get_all_consumer_accounts,
    get_all_payment_receipts,
    get_budget_vs_actual,
    get_missing_bills_kpi,
    get_official_bill_register,
    get_receipt_reconciliation,
    get_rebate_performance,
    get_rejected_bills_bucket,
    get_merged_bill_receipt_reconciliation,
)

# ---------------------------------------------------------------------------
# COLUMN METADATA & FIELD DEFINITIONS
# ---------------------------------------------------------------------------

BILL_REGISTER_COLUMN_LABELS: dict[str, str] = {
    # Identifiers
    "bill_number": "Bill Number",
    "consumer_account_no": "Consumer A/c No.",
    "meter_sl_no": "Meter Sl. No.",
    "toll_plaza_id": "Toll Plaza",
    "bill_type": "Feeder Type (HT/LT)",
    "consumer_scope": "Scope (PLAZA/HIGHWAY)",
    "asset_code": "Asset Code",
    "location": "Location / Chainage",
    
    # Timeline
    "bill_month": "Bill Month",
    "financial_year": "Financial Year",
    "bill_period": "Bill Period",
    "bill_days": "Bill Days",
    "rebate_date": "Rebate Date",
    "due_date": "Due Date",
    "latest_payment_date": "Latest Payment Date",
    
    # Technical & Jurisdictions
    "sanctioned_load_kw": "Sanctioned Load (kW)",
    "contract_demand": "Contract Demand",
    "md": "Recorded MD",
    "cuml_md_kw": "CUML MD (kW)",
    "cuml_md_kva": "CUML MD (kVA)",
    "security_deposit": "Security Deposit (₹)",
    "tariff_category": "Tariff Category",
    "division_name": "Division",
    "sub_division": "Sub-Division",
    "section": "Section",
    "usage_type": "Usage Type",
    
    # Consumption & Slabs
    "slab_normal_kwh": "Normal Units (kWh)",
    "slab_peak_kwh": "Peak Units (kWh)",
    "slab_solar_kwh": "Solar Units (kWh)",
    "total_billed_kwh": "Total Energy Units (kWh)",
    
    # Financial Charges
    "energy_charges": "Energy Charges (₹)",
    "demand_charge": "Demand Charge (₹)",
    "tod_incentive": "TOD Incentive (₹)",
    "tod_surcharge": "TOD Surcharge (₹)",
    "electricity_charges": "Electricity Charges (₹)",
    "electricity_duty": "Electricity Duty (₹)",
    "meter_rent": "Meter Rent (₹)",
    "customer_service_charge": "Customer Service Charge (₹)",
    "customer_service": "Customer Service (₹)",
    "Customer Service (₹)": "Customer Service (₹)",
    "Meter Rent (₹)": "Meter Rent (₹)",
    "dps_rs": "DPS / Delay Surcharge (₹)",
    "prompt_rebate": "Prompt Rebate (₹)",
    "current_total": "Current Assessment (₹)",
    "total_amount_payable": "Total Amount Payable (₹)",
    "net_payable_amount_before_rbt_dt_rs": "Net Payable Before Rebate (₹)",
    "net_payable_amount_after_rbt_dt_rs": "Net Payable After Rebate (₹)",
    
    # Reconciliation & Payment
    "amount_paid": "Amount Paid (₹)",
    "outstanding_balance": "Outstanding Balance (₹)",
    "payment_status": "Payment Status",
    
    # Audit & Tracking
    "verification_status": "Verification Status",
    "is_edited": "Edited by Operator",
    "edited_by": "Edited By",
    "edited_at": "Edited At",
    "edit_notes": "Audit Notes",
    "source_filename": "Source File",
    "rebate_status": "Rebate Status",
    "rebate_availed": "Rebate Availed (₹)",
    "rebate_loss": "Rebate Loss (₹)",
    "rebate_remarks": "Rebate Audit Remarks",
    "company_profit_rs": "Company Profit (Rebate Availed) (₹)",
    "company_loss_rs": "Company Loss (Rebate Lost) (₹)",
    "financial_impact": "Financial Impact (Profit/Loss)",
    "collections_date": "Payment Date",
    "receipt_no": "Receipt Number",
    "payment_type": "Payment Type",
    "office_name": "Office Name",
}

COLUMN_PRESETS = {
    "Company Profit & Rebate Audit (14)": [
        "consumer_account_no", "bill_month", "bill_number", "toll_plaza_id",
        "total_amount_payable", "rebate_date", "collections_date",
        "prompt_rebate", "rebate_status", "rebate_availed", "rebate_loss",
        "company_profit_rs", "company_loss_rs", "financial_impact"
    ],
    "Reconciliation Core (18)": [
        "bill_number", "consumer_account_no", "meter_sl_no", "toll_plaza_id",
        "bill_type", "consumer_scope", "bill_month", "sanctioned_load_kw",
        "contract_demand", "total_billed_kwh", "energy_charges",
        "meter_rent", "customer_service_charge",
        "total_amount_payable", "net_payable_amount_before_rbt_dt_rs",
        "net_payable_amount_after_rbt_dt_rs", "amount_paid", "outstanding_balance", "payment_status"
    ],
    "Financial & Charges (19)": [
        "bill_number", "consumer_account_no", "bill_month", "total_billed_kwh",
        "energy_charges", "demand_charge", "tod_incentive", "tod_surcharge",
        "electricity_charges", "electricity_duty", "meter_rent", "customer_service_charge",
        "dps_rs", "prompt_rebate", "current_total", "total_amount_payable",
        "net_payable_amount_before_rbt_dt_rs", "net_payable_amount_after_rbt_dt_rs", "payment_status"
    ],
    "Meters & Demand Specs (14)": [
        "consumer_account_no", "meter_sl_no", "toll_plaza_id", "bill_type",
        "consumer_scope", "division_name", "sub_division", "section",
        "tariff_category", "sanctioned_load_kw", "contract_demand",
        "security_deposit", "md", "rebate_date"
    ],
    "Audit & Operator Edits (9)": [
        "bill_number", "consumer_account_no", "bill_month",
        "verification_status", "is_edited", "edited_by",
        "edited_at", "edit_notes", "source_filename"
    ]
}


# ---------------------------------------------------------------------------
# EXCEL GENERATOR (STYLED WORKBOOK)
# ---------------------------------------------------------------------------

def generate_styled_excel(df: pd.DataFrame, sheet_title: str = "Report") -> bytes:
    """Creates a formatted Excel spreadsheet with SRTPL branded headers and formatted numbers."""
    if not HAS_OPENPYXL:
        # Fallback to standard pandas excel export if openpyxl is absent
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_title[:31])
        return buf.getvalue()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_title[:31]
    ws.views.sheetView[0].showGridLines = True

    # SRTPL Brand Header Styling
    header_fill = PatternFill(start_color="0A192F", end_color="0A192F", fill_type="solid")
    header_font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
    data_font = Font(name="Segoe UI", size=9)
    thin_border = Border(
        left=Side(style="thin", color="E2E8F0"),
        right=Side(style="thin", color="E2E8F0"),
        top=Side(style="thin", color="E2E8F0"),
        bottom=Side(style="thin", color="E2E8F0")
    )

    # Write Header Row
    ws.append(list(df.columns))
    for col_idx in range(1, len(df.columns) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Write Data Rows
    for r_idx, row_values in enumerate(df.itertuples(index=False), start=2):
        ws.append(list(row_values))
        for c_idx in range(1, len(df.columns) + 1):
            cell = ws.cell(row=r_idx, column=c_idx)
            cell.font = data_font
            cell.border = thin_border
            val = cell.value

            col_name = str(df.columns[c_idx - 1]).lower()
            if isinstance(val, (int, float)):
                cell.alignment = Alignment(horizontal="right", vertical="center")
                if "rs" in col_name or "amount" in col_name or "charge" in col_name or "total" in col_name or "paid" in col_name or "balance" in col_name or "duty" in col_name or "deposit" in col_name:
                    cell.number_format = "₹ #,##0.00"
                elif "kwh" in col_name or "units" in col_name:
                    cell.number_format = "#,##0.00"
                elif "kw" in col_name or "kva" in col_name or "md" in col_name:
                    cell.number_format = "#,##0.0000"
                else:
                    cell.number_format = "#,##0"
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

    # Auto-adjust Column Widths
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 40)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# MAIN RENDER FUNCTION
# ---------------------------------------------------------------------------

def render() -> None:
    """Renders the comprehensive Report Center with Custom View Builder."""
    st.markdown('<div class="module-header">📊 REPORTS & CUSTOM VIEW STUDIO</div>', unsafe_allow_html=True)
    st.caption("Design, slice, grill, and export tailored energy accounting views, financial reconciliations, and audit reports.")

    # Top Navigation Subtabs
    tab_view_builder, tab_standard_reports, tab_saved_views = st.tabs([
        "🎯 Custom View Builder",
        "📑 Pre-configured Management Reports",
        "⭐ Saved View Bookmarks",
    ])

    # =========================================================================
    # TAB 1: CUSTOM VIEW BUILDER (USER MOTTO: VIEW IN HIS OWN CHOICE)
    # =========================================================================
    with tab_view_builder:
        _render_custom_view_builder()

    # =========================================================================
    # TAB 2: PRE-CONFIGURED STANDARD REPORTS
    # =========================================================================
    with tab_standard_reports:
        _render_standard_reports()

    # =========================================================================
    # TAB 3: SAVED VIEW BOOKMARKS
    # =========================================================================
    with tab_saved_views:
        _render_saved_views()


# ---------------------------------------------------------------------------
# TAB 1 IMPLEMENTATION: CUSTOM VIEW BUILDER
# ---------------------------------------------------------------------------

def _render_custom_view_builder() -> None:
    """Builds custom views with dynamic filters, column selector with 'Select All', and grilled grid."""
    
    # 1. Dataset Selection
    dataset_options = {
        "OFFICIAL_BILLS": "⚡ EB Bill Register & Reconciliation (Official Energy Invoices)",
        "MERGED_RECONCILIATION": "🔄 Unified Merged Bill & Receipts Reconciliation (With Rebate Availed/Loss)",
        "RECEIPTS": "💰 Payment Receipts & Bank Allocation Register",
        "BUDGET_ACTUAL": "📊 Monthly Budget vs Actual Expenditure Variance",
        "CONSUMER_MASTER": "🏷️ 60 Consumer Account Master Registry",
        "REJECTED_BUCKET": "🗑️ Operator Rejected Bills & Duplicate Scans Bucket",
        "MISSING_BILLS": "⚠️ Missing Bills & Gap Analysis Register",
    }
    
    col_ds, col_opt = st.columns([3, 1])
    with col_ds:
        selected_ds_key = st.selectbox(
            "Select Data Domain to Build View",
            options=list(dataset_options.keys()),
            format_func=lambda k: dataset_options[k],
            key="custom_builder_dataset_selector",
        )
    with col_opt:
        use_friendly_names = st.toggle("Human-friendly Headers", value=True, help="Toggle between friendly labels (e.g. 'Meter Sl. No.') and technical column names ('meter_sl_no')")

    # Load Base Data
    raw_df = _load_dataset_by_key(selected_ds_key)

    if raw_df.empty:
        st.info("ℹ️ No records are currently present in the database or active session for this domain. Upload and post energy bills or check database connection.")
        return

    # Normalize Column Types
    raw_df = _sanitize_dataframe(raw_df)

    # 2. Dynamic Filter Bar
    with st.container(border=True):
        st.markdown("##### 🔍 View Filters")
        
        # Prepare Distinct Filter Values
        all_months = sorted([str(m) for m in raw_df["bill_month"].dropna().unique() if str(m).strip() != ""]) if "bill_month" in raw_df.columns else []
        all_plazas = sorted([str(p) for p in raw_df["toll_plaza_id"].dropna().unique() if str(p).strip() != ""]) if "toll_plaza_id" in raw_df.columns else ["TP01", "TP02", "TP03"]
        all_periods = sorted([str(p) for p in raw_df["financial_year"].dropna().unique() if str(p).strip() != ""]) if "financial_year" in raw_df.columns else []

        f_col1, f_col2, f_col3 = st.columns(3)

        # Bill Month Filter with Select All / Clear
        with f_col1:
            st.markdown("**Bill Month**")
            btn_m_all, btn_m_clr = st.columns(2)
            if btn_m_all.button("Select All", key="btn_sel_all_months", width="stretch"):
                st.session_state["filter_sel_months"] = list(all_months)
                st.rerun()
            if btn_m_clr.button("Clear", key="btn_clr_months", width="stretch"):
                st.session_state["filter_sel_months"] = []
                st.rerun()

            sel_months = st.multiselect(
                "Filter Months",
                options=all_months,
                default=st.session_state.get("filter_sel_months", all_months),
                key="filter_sel_months",
                label_visibility="collapsed",
            )

        # Toll Plaza Filter with Select All / Clear
        with f_col2:
            st.markdown("**Toll Plaza**")
            btn_p_all, btn_p_clr = st.columns(2)
            if btn_p_all.button("Select All", key="btn_sel_all_plazas", width="stretch"):
                st.session_state["filter_sel_plazas"] = list(all_plazas)
                st.rerun()
            if btn_p_clr.button("Clear", key="btn_clr_plazas", width="stretch"):
                st.session_state["filter_sel_plazas"] = []
                st.rerun()

            sel_plazas = st.multiselect(
                "Filter Plazas",
                options=all_plazas,
                default=st.session_state.get("filter_sel_plazas", all_plazas),
                key="filter_sel_plazas",
                label_visibility="collapsed",
            )

        # Period / Financial Year Filter
        with f_col3:
            st.markdown("**Period / Financial Year**")
            btn_fy_all, btn_fy_clr = st.columns(2)
            if btn_fy_all.button("Select All", key="btn_sel_all_fy", width="stretch"):
                st.session_state["filter_sel_periods"] = list(all_periods)
                st.rerun()
            if btn_fy_clr.button("Clear", key="btn_clr_fy", width="stretch"):
                st.session_state["filter_sel_periods"] = []
                st.rerun()

            sel_periods = st.multiselect(
                "Filter Periods",
                options=all_periods,
                default=st.session_state.get("filter_sel_periods", all_periods),
                key="filter_sel_periods",
                label_visibility="collapsed",
            )

        # Secondary Filters Row
        sf_col1, sf_col2, sf_col3, sf_col4 = st.columns(4)
        
        # Bill Type (HT / LT)
        with sf_col1:
            all_types = sorted([str(t) for t in raw_df["bill_type"].dropna().unique() if str(t).strip() != ""]) if "bill_type" in raw_df.columns else []
            sel_types = st.multiselect("Feeder Type", options=all_types, default=all_types, key="filter_sel_types") if all_types else []

        # Consumer Scope (PLAZA / HIGHWAY)
        with sf_col2:
            all_scopes = sorted([str(s) for s in raw_df["consumer_scope"].dropna().unique() if str(s).strip() != ""]) if "consumer_scope" in raw_df.columns else []
            sel_scopes = st.multiselect("Consumer Scope", options=all_scopes, default=all_scopes, key="filter_sel_scopes") if all_scopes else []

        # Payment Status
        with sf_col3:
            all_statuses = sorted([str(st_val) for st_val in raw_df["payment_status"].dropna().unique() if str(st_val).strip() != ""]) if "payment_status" in raw_df.columns else []
            sel_statuses = st.multiselect("Payment Status", options=all_statuses, default=all_statuses, key="filter_sel_statuses") if all_statuses else []

        # Free-text Search
        with sf_col4:
            search_query = st.text_input("Quick Search", placeholder="Bill No, A/c No, Meter No, Section...", key="filter_search_query")

    # Apply Filters
    filtered_df = raw_df.copy()
    if sel_months and "bill_month" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["bill_month"].astype(str).isin(sel_months)]
    if sel_plazas and "toll_plaza_id" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["toll_plaza_id"].astype(str).isin(sel_plazas)]
    if sel_periods and "financial_year" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["financial_year"].astype(str).isin(sel_periods)]
    if sel_types and "bill_type" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["bill_type"].astype(str).isin(sel_types)]
    if sel_scopes and "consumer_scope" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["consumer_scope"].astype(str).isin(sel_scopes)]
    if sel_statuses and "payment_status" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["payment_status"].astype(str).isin(sel_statuses)]
    if search_query.strip():
        q = search_query.strip().lower()
        search_cols = [c for c in ["bill_number", "consumer_account_no", "meter_sl_no", "section", "division_name", "sub_division", "source_filename"] if c in filtered_df.columns]
        if search_cols:
            match_mask = pd.Series(False, index=filtered_df.index)
            for c in search_cols:
                match_mask = match_mask | filtered_df[c].astype(str).str.lower().str.contains(q, na=False)
            filtered_df = filtered_df[match_mask]

    # 3. Column Selector Toolbar (With Select All & Presets)
    all_available_columns = list(filtered_df.columns)

    with st.container(border=True):
        st.markdown("##### 📋 Columns Visibility (Grilled Style Selector)")
        
        # Preset Action Buttons
        p_c1, p_c2, p_c3, p_c4, p_c5, p_c6 = st.columns(6)
        
        if p_c1.button("Select All Columns", key="btn_sel_all_cols", width="stretch"):
            st.session_state["chosen_view_columns"] = list(all_available_columns)
            st.rerun()

        if p_c2.button("Deselect All", key="btn_clr_cols", width="stretch"):
            st.session_state["chosen_view_columns"] = []
            st.rerun()

        if p_c3.button("Reconciliation Core", key="btn_preset_core", width="stretch"):
            valid = [c for c in COLUMN_PRESETS["Reconciliation Core (15)"] if c in all_available_columns]
            st.session_state["chosen_view_columns"] = valid
            st.rerun()

        if p_c4.button("Financial & Charges", key="btn_preset_fin", width="stretch"):
            valid = [c for c in COLUMN_PRESETS["Financial & Charges (17)"] if c in all_available_columns]
            st.session_state["chosen_view_columns"] = valid
            st.rerun()

        if p_c5.button("Meters & Demands", key="btn_preset_meters", width="stretch"):
            valid = [c for c in COLUMN_PRESETS["Meters & Demand Specs (14)"] if c in all_available_columns]
            st.session_state["chosen_view_columns"] = valid
            st.rerun()

        if p_c6.button("Audit Trail", key="btn_preset_audit", width="stretch"):
            valid = [c for c in COLUMN_PRESETS["Audit & Operator Edits (9)"] if c in all_available_columns]
            st.session_state["chosen_view_columns"] = valid
            st.rerun()

        # Multi-select column chooser
        default_cols = st.session_state.get("chosen_view_columns")
        if not default_cols:
            if selected_ds_key == "OFFICIAL_BILLS":
                default_cols = [c for c in COLUMN_PRESETS["Reconciliation Core (15)"] if c in all_available_columns]
            else:
                default_cols = all_available_columns[:15]
            st.session_state["chosen_view_columns"] = default_cols

        chosen_columns = st.multiselect(
            "Selected Columns for Active View",
            options=all_available_columns,
            default=[c for c in default_cols if c in all_available_columns],
            format_func=lambda c: f"{BILL_REGISTER_COLUMN_LABELS.get(c, c)} ({c})" if use_friendly_names else c,
            key="chosen_view_columns_widget",
        )
        st.session_state["chosen_view_columns"] = chosen_columns

    if not chosen_columns:
        st.warning("⚠️ No columns are selected. Click 'Select All Columns' or select columns from the list above.")
        return

    # Slice View DataFrame
    view_df = filtered_df[chosen_columns].copy()

    # 4. Summary Executive KPI Cards
    kpi_c1, kpi_c2, kpi_c3, kpi_c4, kpi_c5, kpi_c6 = st.columns(6)
    kpi_c1.metric("Selected Records", f"{len(view_df):,}")
    
    total_kwh = view_df["total_billed_kwh"].sum() if "total_billed_kwh" in view_df.columns else 0.0
    kpi_c2.metric("Total Billed Energy", f"{total_kwh:,.1f} kWh")

    tot_payable = view_df["total_amount_payable"].sum() if "total_amount_payable" in view_df.columns else (view_df["amount"].sum() if "amount" in view_df.columns else 0.0)
    kpi_c3.metric("Total Billed Amount", f"₹ {tot_payable:,.2f}")

    tot_paid = view_df["amount_paid"].sum() if "amount_paid" in view_df.columns else 0.0
    kpi_c4.metric("Total Paid Amount", f"₹ {tot_paid:,.2f}")

    tot_bal = view_df["outstanding_balance"].sum() if "outstanding_balance" in view_df.columns else max(0.0, tot_payable - tot_paid)
    kpi_c5.metric("Outstanding Balance", f"₹ {tot_bal:,.2f}")

    realization = (tot_paid / tot_payable * 100.0) if tot_payable > 0 else 0.0
    kpi_c6.metric("Realization Rate", f"{realization:.1f}%")

    # 5. Grilled-Style Data Table
    # If friendly names requested, construct presentation dataframe
    display_df = view_df.copy()
    if use_friendly_names:
        rename_map = {c: BILL_REGISTER_COLUMN_LABELS.get(c, c) for c in display_df.columns}
        display_df = display_df.rename(columns=rename_map)

    # Column configuration for professional table rendering
    col_configs = _build_streamlit_column_configs(display_df)

    st.markdown("---")
    st.markdown(f"**Viewing {len(display_df):,} rows × {len(chosen_columns)} columns**")
    
    st.dataframe(
        display_df,
        column_config=col_configs,
        width="stretch",
        height=min(600, max(250, len(display_df) * 35 + 50)),
    )

    # 6. Export Toolbar (Excel & CSV)
    st.markdown("##### 📥 Export Custom View")
    exp_c1, exp_c2, exp_c3 = st.columns([2, 2, 3])

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_base = f"SRTPL_{selected_ds_key}_Report_{ts}"

    # Excel Export
    excel_bytes = generate_styled_excel(display_df, sheet_title=selected_ds_key)
    exp_c1.download_button(
        "📥 Download as Excel (.xlsx)",
        data=excel_bytes,
        file_name=f"{file_base}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
        type="primary",
    )

    # CSV Export
    csv_bytes = display_df.to_csv(index=False).encode("utf-8-sig")
    exp_c2.download_button(
        "📄 Download as CSV (.csv)",
        data=csv_bytes,
        file_name=f"{file_base}.csv",
        mime="text/csv",
        width="stretch",
    )

    # 7. Save Custom View Bookmark Expander
    with st.expander("💾 Bookmark This Custom View Configuration", expanded=False):
        save_col1, save_col2 = st.columns([3, 1])
        new_view_name = save_col1.text_input("Custom View Name", placeholder="e.g., HT Plaza Demands & Rebates Q1")
        if save_col2.button("Save Bookmark", width="stretch") and new_view_name.strip():
            if "user_saved_custom_views" not in st.session_state:
                st.session_state["user_saved_custom_views"] = {}
            st.session_state["user_saved_custom_views"][new_view_name.strip()] = {
                "dataset": selected_ds_key,
                "columns": list(chosen_columns),
                "months": list(sel_months),
                "plazas": list(sel_plazas),
                "periods": list(sel_periods),
                "saved_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            }
            st.success(f"View '{new_view_name.strip()}' saved to bookmarks!")


# ---------------------------------------------------------------------------
# TAB 2 IMPLEMENTATION: PRE-CONFIGURED STANDARD REPORTS
# ---------------------------------------------------------------------------

def _render_standard_reports() -> None:
    """Pre-built standard reports (Executive MIS, Daily Energy, Budget Variance, Rebates)."""
    st.markdown("##### 📑 Standard Management & Executive Energy Reports")
    
    std_reports = {
        "EXECUTIVE_MIS": "Executive Monthly Energy MIS & Financial Register",
        "REBATE_PERFORMANCE": "Prompt Payment Rebate Performance & Loss Audit",
        "BUDGET_VARIANCE": "Monthly Plaza Energy Budget vs Actual Variance",
        "RECEIPT_RECONCILIATION": "Electricity Board to Bank Receipt Reconciliation",
    }

    rep_choice = st.selectbox(
        "Select Standard Report",
        options=list(std_reports.keys()),
        format_func=lambda k: std_reports[k],
        key="std_report_selector"
    )

    if rep_choice == "EXECUTIVE_MIS":
        df = get_official_bill_register()
        sheet_title = "Executive_MIS"
    elif rep_choice == "REBATE_PERFORMANCE":
        df = get_rebate_performance()
        sheet_title = "Rebate_Performance"
    elif rep_choice == "BUDGET_VARIANCE":
        df = get_budget_vs_actual()
        sheet_title = "Budget_vs_Actual"
    else:
        df = get_receipt_reconciliation()
        sheet_title = "Receipt_Reconciliation"

    if df.empty:
        st.info("No records are currently present for this report.")
        return

    st.dataframe(df, width="stretch", height=450)

    e_c1, e_c2 = st.columns(2)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    e_c1.download_button(
        f"📥 Download {rep_choice} (.xlsx)",
        data=generate_styled_excel(df, sheet_title=sheet_title),
        file_name=f"SRTPL_{rep_choice}_{ts}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
        type="primary"
    )
    e_c2.download_button(
        f"📄 Download {rep_choice} (.csv)",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"SRTPL_{rep_choice}_{ts}.csv",
        mime="text/csv",
        width="stretch"
    )


# ---------------------------------------------------------------------------
# TAB 3 IMPLEMENTATION: SAVED VIEW BOOKMARKS
# ---------------------------------------------------------------------------

def _render_saved_views() -> None:
    """Lists and allows re-applying saved custom views."""
    st.markdown("##### ⭐ Your Saved Custom Views")
    
    saved = st.session_state.get("user_saved_custom_views", {})
    if not saved:
        st.info("No custom views have been bookmarked yet. Configure your filters and columns in the 'Custom View Builder' tab, then save your view bookmark.")
        return

    for view_name, cfg in list(saved.items()):
        with st.container(border=True):
            v_c1, v_c2, v_c3 = st.columns([3, 1, 1])
            v_c1.markdown(f"**{view_name}**")
            v_c1.caption(f"Domain: {cfg.get('dataset')} • Columns: {len(cfg.get('columns', []))} • Saved: {cfg.get('saved_at')}")

            if v_c2.button("Apply View", key=f"btn_apply_{view_name}", width="stretch"):
                st.session_state["custom_builder_dataset_selector"] = cfg.get("dataset", "OFFICIAL_BILLS")
                st.session_state["chosen_view_columns"] = cfg.get("columns", [])
                st.session_state["filter_sel_months"] = cfg.get("months", [])
                st.session_state["filter_sel_plazas"] = cfg.get("plazas", [])
                st.session_state["filter_sel_periods"] = cfg.get("periods", [])
                st.success(f"View '{view_name}' applied! Switch to the 'Custom View Builder' tab to see it.")

            if v_c3.button("Delete", key=f"btn_del_{view_name}", width="stretch"):
                saved.pop(view_name, None)
                st.session_state["user_saved_custom_views"] = saved
                st.rerun()


# ---------------------------------------------------------------------------
# DATA LOADERS & HELPERS
# ---------------------------------------------------------------------------

def _load_dataset_by_key(dataset_key: str) -> pd.DataFrame:
    """Fetches the corresponding dataset from database or unified in-memory storage."""
    if dataset_key == "OFFICIAL_BILLS":
        df = get_official_bill_register()
        # Merge session extracted bills if present
        if "extracted_bills_full_df" in st.session_state and isinstance(st.session_state["extracted_bills_full_df"], pd.DataFrame):
            sess_df = st.session_state["extracted_bills_full_df"]
            if not sess_df.empty:
                sess_df = _ensure_official_register_columns(sess_df)
                if df.empty:
                    df = sess_df
                else:
                    existing_bns = set(df["bill_number"].dropna().astype(str).str.strip())
                    new_rows = sess_df[~sess_df["bill_number"].dropna().astype(str).str.strip().isin(existing_bns)]
                    if not new_rows.empty:
                        df = pd.concat([df, new_rows], ignore_index=True)
        return _ensure_official_register_columns(df) if not df.empty else df

    elif dataset_key == "MERGED_RECONCILIATION":
        return get_merged_bill_receipt_reconciliation()

    elif dataset_key == "RECEIPTS":
        r_df = get_receipt_reconciliation()
        if r_df.empty:
            r_df = get_all_payment_receipts()
        return r_df

    elif dataset_key == "BUDGET_ACTUAL":
        return get_budget_vs_actual()

    elif dataset_key == "CONSUMER_MASTER":
        return get_all_consumer_accounts()

    elif dataset_key == "REJECTED_BUCKET":
        return get_rejected_bills_bucket()

    elif dataset_key == "MISSING_BILLS":
        b_df = get_official_bill_register()
        return get_missing_bills_kpi(b_df)

    return pd.DataFrame()


def _sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Ensures numeric columns are clean floats/ints and strings are cleanly stripped."""
    clean = df.copy()
    numeric_cols = [
        "sanctioned_load_kw", "security_deposit", "md", "md_kw", "md_kva",
        "cuml_md_kw", "cuml_md_kva", "dps_rs", "slab_normal_kwh", "slab_peak_kwh",
        "slab_solar_kwh", "total_billed_kwh", "energy_charges", "demand_charge",
        "tod_incentive", "tod_surcharge", "electricity_charges", "electricity_duty",
        "current_total", "prompt_rebate", "total_amount_payable",
        "net_payable_amount_before_rbt_dt_rs", "net_payable_amount_after_rbt_dt_rs",
        "amount_paid", "outstanding_balance", "amount", "units", "budget_amount",
        "approved_budget", "actual_billed_amount", "actual_paid_amount",
        "budget_variance_amount", "budget_variance_percentage"
    ]
    for c in numeric_cols:
        if c in clean.columns:
            clean[c] = pd.to_numeric(clean[c], errors="coerce").fillna(0.0)

    for c in clean.columns:
        if clean[c].dtype == object:
            clean[c] = clean[c].fillna("").astype(str).str.strip()

    return clean


def _build_streamlit_column_configs(df: pd.DataFrame) -> dict[str, Any]:
    """Generates st.column_config definitions based on column name semantics."""
    configs: dict[str, Any] = {}
    for col in df.columns:
        c_low = str(col).lower()
        if any(term in c_low for term in ["(rs.)", "(₹)", "charges", "payable", "balance", "paid", "duty", "rebate", "dps", "total", "budget", "variance_amount", "deposit"]):
            configs[col] = st.column_config.NumberColumn(format="₹ %.2f")
        elif "kwh" in c_low or "units" in c_low:
            configs[col] = st.column_config.NumberColumn(format="%.2f kWh")
        elif "load" in c_low or "kw" in c_low:
            configs[col] = st.column_config.NumberColumn(format="%.2f kW")
        elif "kva" in c_low or "md" in c_low:
            configs[col] = st.column_config.NumberColumn(format="%.4f")
        elif "percentage" in c_low or "rate" in c_low or "%" in c_low:
            configs[col] = st.column_config.NumberColumn(format="%.2f %%")
        elif "status" in c_low:
            configs[col] = st.column_config.TextColumn(help="Lifecycle & Payment Status")
    return configs


if __name__ == "__main__":
    render()
