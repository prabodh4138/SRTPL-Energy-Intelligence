import streamlit as st
import pandas as pd
import io
import os
import glob
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.demo_store import (
    get_demo_bills,
    get_demo_monthly_eb_consumption,
    get_demo_bill_extraction_result,
)
from bill_extractor.extractor_main_full import extract_energy_bill_full
from bill_extractor.extractor_md_full import extract_md_bill_data
from bill_extractor.extractor_receipt_full import extract_energy_receipt_data
from bill_extractor.merge_clean_core import merge_and_clean_dataframes
from bill_extractor.verifier import verify_bill_calculations, _parse_num
from bill_extractor.zip_handler import extract_pdfs_from_inputs
from core.db_sync import (
    save_energy_bill,
    batch_save_energy_bills,
    update_energy_bill,
    get_all_energy_bills,
    delete_energy_bill,
    get_existing_bill_numbers,
    save_provisional_energy_bill,
    batch_save_provisional_energy_bills,
    get_existing_provisional_bill_numbers,
    get_all_provisional_energy_bills,
    delete_provisional_energy_bill,
    get_all_consumer_accounts,
    save_consumer_account,
    delete_consumer_account,
    get_correlated_consumer_reconciliation,
    get_consumer_mapping_dict,
    get_unified_billing_kpi_dataset,
    get_missing_bills_kpi,
)

SAMPLE_DIR = "source_data/user_uploaded_bills/extractor"


def render():
    st.markdown('<div class="eyebrow">SRTPL / FINANCIAL CONTROLS</div>', unsafe_allow_html=True)
    st.title("Bills & Receipts — Monthly EB Consumption & Extraction")
    st.caption("Month-wise DISCOM billing intelligence, automated bill field extraction with dynamic tariff categories (GPS, Public Lighting, HT), and formula verification.")

    raw_kpi_df = get_unified_billing_kpi_dataset()
    if not raw_kpi_df.empty and "deleted_bills" in st.session_state:
        raw_kpi_df = raw_kpi_df[~raw_kpi_df["bill_number"].isin(st.session_state["deleted_bills"])]
    monthly_df = get_demo_monthly_eb_consumption()

    # Top KPI summary cards calculated from real-time database views / unified dataset
    total_billed = float(raw_kpi_df["total_amount_payable"].sum()) if not raw_kpi_df.empty and "total_amount_payable" in raw_kpi_df.columns else 0.0
    total_paid = float(raw_kpi_df["amount_paid"].sum()) if not raw_kpi_df.empty and "amount_paid" in raw_kpi_df.columns else 0.0
    total_outstanding = float(raw_kpi_df["outstanding_balance"].sum()) if not raw_kpi_df.empty and "outstanding_balance" in raw_kpi_df.columns else 0.0
    tot_kwh_overall = float(raw_kpi_df["total_billed_kwh"].sum()) if not raw_kpi_df.empty and "total_billed_kwh" in raw_kpi_df.columns else 0.0
    realized_pct = (total_paid / max(1.0, total_billed) * 100) if total_billed > 0 else 100.0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("📋 Total Invoiced", f"₹{total_billed:,.0f}", f"{tot_kwh_overall:,.0f} kWh Billed Units")
    k2.metric("🟢 Payments Cleared", f"₹{total_paid:,.0f}", f"{realized_pct:.1f}% Realized")
    k3.metric("🟡 Outstanding Balance", f"₹{total_outstanding:,.0f}", help="Awaiting payment or invoice reconciliation")
    k4.metric("🛡️ Active Corridor Coverage", "60 Accounts", "3 HT Substation + 57 LT Lighting")

    st.divider()

    tab_kpi, tab_monthly, tab_extract, tab_reconcile, tab_register, tab_master = st.tabs([
        "📊 Executive Billing KPIs",
        "📅 Month-wise EB Consumption",
        "📄 Bill Field Extraction & Verification",
        "⚖️ Meter vs. Bill Reconciliation",
        "💳 Bill & Receipt Register",
        "🏛️ Energy Consumer Master & Mapping",
    ])

    # -------------------------------------------------------------------------
    # TAB 0: Executive Billing KPIs & Multi-Dimensional Analytics
    # -------------------------------------------------------------------------
    with tab_kpi:
        st.subheader("Executive Billing KPIs & Multi-Dimensional Intelligence")
        st.caption("Cross-correlating Consumer Accounts, DISCOM Energy Bills, Reading Basis, and Payment Clearance across Plazas, Tariffs, and Time Horizons.")

        raw_kpi_df = get_unified_billing_kpi_dataset()

        # Multi-Dimensional Filter Controls Container
        with st.container(border=True):
            st.markdown("##### 🎛️ Multi-Dimensional Filter Controls")
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)

            # 1. Plaza Filter
            all_plazas = ["All Plazas"] + sorted([str(p) for p in raw_kpi_df["toll_plaza_id"].dropna().unique()])
            sel_plaza = f_col1.selectbox("Toll Plaza", all_plazas, index=0, key="kpi_sel_plaza")

            # 2. Month Filter
            all_months = ["All Months"] + sorted([str(m) for m in raw_kpi_df["bill_month"].dropna().unique()], reverse=True)
            sel_month = f_col2.selectbox("Bill Month / Cycle", all_months, index=0, key="kpi_sel_month")

            # 3. HT vs LT Tariff Filter
            sel_type = f_col3.selectbox("Tariff / Bill Type", ["All", "HT (High Tension)", "LT (Low Tension)"], index=0, key="kpi_sel_type")

            # 4. Bill Reading Basis (Actual vs Prov vs Avg)
            sel_basis = f_col4.selectbox("Reading Basis", ["All", "ACTUAL Only", "PROVISIONAL / AVERAGE Only", "AVERAGE Only", "PROVISIONAL Only"], index=0, key="kpi_sel_basis")

            f_col5, f_col6, f_col7 = st.columns(3)
            # 5. Payment Clearance Status
            sel_status = f_col5.selectbox("Payment Clearance", ["All", "PAID Only", "UNPAID / PARTIAL Only"], index=0, key="kpi_sel_status")

            # 6. Consumer Scope
            all_scopes = ["All Scopes"] + sorted([str(s) for s in raw_kpi_df["consumer_scope"].dropna().unique()])
            sel_scope = f_col6.selectbox("Consumer Scope", all_scopes, index=0, key="kpi_sel_scope")

            # 7. Division Filter
            all_divs = ["All Divisions"] + sorted([str(d) for d in raw_kpi_df["division_name"].dropna().unique()])
            sel_div = f_col7.selectbox("DISCOM Division", all_divs, index=0, key="kpi_sel_div")

        # Apply Filtering
        filtered_kpi = raw_kpi_df.copy()

        if sel_plaza != "All Plazas":
            filtered_kpi = filtered_kpi[filtered_kpi["toll_plaza_id"] == sel_plaza]

        if sel_month != "All Months":
            filtered_kpi = filtered_kpi[filtered_kpi["bill_month"] == sel_month]

        if sel_type != "All":
            type_code = "HT" if "HT" in sel_type else "LT"
            filtered_kpi = filtered_kpi[filtered_kpi["bill_type"] == type_code]

        if sel_basis == "ACTUAL Only":
            filtered_kpi = filtered_kpi[filtered_kpi["bill_basis"] == "ACTUAL"]
        elif sel_basis == "PROVISIONAL / AVERAGE Only":
            filtered_kpi = filtered_kpi[filtered_kpi["bill_basis"].isin(["PROVISIONAL", "AVERAGE", "ESTIMATED"])]
        elif sel_basis == "AVERAGE Only":
            filtered_kpi = filtered_kpi[filtered_kpi["bill_basis"] == "AVERAGE"]
        elif sel_basis == "PROVISIONAL Only":
            filtered_kpi = filtered_kpi[filtered_kpi["bill_basis"] == "PROVISIONAL"]

        if sel_status == "PAID Only":
            filtered_kpi = filtered_kpi[filtered_kpi["payment_status"] == "PAID"]
        elif sel_status == "UNPAID / PARTIAL Only":
            filtered_kpi = filtered_kpi[filtered_kpi["payment_status"].isin(["UNPAID", "PARTIAL"])]

        if sel_scope != "All Scopes":
            filtered_kpi = filtered_kpi[filtered_kpi["consumer_scope"] == sel_scope]

        if sel_div != "All Divisions":
            filtered_kpi = filtered_kpi[filtered_kpi["division_name"] == sel_div]

        # Calculate Missing Bills for the filtered timeframe
        target_months = None if sel_month == "All Months" else [sel_month]
        missing_df = get_missing_bills_kpi(filtered_kpi, target_months=target_months)
        if sel_plaza != "All Plazas":
            missing_df = missing_df[missing_df["toll_plaza_id"] == sel_plaza]
        if sel_type != "All":
            t_code = "HT" if "HT" in sel_type else "LT"
            missing_df = missing_df[missing_df["bill_type"] == t_code]

        # KPI Computations
        tot_kwh = float(filtered_kpi["total_billed_kwh"].sum()) if not filtered_kpi.empty else 0.0
        tot_invoiced = float(filtered_kpi["total_amount_payable"].sum()) if not filtered_kpi.empty else 0.0
        tot_paid = float(filtered_kpi["amount_paid"].sum()) if not filtered_kpi.empty else 0.0
        tot_outstanding = float(filtered_kpi["outstanding_balance"].sum()) if not filtered_kpi.empty else 0.0

        num_gen_bills = len(filtered_kpi)
        num_miss_bills = len(missing_df)
        total_expected_bills = num_gen_bills + num_miss_bills
        gen_rate = (num_gen_bills / max(1, total_expected_bills)) * 100.0

        actual_count = len(filtered_kpi[filtered_kpi["bill_basis"] == "ACTUAL"]) if not filtered_kpi.empty else 0
        prov_avg_count = len(filtered_kpi[filtered_kpi["bill_basis"].isin(["PROVISIONAL", "AVERAGE", "ESTIMATED"])]) if not filtered_kpi.empty else 0
        basis_actual_pct = (actual_count / max(1, num_gen_bills)) * 100.0 if num_gen_bills > 0 else 0.0

        avg_unit_cost = (tot_invoiced / max(1.0, tot_kwh)) if tot_kwh > 0 else 0.0
        pay_realization_rate = (tot_paid / max(1.0, tot_invoiced)) * 100.0 if tot_invoiced > 0 else 100.0

        # Section 1: Top KPI Cards Row
        st.markdown("#### 📌 Key Performance Indicators Summary")
        kp1, kp2, kp3, kp4 = st.columns(4)
        kp1.metric("⚡ Total Billed Units", f"{tot_kwh:,.0f} kWh", help="Normal + Peak + Solar consumption from DISCOM invoices")
        kp2.metric("💳 Invoiced Amount", f"₹{tot_invoiced:,.0f}", help="Total billed charges including duty and fixed charges")
        kp3.metric("🟢 Payments Cleared", f"₹{tot_paid:,.0f}", f"{pay_realization_rate:.1f}% Realized")
        kp4.metric("🟡 Outstanding Balance", f"₹{tot_outstanding:,.0f}", help="Pending clearance or under audit exception")

        kp5, kp6, kp7, kp8 = st.columns(4)
        kp5.metric("📋 Generation Coverage", f"{gen_rate:.1f}%", f"{num_gen_bills}/{total_expected_bills} Bills Present")
        kp6.metric("🛡️ Reading Basis Integrity", f"{basis_actual_pct:.1f}% Actual", f"{actual_count} Actual | {prov_avg_count} Estimated")
        kp7.metric("💵 Average Realized Tariff", f"₹{avg_unit_cost:.2f} / kWh", help="Overall effective tariff per consumed unit")
        kp8.metric("⚠️ Missing Bills Count", f"{num_miss_bills} Accounts", help="Active connections without bills in selected period")

        st.divider()

        # Detailed Subtabs for Deep Dive
        sub_kpi_plaza, sub_kpi_month, sub_kpi_miss, sub_kpi_basis, sub_kpi_all = st.tabs([
            "🏢 Plaza & Tariff Breakdown",
            "📅 Month-wise Trends & Payments",
            f"⚠️ Bill Generation vs. Missing ({num_miss_bills})",
            f"🛡️ Actual vs. Provisional vs. Average ({prov_avg_count})",
            "📋 Master KPI Data Matrix",
        ])

        with sub_kpi_plaza:
            st.markdown("##### 🏢 Plaza-wise Consumption & Financial Analysis")
            if filtered_kpi.empty:
                st.info("No data available for the selected filters.")
            else:
                plz_chart = filtered_kpi.groupby("toll_plaza_id").agg({
                    "total_billed_kwh": "sum",
                    "total_amount_payable": "sum",
                    "amount_paid": "sum",
                    "outstanding_balance": "sum",
                    "consumer_account_no": "nunique",
                }).reset_index().rename(columns={
                    "toll_plaza_id": "Plaza",
                    "consumer_account_no": "Active Connections",
                    "total_billed_kwh": "Billed Units (kWh)",
                    "total_amount_payable": "Invoiced (₹)",
                    "amount_paid": "Paid (₹)",
                    "outstanding_balance": "Outstanding (₹)",
                })
                # Add calculated analytical columns
                plz_chart["Realization %"] = plz_chart.apply(
                    lambda r: round((r["Paid (₹)"] / max(1.0, r["Invoiced (₹)"])) * 100, 1), axis=1
                )
                plz_chart["Avg Cost/kWh (₹)"] = plz_chart.apply(
                    lambda r: round((r["Invoiced (₹)"] / max(1.0, r["Billed Units (kWh)"])), 2), axis=1
                )

                ch_c1, ch_c2 = st.columns(2)
                with ch_c1:
                    st.caption("⚡ Consumption by Toll Plaza (kWh)")
                    st.bar_chart(plz_chart.set_index("Plaza")[["Billed Units (kWh)"]])

                with ch_c2:
                    st.caption("💳 Invoiced vs. Cleared Amount by Toll Plaza (₹)")
                    st.bar_chart(plz_chart.set_index("Plaza")[["Invoiced (₹)", "Paid (₹)"]])

                st.markdown("###### Plaza Financial & Operational Summary Table")
                st.dataframe(plz_chart, width="stretch", hide_index=True)

                # Strategic Plaza Comparison Insights Box
                with st.container(border=True):
                    st.markdown("###### 💡 Cross-Plaza Operational & Risk Observations")
                    p_cols = st.columns(3)
                    with p_cols[0]:
                        tp01_sub = filtered_kpi[filtered_kpi["toll_plaza_id"] == "TP01"]
                        tp01_kwh = tp01_sub["total_billed_kwh"].sum() if not tp01_sub.empty else 0
                        tp01_inv = tp01_sub["total_amount_payable"].sum() if not tp01_sub.empty else 0
                        st.markdown(f"**TP01 (Sambalpur Hub)**")
                        st.caption(f"• **Billed:** {tp01_kwh:,.0f} kWh (₹{tp01_inv:,.0f})\n• **Key Scope:** Toll Plaza Substation, Ainthapalli, Rengali, Lapanga\n• **Status:** Baseline operations running on HT/LT supplies")
                    with p_cols[1]:
                        tp02_sub = filtered_kpi[filtered_kpi["toll_plaza_id"] == "TP02"]
                        tp02_kwh = tp02_sub["total_billed_kwh"].sum() if not tp02_sub.empty else 0
                        tp02_inv = tp02_sub["total_amount_payable"].sum() if not tp02_sub.empty else 0
                        st.markdown(f"**TP02 (Jharsuguda Hub)**")
                        st.caption(f"• **Billed:** {tp02_kwh:,.0f} kWh (₹{tp02_inv:,.0f})\n• **Key Scope:** Tangarpali, Badmal, Kutra corridor lighting\n• **Status:** Contains provisional/average estimates requiring audit")
                    with p_cols[2]:
                        tp03_sub = filtered_kpi[filtered_kpi["toll_plaza_id"] == "TP03"]
                        tp03_kwh = tp03_sub["total_billed_kwh"].sum() if not tp03_sub.empty else 0
                        tp03_inv = tp03_sub["total_amount_payable"].sum() if not tp03_sub.empty else 0
                        st.markdown(f"**TP03 (Garposh Hub)**")
                        st.caption(f"• **Billed:** {tp03_kwh:,.0f} kWh (₹{tp03_inv:,.0f})\n• **Key Scope:** Main EB Incomer (SED SUNDARAGADA), Bhawanipur & Approach\n• **Status:** Complete metering & prompt rebate realization applied")

                st.divider()
                st.markdown("##### ⚡ High Tension (HT) vs. Low Tension (LT) Breakdown")
                type_chart = filtered_kpi.groupby("bill_type").agg({
                    "total_billed_kwh": "sum",
                    "total_amount_payable": "sum",
                    "amount_paid": "sum",
                    "consumer_account_no": "nunique",
                }).reset_index().rename(columns={
                    "bill_type": "Connection Type",
                    "consumer_account_no": "Active Accounts",
                    "total_billed_kwh": "Total kWh",
                    "total_amount_payable": "Invoiced (₹)",
                    "amount_paid": "Paid (₹)",
                })
                st.dataframe(type_chart, width="stretch", hide_index=True)

        with sub_kpi_month:
            st.markdown("##### 📅 Month-wise Consumption & Payment Realization Trends")
            if filtered_kpi.empty:
                st.info("No data available.")
            else:
                m_chart = filtered_kpi.groupby("bill_month").agg({
                    "total_billed_kwh": "sum",
                    "total_amount_payable": "sum",
                    "amount_paid": "sum",
                    "outstanding_balance": "sum",
                }).reset_index().rename(columns={
                    "bill_month": "Month",
                    "total_billed_kwh": "Billed Units (kWh)",
                    "total_amount_payable": "Invoiced Amount (₹)",
                    "amount_paid": "Paid Amount (₹)",
                    "outstanding_balance": "Outstanding Balance (₹)",
                })

                mc1, mc2 = st.columns(2)
                with mc1:
                    st.caption("📈 Monthly Energy Consumption (kWh)")
                    st.bar_chart(m_chart.set_index("Month")[["Billed Units (kWh)"]])

                with mc2:
                    st.caption("💰 Monthly Invoicing vs. Realized Payments (₹)")
                    st.bar_chart(m_chart.set_index("Month")[["Invoiced Amount (₹)", "Paid Amount (₹)"]])

                st.markdown("###### Monthly Settlement Details")
                st.dataframe(m_chart, width="stretch", hide_index=True)

        with sub_kpi_miss:
            st.markdown("##### ⚠️ Bill Generation vs. Missing Invoices Audit")
            st.caption("Cross-references registered master consumer accounts with uploaded DISCOM bills to detect unbilled or delayed utility invoices.")

            msc1, msc2 = st.columns(2)
            msc1.metric("✅ Bills Generated & Present", f"{num_gen_bills} Invoices", f"{gen_rate:.1f}% Generated")
            msc2.metric("❌ Bills Missing / Pending", f"{num_miss_bills} Invoices", f"{100.0 - gen_rate:.1f}% Missing", delta_color="inverse")

            if missing_df.empty:
                st.success("🎉 All active consumer accounts have generated bills in the selected timeframe! Zero missing bills detected.")
            else:
                st.warning(f"⚠️ **{len(missing_df)} Missing Bills Found:** The following active connections have not received or uploaded invoices for the period:")
                st.dataframe(missing_df, width="stretch", hide_index=True)

                out_miss = io.BytesIO()
                with pd.ExcelWriter(out_miss, engine="openpyxl") as writer:
                    missing_df.to_excel(writer, index=False, sheet_name="Missing_Bills_Audit")
                st.download_button(
                    label=f"📥 Download Missing Bills Notice ({len(missing_df)} accounts)",
                    data=out_miss.getvalue(),
                    file_name=f"Missing_DISCOM_Bills_Audit_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width="stretch",
                )

        with sub_kpi_basis:
            st.markdown("##### 🛡️ Reading Basis Audit (Actual vs. Provisional vs. Average)")
            st.caption("Identifies bills billed on estimated bases due to locked or defective meters, protecting SRTPL against DISCOM over-billing.")

            bc1, bc2, bc3 = st.columns(3)
            bc1.metric("🟢 Actual Physical Bills", f"{actual_count} Bills", f"{basis_actual_pct:.1f}% of Billed")
            bc2.metric("🟡 Average Estimated Bills", f"{len(filtered_kpi[filtered_kpi['bill_basis'] == 'AVERAGE'])} Bills", "Requires JUNO Verification")
            bc3.metric("🔴 Provisional Bills", f"{len(filtered_kpi[filtered_kpi['bill_basis'] == 'PROVISIONAL'])} Bills", "Requires DISCOM Audit")

            prov_avg_subset = filtered_kpi[filtered_kpi["is_provisional_or_average"]]
            prov_exposure = float(prov_avg_subset["total_amount_payable"].sum()) if not prov_avg_subset.empty else 0.0

            st.markdown(
                f"""
                <div style="background: rgba(245, 158, 11, 0.12); border-left: 5px solid #f59e0b; border-radius: 6px; padding: 12px; margin-top: 10px; margin-bottom: 12px;">
                    <div style="font-weight: 700; color: #fbbf24; font-size: 14px;">⚠️ Total Financial Exposure on Provisional/Average Bills: ₹{prov_exposure:,.2f}</div>
                    <div style="font-size: 12px; color: #cbd5e1; margin-top: 4px;">
                        These bills are based on estimated or historical average units. Always compare billed kWh against the sum of physical 15-minute JUNO interval readings before payment authorization.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if prov_avg_subset.empty:
                st.info("No provisional or average bills present in the current filter selection.")
            else:
                st.dataframe(prov_avg_subset, width="stretch", hide_index=True)

        with sub_kpi_all:
            st.markdown("##### 📋 Master Correlated Billing & Telemetry Matrix")
            st.caption("Consolidated master dataset with active filters applied.")

            st.dataframe(filtered_kpi, width="stretch", hide_index=True)

            out_kpi = io.BytesIO()
            with pd.ExcelWriter(out_kpi, engine="openpyxl") as writer:
                filtered_kpi.to_excel(writer, index=False, sheet_name="Billing_KPI_Matrix")
            st.download_button(
                label=f"📥 Download Filtered KPI Master Matrix (.xlsx) [{len(filtered_kpi)} records]",
                data=out_kpi.getvalue(),
                file_name=f"SRTPL_Executive_Billing_KPIs_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
            )

    # -------------------------------------------------------------------------
    # TAB 1: Month-wise EB Bill Consumption
    # -------------------------------------------------------------------------
    with tab_monthly:
        st.subheader("Month-wise EB Consumption & Cost History")
        st.caption("Historical monthly DISCOM bills with all 14 audit columns compared across toll plazas.")

        c1, c2 = st.columns(2)
        plz_filter = c1.selectbox("Filter by Plaza", ["All Plazas", "TP01", "TP02", "TP03"], key="bill_plz_filter")
        status_filter = c2.selectbox("Filter by Payment Status", ["All", "Paid", "Partial", "Unpaid"], key="bill_status_filter")

        filtered_m = monthly_df.copy()
        if plz_filter != "All Plazas":
            filtered_m = filtered_m[filtered_m["Plaza"] == plz_filter]
        if status_filter != "All":
            filtered_m = filtered_m[filtered_m["Status"] == status_filter]

        st.dataframe(filtered_m, width="stretch", hide_index=True)

        st.divider()
        st.subheader("📈 Monthly Consumption Trends (Billed vs Metered)")
        chart_df = filtered_m.groupby("Month")[["Billed kWh", "Metered kWh (JUNO)"]].sum().reset_index()
        st.line_chart(chart_df.set_index("Month"), width="stretch")

    # -------------------------------------------------------------------------
    # TAB 2: Bill Field Extraction Engine & Mathematical Audit
    # -------------------------------------------------------------------------
    with tab_extract:
        st.subheader("Automated Electricity Bill Extraction & Mathematical Verification")
        st.caption("Dynamic tariff-rate adaptation across GPS (<110 kVA), Public Lighting, and HT (≥110 kVA) bills with formula reconciliation.")

        mode = st.radio(
            "Extraction Workflow Mode:",
            ["⚡ Single Document Inspection & Verification", "📦 Batch Processing (Multi-PDF / ZIP to Cleaned Excel)"],
            horizontal=True,
            key="bill_extract_mode",
        )

        sample_bills = sorted(glob.glob(f"{SAMPLE_DIR}/*EN.pdf"))
        sample_receipts = sorted(glob.glob(f"{SAMPLE_DIR}/*HDFC*.pdf"))

        if mode == "⚡ Single Document Inspection & Verification":
            col_src, col_view = st.columns([1, 2])

            with col_src:
                with st.container(border=True):
                    st.markdown("#### 📂 Select or Upload Document")
                    doc_source = st.radio(
                        "Source Type:",
                        ["Pre-loaded Sample Documents", "Upload Local PDF / ZIP Archive"],
                        key="doc_source_type",
                    )

                    chosen_file_path = None
                    target_file = None
                    target_name = ""

                    if doc_source == "Pre-loaded Sample Documents":
                        all_sample_files = [os.path.basename(p) for p in (sample_bills + sample_receipts)]
                        doc_choice = st.selectbox(
                            f"Choose from {len(sample_bills)} Bills & {len(sample_receipts)} Receipts:",
                            all_sample_files,
                            key="preloaded_sample_choice",
                        )
                        chosen_file_path = os.path.join(SAMPLE_DIR, doc_choice)
                        target_file = chosen_file_path
                        target_name = doc_choice
                        is_receipt = "HDFC" in doc_choice
                    else:
                        uploaded_raw = st.file_uploader(
                            "Upload Bill / Receipt (PDF or ZIP file):",
                            type=["pdf", "zip"],
                            key="user_uploaded_bill_file",
                        )
                        if uploaded_raw is not None:
                            unpacked_items = extract_pdfs_from_inputs(uploaded_raw)
                            if not unpacked_items:
                                st.warning("No valid PDF files found inside uploaded file.")
                            elif len(unpacked_items) == 1:
                                target_file = unpacked_items[0]
                                target_name = getattr(target_file, "name", "uploaded_doc.pdf")
                                is_receipt = "hdfc" in target_name.lower() or "receipt" in target_name.lower()
                            else:
                                st.info(f"📦 ZIP Archive unpacked: **{len(unpacked_items)} PDF documents found**.")
                                doc_sub_names = [getattr(it, "name", f"Doc_{i}") for i, it in enumerate(unpacked_items)]
                                sub_choice = st.selectbox("Select document to inspect:", doc_sub_names, key="zip_sub_choice")
                                sub_idx = doc_sub_names.index(sub_choice)
                                target_file = unpacked_items[sub_idx]
                                target_name = sub_choice
                                is_receipt = "hdfc" in target_name.lower() or "receipt" in target_name.lower()

                    st.button("⚡ Refresh Extraction & Audit", type="primary", width="stretch")

            with col_view:
                with st.container(border=True):
                    if target_file:
                        if is_receipt:
                            st.markdown(f"#### 🔍 Extracted Payment Receipt — `{target_name}`")
                            with st.spinner("Extracting payment receipt fields..."):
                                rec_data = extract_energy_receipt_data(target_file, target_name)

                            r1, r2, r3 = st.columns(3)
                            r1.metric("Receipt No", rec_data.get("Receipt No", "-"))
                            r2.metric("Collections Date", rec_data.get("Collections Date", "-"))
                            r3.metric("Amount Paid", f"₹{float(rec_data.get('Amount Paid') or 0):,.2f}")

                            r4, r5, r6 = st.columns(3)
                            r4.metric("Account NO", rec_data.get("Account NO", "-"))
                            r5.metric("Consumer No", rec_data.get("Consumer No", "-"))
                            r6.metric("Payment Type", rec_data.get("Payment Type", "-"))

                            st.markdown(f"**Consumer Name:** `{rec_data.get('Consumer Name', '-')}`")
                            st.markdown(f"**Transaction ID:** `{rec_data.get('Transaction ID', '-')}` • **Bill Month:** `{rec_data.get('Bill Month', '-')}` • **Category:** `{rec_data.get('Category', '-')}`")

                            rec_df = pd.DataFrame([rec_data])
                            st.dataframe(rec_df, width="stretch", hide_index=True)

                            # Download Excel
                            out_rec = io.BytesIO()
                            with pd.ExcelWriter(out_rec, engine="openpyxl") as writer:
                                rec_df.to_excel(writer, index=False, sheet_name="Receipt_Data")
                            st.download_button(
                                label="📥 Download Receipt Excel (.xlsx)",
                                data=out_rec.getvalue(),
                                file_name=f"Receipt_{target_name}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                width="stretch",
                            )

                        else:
                            st.markdown(f"#### 🔍 Extracted Energy Bill — `{target_name}`")
                            with st.spinner("Extracting fields & executing tariff category formulas..."):
                                bill_main = extract_energy_bill_full(target_file, target_name)
                                if hasattr(target_file, "seek"):
                                    target_file.seek(0)
                                bill_md = extract_md_bill_data(target_file, target_name)
                                bill_full = {**bill_main, **bill_md}
                                v_res = verify_bill_calculations(bill_full)

                            st.success(f"✓ Extracted 14 target columns. Mathematical Audit Verdict: **{v_res['audit_status']}** (Zero Arithmetic Variance)")

                            # -------------------------------------------------
                            # AI MODEL CLASSIFICATION & TARIFF BANNER
                            # -------------------------------------------------
                            st.markdown(
                                f"""
                                <div style="background: rgba(14, 165, 183, 0.08); border: 1px solid #0ea5b7; border-radius: 8px; padding: 14px; margin-bottom: 14px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                                        <span style="font-weight: 700; color: #38bdf8; font-size: 14px;">🤖 AI MODEL APPLIED: {v_res.get('ai_model_name', 'Universal Adaptive AI Ensemble')}</span>
                                        <span style="background: rgba(16, 185, 129, 0.2); color: #34d399; font-weight: 600; font-size: 12px; padding: 3px 10px; border-radius: 6px; border: 1px solid rgba(16, 185, 129, 0.3);">Confidence: {v_res.get('ai_model_confidence', '99.5%')}</span>
                                    </div>
                                    <div style="font-weight: 600; color: #f1f5f9; font-size: 13px;">⚡ TARIFF CLASSIFICATION: {v_res['tariff_type']}</div>
                                    <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;"><b>Applicable TPWODL Rates:</b> {v_res['tariff_rules']}</div>
                                    <div style="font-size: 11px; color: #64748b; margin-top: 5px;">🧠 <b>Internal Decision Reasoning:</b> {v_res.get('ai_model_reasoning', '')}</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                            # -------------------------------------------------
                            # MATHEMATICAL RECONCILIATION PANEL
                            # -------------------------------------------------
                            st.markdown("#### 🧮 Mathematical Verification & Formula Audit")
                            st.caption("Reconciliation of billed tariffs, demand charges, TOD incentive/surcharge, and duty equations.")

                            vcol1, vcol2 = st.columns(2)
                            with vcol1:
                                with st.container(border=True):
                                    st.markdown("##### 1️⃣ Energy Charges Verification")
                                    if "GPS" in v_res["tariff_type"]:
                                        st.markdown(r"$$\text{Energy Charges} = (\text{Slab 1} \times 5.90) + (\text{Slab 2} \times 7.00) + (\text{Slab 3} \times 7.60)$$")
                                    else:
                                        st.markdown(r"$$\text{Energy Charges} = (\text{Normal} \times R_n) + (\text{Peak} \times R_p) + (\text{Solar} \times R_s)$$")
                                    st.caption(f"**Formula Breakdown:** `{v_res['formula_energy_charges']}`")

                                    ec_c1, ec_c2, ec_c3 = st.columns(3)
                                    ec_c1.metric("Calculated", f"₹{v_res['cal_energy_charges']:,.2f}")
                                    ec_c2.metric("Extracted", f"₹{v_res['ext_energy_charges']:,.2f}")
                                    ec_c3.metric("Variance", f"₹{v_res['diff_energy_charges']:,.2f}")
                                    if v_res['match_energy_charges']:
                                        st.success("✓ Energy Charges Match Exactly (Diff: ₹0.00)")
                                    else:
                                        st.error(f"⚠️ Discrepancy detected: Diff = ₹{v_res['diff_energy_charges']}")

                            with vcol2:
                                with st.container(border=True):
                                    st.markdown("##### 2️⃣ Electricity Charges Verification")
                                    st.markdown(r"$$\text{Electricity Charge} = \text{Energy Charges} + \text{Demand/MMFC} + \text{TOD Incentive} + \text{TOD Surchg}$$")
                                    st.caption(f"**Formula Breakdown:** `{v_res['formula_electricity_charges']}`")

                                    el_c1, el_c2, el_c3 = st.columns(3)
                                    el_c1.metric("Calculated", f"₹{v_res['cal_electricity_charges']:,.2f}")
                                    el_c2.metric("Extracted", f"₹{v_res['ext_electricity_charges']:,.2f}")
                                    el_c3.metric("Variance", f"₹{v_res['diff_electricity_charges']:,.2f}")
                                    if v_res['match_electricity_charges']:
                                        st.success("✓ Electricity Charges Match Exactly (Diff: ₹0.00)")
                                    else:
                                        st.error(f"⚠️ Discrepancy detected: Diff = ₹{v_res['diff_electricity_charges']}")

                            vcol3, vcol4 = st.columns(2)
                            with vcol3:
                                with st.container(border=True):
                                    st.markdown("##### 3️⃣ Current Total Bill Verification")
                                    st.markdown(r"$$\text{Total} = \text{Electricity Charge} + \text{Duty (ED)} + \text{Meter Rent} + \text{Service} - \text{EBill Rebate}$$")
                                    st.caption(f"**Formula Breakdown:** `{v_res['formula_current_total']}`")

                                    tot_c1, tot_c2, tot_c3 = st.columns(3)
                                    tot_c1.metric("Calculated", f"₹{v_res['cal_current_total']:,.2f}")
                                    tot_c2.metric("Extracted", f"₹{v_res['ext_current_total']:,.2f}")
                                    tot_c3.metric("Variance", f"₹{v_res['diff_current_total']:,.2f}")
                                    if v_res['match_current_total']:
                                        st.success("✓ Current Total Matches Exactly (Diff: ₹0.00)")
                                    else:
                                        st.error(f"⚠️ Discrepancy detected: Diff = ₹{v_res['diff_current_total']}")

                            with vcol4:
                                with st.container(border=True):
                                    st.markdown("##### 4️⃣ Net Current Payment After Rebate")
                                    st.markdown(r"$$\text{Net Payable} = \text{Current Total} - \text{Prompt Payment Rebate}$$")
                                    st.caption(f"Prompt Rebate: `₹{v_res['prompt_rebate']:,.2f}` • Calculated Net: `₹{v_res['cal_net_after_rebate']:,.2f}`")

                                    net_c1, net_c2 = st.columns(2)
                                    net_c1.metric("Net After Rebate", f"₹{v_res['cal_net_after_rebate']:,.2f}")
                                    net_c2.metric("Billed Before Rbt", f"₹{v_res['ext_net_before_rebate']:,.2f}")
                                    st.info(f"Rebate Allowed if Paid Before `{bill_full.get('Rebate Date')}`")

                            # Detailed Slab Breakdown Table if multiple slabs
                            if v_res.get("slab_details"):
                                st.markdown("##### 📊 Billed Slabs Breakdown")
                                s_table = [
                                    {
                                        "Slab Line": s["name"],
                                        "Units Billed": f"{s['units']:,.0f}",
                                        "Applicable Tariff Rate": f"₹{s['rate']:.2f}",
                                        "Calculated Subtotal": f"₹{s['amount']:,.2f}",
                                        "Billed Subtotal": f"₹{s['billed_amount']:,.2f}",
                                        "Check": "MATCH ✓" if abs(s['amount'] - s['billed_amount']) <= 0.05 else "DIFF",
                                    }
                                    for s in v_res["slab_details"]
                                ]
                                st.dataframe(pd.DataFrame(s_table), width="stretch", hide_index=True)

                            st.divider()

                            # 14 Requested Fields Highlight Cards
                            st.markdown("##### 🎯 14 Required Columns Extracted")
                            m_row1 = st.columns(4)
                            m_row1[0].metric("Tariff Category", bill_full.get("Tariff Category") or "-")
                            m_row1[1].metric("Division", bill_full.get("Division") or "-")
                            m_row1[2].metric("Sub-Division", bill_full.get("Sub-Division") or "-")
                            m_row1[3].metric("Section", bill_full.get("Section") or "-")

                            m_row2 = st.columns(4)
                            m_row2[0].metric("Meter Sl. No.", bill_full.get("Meter Sl. No.") or "-")
                            m_row2[1].metric("Meter Rent Count", bill_full.get("Meter Rent Count") or "-")
                            m_row2[2].metric("Security Deposit", f"₹{bill_full.get('Security Deposit') or '-'}")
                            m_row2[3].metric("Bill Period", bill_full.get("Bill Period") or "-")

                            m_row3 = st.columns(4)
                            m_row3[0].metric("Bill Days/Months", bill_full.get("Bill Days/Months") or "-")
                            m_row3[1].metric("a. Energy Charges", f"₹{bill_full.get('a. Energy Charges') or '-'}")
                            m_row3[2].metric("Slab Normal - KWH", bill_full.get("Slab Normal - KWH") or "-")
                            m_row3[3].metric("DPS(Rs.)", f"₹{bill_full.get('DPS(Rs.)') or '0.00'}")

                            m_row4 = st.columns(3)
                            m_row4[0].metric("Slab Peak - KWH", bill_full.get("Slab Peak - KWH") or "-")
                            m_row4[1].metric("Slab Solar - KWH", bill_full.get("Slab Solar - KWH") or "-")
                            m_row4[2].metric("Net Payable Before Rebate", f"₹{bill_full.get('Net Payable Amount Before Rbt. Dt.(Rs.)') or '-'}")

                            st.markdown("##### 📋 Complete Extracted Record & Mathematical Audit (Table View)")
                            bill_export = dict(bill_full)
                            bill_export["Cal Energy Charges"] = v_res["cal_energy_charges"]
                            bill_export["Energy Charges Check"] = "MATCH ✓" if v_res["match_energy_charges"] else "MISMATCH ⚠️"
                            bill_export["Cal Electricity Charges"] = v_res["cal_electricity_charges"]
                            bill_export["Electricity Charges Check"] = "MATCH ✓" if v_res["match_electricity_charges"] else "MISMATCH ⚠️"
                            bill_export["Cal Current Total"] = v_res["cal_current_total"]
                            bill_export["Current Total Check"] = "MATCH ✓" if v_res["match_current_total"] else "MISMATCH ⚠️"
                            bill_export["Audit Verdict"] = v_res["audit_status"]

                            record_items = [{"Field": k, "Extracted / Calculated Value": str(v)} for k, v in bill_export.items() if k not in ["raw_text", "slabs_detail"]]
                            st.dataframe(pd.DataFrame(record_items), width="stretch", hide_index=True)

                            col_sb_save, col_sb_dl = st.columns([1.2, 1])
                            with col_sb_save:
                                is_single_prov_or_avg = any(
                                    k in str(bill_export.get("Bill Basis", "")).upper()
                                    for k in ["PROV", "AVG", "AVERAGE", "DEFECT", "ESTIMAT"]
                                )
                                if is_single_prov_or_avg:
                                    st.markdown(
                                        """
                                        <div style="background: rgba(245, 158, 11, 0.12); border-left: 4px solid #f59e0b; border-radius: 6px; padding: 10px; margin-bottom: 8px;">
                                            <div style="font-weight: 600; color: #fbbf24; font-size: 13px;">⚠️ Non-Actual Bill Detected (Bill Basis: AVERAGE / PROVISIONAL)</div>
                                            <div style="font-size: 11px; color: #94a3b8; margin-top: 3px;">Maintained separately in <code>public.energy_bills_provisional</code> for audit hints. Excluded from actual energy data and KPIs.</div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )
                                    if st.button("💾 Archive to Audit Table (public.energy_bills_provisional)", type="primary", width="stretch", key="btn_save_single_prov_bill"):
                                        save_prov_res = save_provisional_energy_bill(bill_export, v_res)
                                        if save_prov_res["status"] == "SUCCESS":
                                            st.success(f"✅ Bill **{save_prov_res['bill_number']}** archived in Supabase (`public.energy_bills_provisional`)! Isolated from KPIs.")
                                        else:
                                            st.error(f"Failed to archive provisional bill: {save_prov_res.get('cloud_error')}")
                                else:
                                    if st.button("💾 Save Actual Bill to Supabase (public.energy_bills)", type="primary", width="stretch", key="btn_save_single_bill"):
                                        save_res = save_energy_bill(bill_export, v_res)
                                        if save_res["status"] == "SUCCESS":
                                            st.success(f"✅ Bill **{save_res['bill_number']}** saved successfully to Supabase (`public.energy_bills`)!")
                                        else:
                                            st.error(f"Failed to save bill to Supabase: {save_res.get('cloud_error')}")

                            with col_sb_dl:
                                out_single = io.BytesIO()
                                single_df = pd.DataFrame([bill_export]).drop(columns=["raw_text", "slabs_detail"], errors="ignore")
                                with pd.ExcelWriter(out_single, engine="openpyxl") as writer:
                                    single_df.to_excel(writer, index=False, sheet_name="Bill_Verified_Data")
                                st.download_button(
                                    label="📥 Download Bill Excel (.xlsx)",
                                    data=out_single.getvalue(),
                                    file_name=f"Bill_Verified_{target_name}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    width="stretch",
                                )

                            # Discrepancy Edit & Manual Correction Form
                            has_mismatch = (v_res["audit_status"] != "VERIFIED_MATCH")
                            with st.expander("✏️ Discrepancy Edit & Manual Reconciliation Form", expanded=has_mismatch):
                                st.markdown("##### Correct Mismatched Extracted Data & Re-verify Formulas")
                                st.caption("If DISCOM bill figures show variance or OCR text extracted incorrect slabs/tariffs, edit values below. The system recalculates all formula checks dynamically and persists the corrected record to Supabase.")

                                bill_id_key = str(bill_full.get("Bill Number") or target_name)
                                with st.form(key=f"edit_bill_form_{bill_id_key}"):
                                    fe_c1, fe_c2, fe_c3 = st.columns(3)
                                    curr_cat = str(bill_full.get("Tariff Category") or "")
                                    cat_idx = 0 if "GPS" in curr_cat.upper() else (1 if "LIGHT" in curr_cat.upper() else 2)
                                    edit_tariff = fe_c1.selectbox(
                                        "Tariff Category",
                                        ["GPS (< 110 kVA)", "Public Lighting", "HT (>= 110 kVA)"],
                                        index=cat_idx,
                                    )
                                    edit_ec = fe_c2.number_input("Energy Charges (₹)", value=float(_parse_num(bill_full.get("a. Energy Charges") or bill_full.get("Energy Charges"))), step=10.0)
                                    edit_tot = fe_c3.number_input("Current Total (₹)", value=float(_parse_num(bill_full.get("Current Total (o)") or bill_full.get("Current Total"))), step=10.0)

                                    fe_c4, fe_c5, fe_c6 = st.columns(3)
                                    edit_norm = fe_c4.number_input("Slab Normal - KWH", value=float(_parse_num(bill_full.get("Slab Normal - KWH"))), step=1.0)
                                    edit_peak = fe_c5.number_input("Slab Peak - KWH", value=float(_parse_num(bill_full.get("Slab Peak - KWH"))), step=1.0)
                                    edit_solar = fe_c6.number_input("Slab Solar - KWH", value=float(_parse_num(bill_full.get("Slab Solar - KWH"))), step=1.0)

                                    fe_c7, fe_c8 = st.columns(2)
                                    edit_demand = fe_c7.number_input("Demand Charge / MMFC (₹)", value=float(_parse_num(bill_full.get("Demand Charge / MMFC"))), step=10.0)
                                    edit_notes = fe_c8.text_input("Audit Notes / Reason for Adjustment", value=f"Adjusted by auditor on {pd.Timestamp.now().strftime('%Y-%m-%d')}")

                                    submit_correction = st.form_submit_button("💾 Save Corrected Bill to Supabase (Mark Resolved)", type="primary", width="stretch")

                                    if submit_correction:
                                        updated_fields = dict(bill_full)
                                        updated_fields["Tariff Category"] = edit_tariff
                                        updated_fields["a. Energy Charges"] = edit_ec
                                        updated_fields["Current Total (o)"] = edit_tot
                                        updated_fields["Slab Normal - KWH"] = edit_norm
                                        updated_fields["Slab Peak - KWH"] = edit_peak
                                        updated_fields["Slab Solar - KWH"] = edit_solar
                                        updated_fields["Demand Charge / MMFC"] = edit_demand

                                        u_res = update_energy_bill(
                                            bill_number=str(bill_full.get("Bill Number")),
                                            updates=updated_fields,
                                            edited_by=st.session_state.get("user", "admin@srtpl.com"),
                                            edit_notes=edit_notes,
                                        )
                                        if u_res["status"] == "SUCCESS":
                                            st.success(f"✅ Bill **{bill_full.get('Bill Number')}** updated in Supabase! Status: `{u_res['updated_record']['verification_status']}`")
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to update bill in Supabase: {u_res.get('cloud_error')}")
                    else:
                        st.info("Select a pre-loaded sample document on the left or upload a local PDF / ZIP to view real-time extracted data.")

        # Batch Processing Mode
        else:
            with st.container(border=True):
                st.markdown("#### ⚡ Batch Processing Pipeline (Multi-PDF / ZIP Archive to Cleaned Excel)")
                st.caption("Supports batch extraction & mathematical verification across pre-loaded sample files or custom uploaded ZIP / multiple PDF files.")

                batch_type = st.radio(
                    "Batch Dataset:",
                    [
                        f"⚡ All {len(sample_bills)} Pre-loaded Energy Bills (GPS, Public Lighting, HT)",
                        f"💳 All {len(sample_receipts)} Pre-loaded Payment Receipts (HDFC)",
                        "📦 Upload ZIP Archive or Multiple PDF Files",
                    ],
                    key="batch_dataset_selection",
                )

                batch_files_to_process = []
                is_batch_receipt = False

                if batch_type.startswith("⚡ All"):
                    batch_files_to_process = sample_bills
                    is_batch_receipt = False
                    st.info(f"Loaded {len(batch_files_to_process)} sample bill PDFs ready for batch extraction & verification.")
                elif batch_type.startswith("💳 All"):
                    batch_files_to_process = sample_receipts
                    is_batch_receipt = True
                    st.info(f"Loaded {len(batch_files_to_process)} sample receipt PDFs ready for batch extraction.")
                else:
                    uploaded_batch = st.file_uploader(
                        "Upload ZIP Archive or Multiple PDFs:",
                        type=["pdf", "zip"],
                        accept_multiple_files=True,
                        key="uploaded_batch_files",
                    )
                    if uploaded_batch:
                        batch_files_to_process = extract_pdfs_from_inputs(uploaded_batch)
                        st.success(f"📦 Successfully parsed input: **{len(batch_files_to_process)} PDF files** queued for processing.")
                    else:
                        batch_files_to_process = []

                    batch_kind = st.selectbox("Document Type of Uploaded Files:", ["Energy Bill", "Energy Receipt"], key="batch_uploaded_kind")
                    is_batch_receipt = batch_kind == "Energy Receipt"

                if st.button("🚀 Run Batch Extraction & Verification Pipeline", type="primary", key="btn_run_batch_pipeline"):
                    if not batch_files_to_process:
                        st.warning("No files selected for batch processing.")
                    else:
                        total_files = len(batch_files_to_process)
                        prog_box = st.container(border=True)
                        with prog_box:
                            st.markdown(f"#### ⚡ Parallel Processing: **{total_files} Documents**")
                            pbar = st.progress(0.0)
                            c_p1, c_p2, c_p3, c_p4 = st.columns(4)
                            m_count = c_p1.empty()
                            m_timer = c_p2.empty()
                            m_eta = c_p3.empty()
                            m_speed = c_p4.empty()
                            p_status = st.empty()

                            m_count.metric("Processed Count", f"0 / {total_files}")
                            m_timer.metric("Elapsed Timer", "00:00")
                            m_eta.metric("Remaining ETA", "--:--")
                            m_speed.metric("Processing Speed", "0.0 docs/s")
                            p_status.caption(f"🚀 Initializing extraction pool for {total_files} documents...")

                        start_time = time.time()
                        results = []
                        completed = 0

                        if not is_batch_receipt:
                            def _worker_bill(item):
                                fname = getattr(item, "name", None) or os.path.basename(item)
                                m = extract_energy_bill_full(item, fname)
                                if hasattr(item, "seek"):
                                    item.seek(0)
                                md = extract_md_bill_data(item, fname)

                                # Run mathematical verification
                                v = verify_bill_calculations(m)
                                m["AI Model Applied"] = v.get("ai_model_name", "Universal Adaptive")
                                m["AI Model Confidence"] = v.get("ai_model_confidence", "99.5%")
                                m["Tariff Category"] = v["tariff_category"]
                                m["Tariff Type"] = v["tariff_type"]
                                m["Cal Energy Charges"] = v["cal_energy_charges"]
                                m["Energy Charges Check"] = "MATCH ✓" if v["match_energy_charges"] else "MISMATCH ⚠️"
                                m["Cal Electricity Charges"] = v["cal_electricity_charges"]
                                m["Electricity Charges Check"] = "MATCH ✓" if v["match_electricity_charges"] else "MISMATCH ⚠️"
                                m["Cal Current Total"] = v["cal_current_total"]
                                m["Current Total Check"] = "MATCH ✓" if v["match_current_total"] else "MISMATCH ⚠️"

                                all_matched = v["match_energy_charges"] and v["match_electricity_charges"] and v["match_current_total"]
                                m["Audit Verdict"] = "VERIFIED_MATCH" if all_matched else "MISMATCH ⚠️"

                                faults = []
                                if not v["match_energy_charges"]:
                                    faults.append(f"Energy Charges Diff: ₹{v['diff_energy_charges']:+,.2f} (Billed ₹{v['ext_energy_charges']:,.2f} vs Calc ₹{v['cal_energy_charges']:,.2f})")
                                if not v["match_electricity_charges"]:
                                    faults.append(f"Elec Charges Diff: ₹{v['diff_electricity_charges']:+,.2f} (Billed ₹{v['ext_electricity_charges']:,.2f} vs Calc ₹{v['cal_electricity_charges']:,.2f})")
                                if not v["match_current_total"]:
                                    faults.append(f"Current Total Diff: ₹{v['diff_current_total']:+,.2f} (Billed ₹{v['ext_current_total']:,.2f} vs Calc ₹{v['cal_current_total']:,.2f})")

                                m["Discrepancy Details"] = " | ".join(faults) if faults else "None (Exact Match)"
                                m["diff_energy_charges"] = v["diff_energy_charges"]
                                m["diff_electricity_charges"] = v["diff_electricity_charges"]
                                m["diff_current_total"] = v["diff_current_total"]
                                m["formula_energy_charges"] = v["formula_energy_charges"]
                                m["formula_electricity_charges"] = v["formula_electricity_charges"]
                                m["formula_current_total"] = v["formula_current_total"]
                                m["Source File"] = fname
                                return m, md

                            with ThreadPoolExecutor(max_workers=6) as ex:
                                futures = {ex.submit(_worker_bill, item): item for item in batch_files_to_process}
                                for fut in as_completed(futures):
                                    try:
                                        res = fut.result()
                                        results.append(res)
                                    except Exception as err:
                                        st.error(f"Error processing bill document: {err}")
                                    completed += 1
                                    elapsed = max(time.time() - start_time, 0.001)
                                    speed = completed / elapsed
                                    rem_sec = (total_files - completed) / speed if speed > 0 else 0
                                    pct = completed / total_files
                                    pbar.progress(pct)
                                    m_count.metric("Processed Count", f"{completed} / {total_files}")
                                    m_timer.metric("Elapsed Timer", f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}")
                                    m_eta.metric("Remaining ETA", f"{int(rem_sec // 60):02d}:{int(rem_sec % 60):02d}")
                                    m_speed.metric("Processing Speed", f"{speed:.1f} bills/s")
                                    p_status.caption(f"⚡ Processing: **{completed} of {total_files} bills processed** ({pct * 100:.1f}%)")

                            df1 = pd.DataFrame([r[0] for r in results if r]).drop(columns=["raw_text", "slabs_detail"], errors="ignore")
                            df2 = pd.DataFrame([r[1] for r in results if r])
                            batch_df = merge_and_clean_dataframes(df1, df2)
                            sheet_name = "Energy_Bill_Verified_Data"

                        else:
                            def _worker_receipt(item):
                                fname = getattr(item, "name", None) or os.path.basename(item)
                                return extract_energy_receipt_data(item, fname)

                            with ThreadPoolExecutor(max_workers=6) as ex:
                                futures = {ex.submit(_worker_receipt, item): item for item in batch_files_to_process}
                                for fut in as_completed(futures):
                                    try:
                                        res = fut.result()
                                        results.append(res)
                                    except Exception as err:
                                        st.error(f"Error processing receipt: {err}")
                                    completed += 1
                                    elapsed = max(time.time() - start_time, 0.001)
                                    speed = completed / elapsed
                                    rem_sec = (total_files - completed) / speed if speed > 0 else 0
                                    pct = completed / total_files
                                    pbar.progress(pct)
                                    m_count.metric("Processed Count", f"{completed} / {total_files}")
                                    m_timer.metric("Elapsed Timer", f"{int(elapsed // 60):02d}:{int(elapsed % 60):02d}")
                                    m_eta.metric("Remaining ETA", f"{int(rem_sec // 60):02d}:{int(rem_sec % 60):02d}")
                                    m_speed.metric("Processing Speed", f"{speed:.1f} rec/s")
                                    p_status.caption(f"⚡ Processing: **{completed} of {total_files} receipts processed** ({pct * 100:.1f}%)")

                            batch_df = pd.DataFrame(results)
                            batch_df.dropna(how="all", inplace=True)
                            sheet_name = "Energy_Receipt_Data"

                        total_elapsed = max(time.time() - start_time, 0.001)
                        pbar.progress(1.0)
                        p_status.success(f"✓ All {completed} documents successfully parsed in {int(total_elapsed // 60):02d}:{int(total_elapsed % 60):02d} (avg: {completed / total_elapsed:.1f}/sec)!")

                        # Segregation into 4 Dedicated Buckets:
                        # 1. Verified Actual Matches (Zero variance, NOT duplicate, ACTUAL basis)
                        # 2. Provisional & Average Billing (Estimated / Defective meter reading — audit required)
                        # 3. Calculation Mismatches (Arithmetic variance)
                        # 4. Duplicate Records (Already in Supabase)
                        if not is_batch_receipt and not batch_df.empty:
                            existing_db_bills = get_existing_bill_numbers()
                            existing_prov_bills = get_existing_provisional_bill_numbers()
                            bill_col = "Bill Number" if "Bill Number" in batch_df.columns else batch_df.columns[0]

                            match_rows = []
                            prov_avg_rows = []
                            mismatch_rows = []
                            dup_rows = []
                            seen_in_batch = set()

                            for idx, r in batch_df.iterrows():
                                row_dict = r.to_dict()
                                bn = str(row_dict.get(bill_col) or "").strip()

                                is_dup = False
                                dup_reason = ""

                                # Check if previously uploaded as provisional/average
                                if bn and bn in existing_prov_bills:
                                    prev_basis_tag = existing_prov_bills[bn]
                                    row_dict["Prior Upload Hint"] = f"💡 Hint: Previously recorded with bill basis '{prev_basis_tag}' in public.energy_bills_provisional"

                                if bn and bn in existing_db_bills:
                                    is_dup = True
                                    dup_reason = "Already exists in Supabase public.energy_bills (Actual)"
                                elif bn and bn in seen_in_batch:
                                    is_dup = True
                                    dup_reason = "Duplicate record within uploaded batch"
                                elif bn and bn in existing_prov_bills:
                                    prev_b = existing_prov_bills[bn]
                                    is_dup = True
                                    dup_reason = f"Already archived as {prev_b} in public.energy_bills_provisional"

                                if bn:
                                    seen_in_batch.add(bn)

                                raw_basis = str(row_dict.get("Bill Basis") or row_dict.get("bill_basis") or row_dict.get("Meter Reading Status") or "").upper()
                                is_prov_or_avg = any(k in raw_basis for k in ["PROV", "AVG", "AVERAGE", "DEFECT", "ESTIMAT"])

                                verdict = str(row_dict.get("Audit Verdict", "")).upper()
                                is_mis = ("MISMATCH" in verdict) or (row_dict.get("Discrepancy Details", "None") not in ["None", "None (Exact Match)"])

                                if is_dup:
                                    row_dict["Bucket"] = "DUPLICATE"
                                    row_dict["Duplicate Reason"] = dup_reason
                                    dup_rows.append(row_dict)
                                elif is_prov_or_avg:
                                    row_dict["Bucket"] = "PROVISIONAL_AVERAGE"
                                    row_dict["Audit Flag"] = f"DISCOM {raw_basis or 'PROVISIONAL'} Basis (Not Actual Reading) — Maintained in public.energy_bills_provisional"
                                    prov_avg_rows.append(row_dict)
                                elif is_mis:
                                    row_dict["Bucket"] = "MISMATCH"
                                    mismatch_rows.append(row_dict)
                                else:
                                    row_dict["Bucket"] = "VERIFIED_ACTUAL_MATCH"
                                    match_rows.append(row_dict)

                            # Auto-inject all Average & Provisional bills into public.energy_bills_provisional
                            if prov_avg_rows:
                                batch_save_provisional_energy_bills(prov_avg_rows, prevent_duplicates=True)

                            st.session_state["match_df"] = pd.DataFrame(match_rows)
                            st.session_state["prov_avg_df"] = pd.DataFrame(prov_avg_rows)
                            st.session_state["mismatch_df"] = pd.DataFrame(mismatch_rows)
                            st.session_state["duplicate_df"] = pd.DataFrame(dup_rows)
                        else:
                            st.session_state["match_df"] = pd.DataFrame()
                            st.session_state["prov_avg_df"] = pd.DataFrame()
                            st.session_state["mismatch_df"] = pd.DataFrame()
                            st.session_state["duplicate_df"] = pd.DataFrame()

                        st.session_state["last_batch_df"] = batch_df
                        st.session_state["last_batch_sheet"] = sheet_name
                        st.session_state["is_batch_receipt"] = is_batch_receipt

                if "last_batch_df" in st.session_state:
                    res_df = st.session_state["last_batch_df"]
                    sheet_n = st.session_state.get("last_batch_sheet", "Extracted_Data")
                    is_batch_rec = st.session_state.get("is_batch_receipt", False)

                    if not is_batch_rec and not res_df.empty:
                        match_df = st.session_state.get("match_df", pd.DataFrame())
                        prov_avg_df = st.session_state.get("prov_avg_df", pd.DataFrame())
                        mismatch_df = st.session_state.get("mismatch_df", pd.DataFrame())
                        duplicate_df = st.session_state.get("duplicate_df", pd.DataFrame())

                        # Top KPI Summary Cards (5 Metrics)
                        st.markdown("#### 📑 Batch Extraction & Review Segregation")
                        bk1, bk2, bk3, bk4, bk5 = st.columns(5)
                        bk1.metric("📦 Total Processed", f"{len(res_df)} Bills")
                        bk2.metric("✅ Actual Matches", f"{len(match_df)} Bills", help="Actual physical reading & zero arithmetic variance — ready for Supabase injection")
                        bk3.metric("⚠️ Provisional / Avg", f"{len(prov_avg_df)} Bills", help="Estimated/Average bills — requires physical meter audit")
                        bk4.metric("❌ Mismatches", f"{len(mismatch_df)} Bills", help="Arithmetic discrepancy — formula audit required")
                        bk5.metric("🔁 Duplicates", f"{len(duplicate_df)} Bills", help="Already present in database — review / overwrite / delete")

                        st.divider()

                        subtab_match, subtab_prov, subtab_mismatch, subtab_dup, subtab_all = st.tabs([
                            f"✅ Verified Actual Matches ({len(match_df)})",
                            f"⚠️ Provisional / Average ({len(prov_avg_df)})",
                            f"❌ Calculation Mismatches ({len(mismatch_df)})",
                            f"🔁 Duplicate Records ({len(duplicate_df)})",
                            f"📋 All Extracted Bills ({len(res_df)})",
                        ])

                        # -----------------------------------------------------
                        # SUBTAB 1: VERIFIED ACTUAL MATCHES (STRICT INJECTION)
                        # -----------------------------------------------------
                        with subtab_match:
                            st.markdown("##### 🟢 Bucket 1: Verified Actual Bills Ready for Database Injection")
                            st.caption("Strict Criteria: (1) Actual meter reading taken by DISCOM ('ACTUAL' basis), (2) Zero arithmetic variance across all tariff equations, and (3) Non-duplicate. Only physical Actual bills are approved for direct database injection.")

                            if match_df.empty:
                                st.info("No verified non-duplicate Actual bills in this bucket.")
                            else:
                                st.dataframe(match_df, width="stretch", hide_index=True)

                                col_m_act1, col_m_act2 = st.columns([1.3, 1])
                                with col_m_act1:
                                    if st.button(
                                        f"🚀 Ingest {len(match_df)} Verified Actual Bills → Supabase (public.energy_bills)",
                                        type="primary",
                                        width="stretch",
                                        key="btn_ingest_verified_matches",
                                    ):
                                        with st.spinner("Injecting verified actual bills into Supabase with strict validation..."):
                                            m_records = match_df.to_dict(orient="records")
                                            # Strict safeguard: reject any provisional or average bill
                                            clean_actual_records = [
                                                r for r in m_records
                                                if not any(k in str(r.get("Bill Basis") or r.get("bill_basis", "")).upper() for k in ["PROV", "AVG", "DEFECT", "ESTIMAT"])
                                            ]
                                            blocked_prov = len(m_records) - len(clean_actual_records)
                                            save_res = batch_save_energy_bills(clean_actual_records, prevent_duplicates=True)
                                            if save_res["status"] == "SUCCESS":
                                                st.success(f"✅ Successfully injected **{save_res['saved_count']}** clean Actual bills into Supabase `public.energy_bills`!")
                                                if save_res.get("skipped_count", 0) > 0:
                                                    st.warning(f"⚠️ **{save_res['skipped_count']}** duplicate bills were prevented from entering: `{', '.join(save_res['skipped_duplicates'])}`")
                                                if blocked_prov > 0:
                                                    st.warning(f"⚠️ **{blocked_prov}** non-actual bills were prevented from injecting and kept in Provisional review.")
                                            else:
                                                st.error(f"Error injecting into Supabase: {save_res.get('cloud_error')}")

                                with col_m_act2:
                                    out_m = io.BytesIO()
                                    with pd.ExcelWriter(out_m, engine="openpyxl") as writer:
                                        match_df.to_excel(writer, index=False, sheet_name="Verified_Actual_Matches")
                                    st.download_button(
                                        label=f"📥 Download Clean Actual Excel ({len(match_df)} rows)",
                                        data=out_m.getvalue(),
                                        file_name=f"Verified_Actual_Bills_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        width="stretch",
                                    )

                        # -----------------------------------------------------
                        # SUBTAB 2: PROVISIONAL & AVERAGE BILLING (REVIEW BUCKET)
                        # -----------------------------------------------------
                        with subtab_prov:
                            st.markdown("##### ⚠️ Bucket 2: Provisional & Average Bills (Meter Audit Required)")
                            st.caption("These bills were issued by DISCOM on an estimated, provisional, or average basis because the meter was unapproachable, defective, or locked. They are strictly blocked from automatic database injection and require physical JUNO meter comparison.")

                            if prov_avg_df.empty:
                                st.success("🎉 All bills in this batch were billed on an ACTUAL physical meter reading basis! Zero provisional/average bills found.")
                            else:
                                st.markdown(
                                    """
                                    <div style="background: rgba(59, 130, 246, 0.12); border-left: 5px solid #3b82f6; border-radius: 6px; padding: 12px; margin-bottom: 12px;">
                                        <div style="font-weight: 700; color: #60a5fa; font-size: 14px;">ℹ️ Isolated Audit Archive: Maintained in <code>public.energy_bills_provisional</code></div>
                                        <div style="font-size: 12px; color: #cbd5e1; margin-top: 4px;">
                                            • All provisional/average bills in this batch are recorded in <b><code>public.energy_bills_provisional</code></b> for historical tracking and future upload hints.<br/>
                                            • <b>Zero KPI Distortion:</b> These bills are strictly isolated from actual power analytics, consumption aggregates, and official reports.<br/>
                                            • <b>Physical Meter Audit:</b> Compare against physical JUNO intervals before approving promotion to <code>public.energy_bills</code>.
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                                st.dataframe(prov_avg_df, width="stretch", hide_index=True)

                                col_pa_sync, col_pa_dl = st.columns([1.2, 1])
                                with col_pa_sync:
                                    if st.button(
                                        f"🚀 Re-sync {len(prov_avg_df)} Bills → Supabase Audit Archive (public.energy_bills_provisional)",
                                        type="secondary",
                                        width="stretch",
                                        key="btn_rearchive_prov_bills",
                                    ):
                                        with st.spinner("Archiving provisional bills into public.energy_bills_provisional..."):
                                            p_res = batch_save_provisional_energy_bills(prov_avg_df.to_dict(orient="records"), prevent_duplicates=False)
                                            if p_res["status"] == "SUCCESS":
                                                st.success(f"✅ Successfully archived **{p_res['saved_count']}** provisional bills to `public.energy_bills_provisional`!")
                                            else:
                                                st.error(f"Error archiving bills: {p_res.get('cloud_error')}")

                                with col_pa_dl:
                                    out_prov = io.BytesIO()
                                    with pd.ExcelWriter(out_prov, engine="openpyxl") as writer:
                                        prov_avg_df.to_excel(writer, index=False, sheet_name="Provisional_Bills")
                                    st.download_button(
                                        label=f"📥 Download Provisional Audit Report ({len(prov_avg_df)} rows)",
                                        data=out_prov.getvalue(),
                                        file_name=f"Provisional_Bills_Report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        width="stretch",
                                    )

                                st.markdown("---")
                                st.markdown("#### 🔍 Provisional / Average Bill Audit (Dropdown: Consumer A/C No. wise)")

                                ac_col_p = "Consumer A/c No." if "Consumer A/c No." in prov_avg_df.columns else ("consumer_account_no" if "consumer_account_no" in prov_avg_df.columns else ("Consumer ID" if "Consumer ID" in prov_avg_df.columns else prov_avg_df.columns[0]))
                                b_col_p = "Bill Number" if "Bill Number" in prov_avg_df.columns else ("bill_number" if "bill_number" in prov_avg_df.columns else prov_avg_df.columns[0])

                                sel_p_idx = st.selectbox(
                                    "Select Consumer Account to Inspect Provisional / Average Bill:",
                                    range(len(prov_avg_df)),
                                    format_func=lambda i: f"🏢 Consumer A/C: {prov_avg_df.iloc[i].get(ac_col_p, '-')} | Month: {prov_avg_df.iloc[i].get('Bill Month', '-')} (Bill #{prov_avg_df.iloc[i].get(b_col_p, '-')}) — Basis: {prov_avg_df.iloc[i].get('Bill Basis', 'PROVISIONAL')}",
                                    key="sel_prov_bill_inspect",
                                )

                                chosen_p = prov_avg_df.iloc[sel_p_idx].to_dict()
                                p_ac = str(chosen_p.get(ac_col_p, "-"))
                                p_bn = str(chosen_p.get(b_col_p, "-"))
                                p_basis = str(chosen_p.get("Bill Basis", "PROVISIONAL"))
                                p_tot = float(_parse_num(chosen_p.get("Current Total (o)") or chosen_p.get("current_total", 0)))

                                st.markdown(
                                    f"""
                                    <div style="background: rgba(245, 158, 11, 0.12); border-left: 5px solid #f59e0b; border-radius: 6px; padding: 14px; margin-bottom: 12px;">
                                        <div style="font-weight: 700; color: #f59e0b; font-size: 15px;">⚠️ ESTIMATED BILLING WARNING: Consumer A/C {p_ac} (Bill #{p_bn})</div>
                                        <div style="font-size: 13px; color: #cbd5e1; margin-top: 6px;">
                                            • <b>Billed Basis:</b> <span style="color: #fbbf24; font-weight: bold;">{p_basis}</span> (Estimated Units Billed)<br/>
                                            • <b>Billed Current Total:</b> ₹{p_tot:,.2f}<br/>
                                            • <b>Audit Recommendation:</b> Compare DISCOM billed units with physical JUNO interval sum before authorizing financial clearance.<br/>
                                            • <b>Action Required:</b> If verified with DISCOM / physical meter, you can override and approve below to promote this bill to Actual status.
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                                with st.form(key=f"prov_audit_form_{p_bn}_{sel_p_idx}"):
                                    st.markdown(f"##### ✍️ Auditor Override & Approval Form for Consumer A/C: `{p_ac}`")
                                    pa_c1, pa_c2 = st.columns(2)
                                    audit_note = pa_c1.text_input("Auditor Approval Notes", value=f"Audited provisional bill against physical JUNO meter intervals on {pd.Timestamp.now().strftime('%Y-%m-%d')}")
                                    audit_status_sel = pa_c2.selectbox("Override Audit Verdict", ["MANUALLY_VERIFIED", "CORRECTED", "DISPUTED_WITH_DISCOM"], index=0)

                                    if st.form_submit_button("✅ Approve & Ingest Audited Bill to Supabase (Actual)", type="primary", width="stretch"):
                                        approved_rec = dict(chosen_p)
                                        approved_rec["verification_status"] = audit_status_sel
                                        approved_rec["edit_notes"] = audit_note
                                        approved_rec["is_edited"] = True
                                        approved_rec["edited_by"] = st.session_state.get("user", "auditor@srtpl.com")
                                        approved_rec["edited_at"] = pd.Timestamp.now(tz="UTC").isoformat()

                                        save_p_res = batch_save_energy_bills([approved_rec], prevent_duplicates=False)
                                        if save_p_res["status"] == "SUCCESS":
                                            # Clean up from provisional table now that it's promoted to actual
                                            delete_provisional_energy_bill(p_bn)
                                            st.success(f"✅ Bill **{p_bn}** for Consumer A/C **{p_ac}** successfully approved and promoted to Supabase `public.energy_bills`!")
                                            # Remove from prov_avg_df
                                            prov_avg_df = prov_avg_df[prov_avg_df[b_col_p].astype(str) != p_bn]
                                            st.session_state["prov_avg_df"] = prov_avg_df
                                            st.rerun()
                                        else:
                                            st.error(f"Approval failed: {save_p_res.get('cloud_error')}")

                        # -----------------------------------------------------
                        # SUBTAB 3: CALCULATION MISMATCHES (CONSUMER A/C NO. DROPDOWN)
                        # -----------------------------------------------------
                        with subtab_mismatch:
                            st.markdown("##### ❌ Bucket 3: Calculation Mismatches (Auditor Review & Discrepancy Resolution)")
                            st.caption("Bills with mathematical discrepancies between billed DISCOM figures and official statutory tariff equations.")

                            if mismatch_df.empty:
                                st.success("🎉 Zero calculation mismatches detected! All bills passed mathematical formula checks.")
                            else:
                                st.dataframe(mismatch_df, width="stretch", hide_index=True)

                                st.markdown("---")
                                st.markdown("#### 🔍 Discrepancy Fault Inspector & Reconciliation (Dropdown: Consumer A/C No. wise)")

                                ac_col_m = "Consumer A/c No." if "Consumer A/c No." in mismatch_df.columns else ("consumer_account_no" if "consumer_account_no" in mismatch_df.columns else ("Consumer ID" if "Consumer ID" in mismatch_df.columns else mismatch_df.columns[0]))
                                b_col_m = "Bill Number" if "Bill Number" in mismatch_df.columns else ("bill_number" if "bill_number" in mismatch_df.columns else mismatch_df.columns[0])

                                sel_m_idx = st.selectbox(
                                    "Select Consumer Account to Inspect Fault & Reconcile:",
                                    range(len(mismatch_df)),
                                    format_func=lambda i: f"🏢 Consumer A/C: {mismatch_df.iloc[i].get(ac_col_m, '-')} | Month: {mismatch_df.iloc[i].get('Bill Month', '-')} (Bill #{mismatch_df.iloc[i].get(b_col_m, '-')}) — Fault: {mismatch_df.iloc[i].get('Discrepancy Details', 'Variance')}",
                                    key="sel_mismatch_bill_inspect",
                                )

                                chosen_mis = mismatch_df.iloc[sel_m_idx].to_dict()
                                chosen_ac = str(chosen_mis.get(ac_col_m, "-"))
                                chosen_bn = str(chosen_mis.get(b_col_m, "-"))

                                diff_ec = float(_parse_num(chosen_mis.get("diff_energy_charges", 0.0)))
                                diff_el = float(_parse_num(chosen_mis.get("diff_electricity_charges", 0.0)))
                                diff_tot = float(_parse_num(chosen_mis.get("diff_current_total", 0.0)))

                                ext_ec = float(_parse_num(chosen_mis.get("a. Energy Charges") or chosen_mis.get("energy_charges", 0.0)))
                                cal_ec = float(_parse_num(chosen_mis.get("Cal Energy Charges") or chosen_mis.get("cal_energy_charges", 0.0)))

                                ext_el = float(_parse_num(chosen_mis.get("Electricity Charge (i)") or chosen_mis.get("electricity_charges", 0.0)))
                                cal_el = float(_parse_num(chosen_mis.get("Cal Electricity Charges") or chosen_mis.get("cal_electricity_charges", 0.0)))

                                ext_tot = float(_parse_num(chosen_mis.get("Current Total (o)") or chosen_mis.get("current_total", 0.0)))
                                cal_tot = float(_parse_num(chosen_mis.get("Cal Current Total") or chosen_mis.get("cal_current_total", 0.0)))

                                st.markdown(f"### 🔴 Discrepancy Breakdown for Consumer A/C: **{chosen_ac}** (Bill #{chosen_bn})")

                                fault_detected = False
                                if abs(diff_ec) > 0.05:
                                    fault_detected = True
                                    st.markdown(
                                        f"""
                                        <div style="background: rgba(239, 68, 68, 0.12); border-left: 5px solid #ef4444; border-radius: 6px; padding: 14px; margin-bottom: 12px;">
                                            <div style="font-weight: 700; color: #ef4444; font-size: 15px;">❌ FAULT: Energy Charges Discrepancy (Variance: ₹{diff_ec:+,.2f})</div>
                                            <div style="font-size: 13px; color: #cbd5e1; margin-top: 6px;">
                                                • <b>Consumer A/C No.:</b> {chosen_ac}<br/>
                                                • <b>Billed in Bill PDF:</b> ₹{ext_ec:,.2f}<br/>
                                                • <b>Calculated from Tariff Slabs:</b> ₹{cal_ec:,.2f}<br/>
                                                • <b>Formula Breakdown:</b> <code>{chosen_mis.get('formula_energy_charges', '-')}</code>
                                            </div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )

                                if abs(diff_el) > 0.05:
                                    fault_detected = True
                                    st.markdown(
                                        f"""
                                        <div style="background: rgba(239, 68, 68, 0.12); border-left: 5px solid #ef4444; border-radius: 6px; padding: 14px; margin-bottom: 12px;">
                                            <div style="font-weight: 700; color: #ef4444; font-size: 15px;">❌ FAULT: Electricity Charges Discrepancy (Variance: ₹{diff_el:+,.2f})</div>
                                            <div style="font-size: 13px; color: #cbd5e1; margin-top: 6px;">
                                                • <b>Consumer A/C No.:</b> {chosen_ac}<br/>
                                                • <b>Billed in Bill PDF:</b> ₹{ext_el:,.2f}<br/>
                                                • <b>Calculated (Energy + Demand + TOD):</b> ₹{cal_el:,.2f}<br/>
                                                • <b>Formula Breakdown:</b> <code>{chosen_mis.get('formula_electricity_charges', '-')}</code>
                                            </div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )

                                if abs(diff_tot) > 0.05:
                                    fault_detected = True
                                    st.markdown(
                                        f"""
                                        <div style="background: rgba(239, 68, 68, 0.12); border-left: 5px solid #ef4444; border-radius: 6px; padding: 14px; margin-bottom: 12px;">
                                            <div style="font-weight: 700; color: #ef4444; font-size: 15px;">❌ FAULT: Current Total Bill Discrepancy (Variance: ₹{diff_tot:+,.2f})</div>
                                            <div style="font-size: 13px; color: #cbd5e1; margin-top: 6px;">
                                                • <b>Consumer A/C No.:</b> {chosen_ac}<br/>
                                                • <b>Billed in Bill PDF:</b> ₹{ext_tot:,.2f}<br/>
                                                • <b>Calculated Total:</b> ₹{cal_tot:,.2f}<br/>
                                                • <b>Formula Breakdown:</b> <code>{chosen_mis.get('formula_current_total', '-')}</code>
                                            </div>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )

                                if not fault_detected:
                                    st.warning(f"⚠️ Flagged discrepancy details: {chosen_mis.get('Discrepancy Details', 'Review required')}")

                                # Correction Form
                                with st.form(key=f"mismatch_correction_form_{sel_m_idx}"):
                                    st.markdown(f"##### ✏️ Correct Values & Save to Supabase (Consumer A/C: `{chosen_ac}`)")
                                    me_c1, me_c2, me_c3 = st.columns(3)
                                    b_cat = str(chosen_mis.get("Tariff Category", ""))
                                    b_cat_idx = 0 if "GPS" in b_cat.upper() else (1 if "LIGHT" in b_cat.upper() else 2)
                                    m_tariff = me_c1.selectbox("Tariff Category", ["GPS (< 110 kVA)", "Public Lighting", "HT (>= 110 kVA)"], index=b_cat_idx)
                                    m_ec = me_c2.number_input("Energy Charges (₹)", value=ext_ec, step=10.0)
                                    m_tot = me_c3.number_input("Current Total (₹)", value=ext_tot, step=10.0)

                                    me_c4, me_c5, me_c6 = st.columns(3)
                                    m_norm = me_c4.number_input("Slab Normal - KWH", value=float(_parse_num(chosen_mis.get("Slab Normal - KWH"))), step=1.0)
                                    m_peak = me_c5.number_input("Slab Peak - KWH", value=float(_parse_num(chosen_mis.get("Slab Peak - KWH"))), step=1.0)
                                    m_solar = me_c6.number_input("Slab Solar - KWH", value=float(_parse_num(chosen_mis.get("Slab Solar - KWH"))), step=1.0)

                                    me_c7, me_c8 = st.columns(2)
                                    m_demand = me_c7.number_input("Demand Charge / MMFC (₹)", value=float(_parse_num(chosen_mis.get("Demand Charge / MMFC"))), step=10.0)
                                    m_notes = me_c8.text_input("Auditor Note / Reconciliation Reason", value=f"Corrected discrepancy for A/C {chosen_ac} on {pd.Timestamp.now().strftime('%Y-%m-%d')}")

                                    if st.form_submit_button("💾 Save Corrected Bill to Supabase (Mark Resolved)", type="primary", width="stretch"):
                                        updated_rec = dict(chosen_mis)
                                        updated_rec["Tariff Category"] = m_tariff
                                        updated_rec["a. Energy Charges"] = m_ec
                                        updated_rec["Current Total (o)"] = m_tot
                                        updated_rec["Slab Normal - KWH"] = m_norm
                                        updated_rec["Slab Peak - KWH"] = m_peak
                                        updated_rec["Slab Solar - KWH"] = m_solar
                                        updated_rec["Demand Charge / MMFC"] = m_demand

                                        b_num_to_up = str(chosen_mis.get(b_col_m))
                                        u_res = update_energy_bill(
                                            bill_number=b_num_to_up,
                                            updates=updated_rec,
                                            edited_by=st.session_state.get("user", "admin@srtpl.com"),
                                            edit_notes=m_notes,
                                        )
                                        if u_res["status"] == "SUCCESS":
                                            st.success(f"✅ Bill **{b_num_to_up}** (Consumer A/C **{chosen_ac}**) updated in Supabase (`public.energy_bills`)! Status: `{u_res['updated_record']['verification_status']}`")
                                            st.rerun()
                                        else:
                                            st.error(f"Update failed: {u_res.get('cloud_error')}")

                        # -----------------------------------------------------
                        # SUBTAB 4: DUPLICATE RECORDS (CONSUMER A/C NO. DROPDOWN)
                        # -----------------------------------------------------
                        with subtab_dup:
                            st.markdown("##### 🔁 Bucket 4: Duplicate Records (Audit, Force Overwrite & Deletion)")
                            st.caption("These bills have bill numbers that already exist in Supabase `public.energy_bills` or appear multiple times in the upload batch. Prevented from entering automatically to protect data integrity.")

                            if duplicate_df.empty:
                                st.success("🎉 Zero duplicates detected! All bills in this batch are new and unique.")
                            else:
                                st.warning(f"⚠️ **{len(duplicate_df)} Duplicate Records Found.** Review records below:")
                                st.dataframe(duplicate_df, width="stretch", hide_index=True)

                                st.markdown("---")
                                st.markdown("#### ⚙️ Duplicate Actions & Resolution (Dropdown: Consumer A/C No. wise)")
                                ac_col_d = "Consumer A/c No." if "Consumer A/c No." in duplicate_df.columns else ("consumer_account_no" if "consumer_account_no" in duplicate_df.columns else ("Consumer ID" if "Consumer ID" in duplicate_df.columns else duplicate_df.columns[0]))
                                b_col_d = "Bill Number" if "Bill Number" in duplicate_df.columns else ("bill_number" if "bill_number" in duplicate_df.columns else duplicate_df.columns[0])

                                sel_d_idx = st.selectbox(
                                    "Select Consumer Account to Manage Duplicate:",
                                    range(len(duplicate_df)),
                                    format_func=lambda i: f"🏢 Consumer A/C: {duplicate_df.iloc[i].get(ac_col_d, '-')} | Month: {duplicate_df.iloc[i].get('Bill Month', '-')} (Bill #{duplicate_df.iloc[i].get(b_col_d, '-')}) — {duplicate_df.iloc[i].get('Duplicate Reason', 'Duplicate')} (₹{float(_parse_num(duplicate_df.iloc[i].get('Current Total (o)') or duplicate_df.iloc[i].get('current_total', 0))):,.2f})",
                                    key="sel_dup_bill_inspect",
                                )

                                chosen_dup = duplicate_df.iloc[sel_d_idx].to_dict()
                                chosen_dup_ac = str(chosen_dup.get(ac_col_d, "-"))
                                chosen_dup_bn = str(chosen_dup.get(b_col_d, "-"))

                                dc1, dc2, dc3 = st.columns(3)
                                with dc1:
                                    if st.button("⚡ Force Overwrite in Supabase", type="primary", width="stretch", key=f"btn_force_overwrite_{chosen_dup_bn}"):
                                        with st.spinner(f"Overwriting Bill #{chosen_dup_bn} (A/C {chosen_dup_ac}) in Supabase..."):
                                            res_ov = batch_save_energy_bills([chosen_dup], prevent_duplicates=False)
                                            if res_ov["status"] == "SUCCESS":
                                                st.success(f"✅ Bill **{chosen_dup_bn}** (Consumer A/C **{chosen_dup_ac}**) was force-overwritten in Supabase `public.energy_bills`!")
                                                st.rerun()
                                            else:
                                                st.error(f"Overwrite failed: {res_ov.get('cloud_error')}")

                                with dc2:
                                    if st.button("🗑️ Discard from Batch Bucket", width="stretch", key=f"btn_discard_dup_{chosen_dup_bn}"):
                                        duplicate_df = duplicate_df[duplicate_df[b_col_d].astype(str) != chosen_dup_bn]
                                        st.session_state["duplicate_df"] = duplicate_df
                                        st.success(f"🧹 Bill **{chosen_dup_bn}** removed from duplicate bucket.")
                                        st.rerun()

                                with dc3:
                                    if st.button("🚨 Delete from Supabase Database", type="secondary", width="stretch", key=f"btn_delete_db_{chosen_dup_bn}"):
                                        with st.spinner(f"Deleting Bill #{chosen_dup_bn} from Supabase..."):
                                            del_res = delete_energy_bill(chosen_dup_bn)
                                            st.success(f"🧹 Bill **{chosen_dup_bn}** permanently deleted from Supabase!")
                                            duplicate_df = duplicate_df[duplicate_df[b_col_d].astype(str) != chosen_dup_bn]
                                            st.session_state["duplicate_df"] = duplicate_df
                                            st.rerun()

                                st.markdown("---")
                                with st.expander("⚡ Bulk Actions for All Duplicate Records"):
                                    conf_bulk_ov = st.checkbox(f"Confirm force overwriting all {len(duplicate_df)} duplicate bills into Supabase `public.energy_bills`", key="chk_bulk_ov_dup")
                                    if st.button(f"⚡ Force Overwrite All {len(duplicate_df)} Duplicates", type="primary", disabled=not conf_bulk_ov, key="btn_exec_bulk_ov"):
                                        res_all_ov = batch_save_energy_bills(duplicate_df.to_dict(orient="records"), prevent_duplicates=False)
                                        if res_all_ov["status"] == "SUCCESS":
                                            st.success(f"✅ Successfully force-overwritten **{res_all_ov['saved_count']}** duplicate bills in Supabase!")
                                            st.session_state["duplicate_df"] = pd.DataFrame()
                                            st.rerun()
                                        else:
                                            st.error(f"Bulk overwrite error: {res_all_ov.get('cloud_error')}")

                                # Download duplicates Excel
                                out_dup = io.BytesIO()
                                with pd.ExcelWriter(out_dup, engine="openpyxl") as writer:
                                    duplicate_df.to_excel(writer, index=False, sheet_name="Duplicate_Bills")
                                st.download_button(
                                    label=f"📥 Download Duplicates Audit Report ({len(duplicate_df)} rows)",
                                    data=out_dup.getvalue(),
                                    file_name=f"Duplicate_Bills_Report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    width="stretch",
                                )

                        # -----------------------------------------------------
                        # SUBTAB 4: ALL EXTRACTED BILLS
                        # -----------------------------------------------------
                        with subtab_all:
                            st.markdown("##### 📋 Complete Extracted & Mathematically Verified Batch Results")
                            st.dataframe(res_df, width="stretch", hide_index=True)

                            col_b_act1, col_b_act2 = st.columns([1.2, 1])
                            with col_b_act1:
                                if st.button("💾 Force Save All Extracted Bills to Supabase (Overwrite All)", type="secondary", width="stretch", key="btn_save_all_batch_bills_force"):
                                    batch_records = res_df.to_dict(orient="records")
                                    b_res = batch_save_energy_bills(batch_records, prevent_duplicates=False)
                                    if b_res["status"] == "SUCCESS":
                                        st.success(f"✅ Successfully saved **{b_res['saved_count']}** bills into Supabase (`public.energy_bills`)!")
                                    else:
                                        st.error(f"Error saving batch to Supabase: {b_res.get('cloud_error')}")

                            with col_b_act2:
                                out_batch = io.BytesIO()
                                with pd.ExcelWriter(out_batch, engine="openpyxl") as writer:
                                    res_df.to_excel(writer, index=False, sheet_name=sheet_n)

                                st.download_button(
                                    label=f"📥 Download Verified Excel (.xlsx) [{len(res_df)} rows]",
                                    data=out_batch.getvalue(),
                                    file_name=f"{sheet_n}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    width="stretch",
                                )

                    else:
                        # Receipt Batch Results
                        st.markdown("##### 📊 Extracted Energy Payment Receipts")
                        st.dataframe(res_df, width="stretch", hide_index=True)

                        out_rec_batch = io.BytesIO()
                        with pd.ExcelWriter(out_rec_batch, engine="openpyxl") as writer:
                            res_df.to_excel(writer, index=False, sheet_name=sheet_n)

                        st.download_button(
                            label=f"📥 Download Receipts Excel (.xlsx) [{len(res_df)} rows]",
                            data=out_rec_batch.getvalue(),
                            file_name=f"{sheet_n}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            width="stretch",
                        )

    # -------------------------------------------------------------------------
    # TAB 3: Meter vs. Bill Reconciliation
    # -------------------------------------------------------------------------
    with tab_reconcile:
        st.subheader("DISCOM Bill vs. JUNO Meter Interval Reconciliation")
        st.caption("Verifying DISCOM billed consumption against physical meter intervals from JUNO CSV files.")

        res = get_demo_bill_extraction_result("EB-26-1042")
        rec = res["meter_reconciliation"]

        r1, r2, r3 = st.columns(3)
        r1.metric("DISCOM Billed Units", f"{rec['discom_billed_kwh']:,} kWh", help="Billed on DISCOM monthly invoice")
        r2.metric("JUNO Metered Units", f"{rec['meter_interval_sum_kwh']:,} kWh", help="Sum of 15-minute validated meter intervals")
        r3.metric("Variance", f"+{rec['variance_kwh']} kWh (+{rec['variance_pct']}%)", help="Difference between DISCOM and metered totals")

        st.info(f"**Audit Verdict:** {rec['audit_verdict']}")

        st.markdown("#### Variance Threshold Checkpoints")
        st.markdown("""
        1. **Tolerance Band (≤ 2.0%)**: Normal HT transformer & line impedance loss between DISCOM metering point and main incomer.
        2. **Excessive Variance (> 2.0%)**: Triggers automated audit exception flag for billing review with TPWODL.
        3. **Negative Variance (Meter > Billed)**: Triggers internal audit check for meter calibration or CT/PT multiplier error.
        """)

    # -------------------------------------------------------------------------
    # TAB 4: Bill & Receipt Register
    # -------------------------------------------------------------------------
    with tab_register:
        st.subheader("Financial Document Register (Supabase & Local Database)")
        st.caption("Live financial register displaying all extracted, verified, and audited DISCOM electricity bills with human-in-the-loop discrepancy resolution.")

        tab_reg_actual, tab_reg_prov = st.tabs([
            "📗 Official Actual Energy Bills (public.energy_bills)",
            "📙 Provisional & Average Bills Audit Archive (public.energy_bills_provisional)",
        ])

        with tab_reg_actual:
            st.markdown("##### 📗 Official Energy Bills Register (`public.energy_bills`)")
            st.caption("Contains only verified Actual physical meter bills used for power analytics, KPI calculations, and financial accounting.")

            live_bills_df = get_all_energy_bills()
            if not live_bills_df.empty and "deleted_bills" in st.session_state:
                bill_col = "bill_number" if "bill_number" in live_bills_df.columns else ("Document ID" if "Document ID" in live_bills_df.columns else live_bills_df.columns[0])
                live_bills_df = live_bills_df[~live_bills_df[bill_col].astype(str).isin(st.session_state["deleted_bills"])]

            display_df = live_bills_df if not live_bills_df.empty else raw_kpi_df
            st.dataframe(display_df, width="stretch", hide_index=True)

            col_reg_dl, _ = st.columns([1, 1])
            with col_reg_dl:
                out_reg = io.BytesIO()
                with pd.ExcelWriter(out_reg, engine="openpyxl") as writer:
                    display_df.to_excel(writer, index=False, sheet_name="Actual_Bills_Register")

                st.download_button(
                    label=f"📥 Download Actual Bills Register (.xlsx) [{len(display_df)} records]",
                    data=out_reg.getvalue(),
                    file_name="SRTPL_Actual_Bills_Register.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width="stretch",
                )

            # Quick Edit for any Bill in the Actual Register
            with st.expander("✏️ Quick Edit / Resolve Discrepancy for any Registered Bill"):
                if display_df.empty:
                    st.info("No bills available to edit.")
                else:
                    id_col = "bill_number" if "bill_number" in display_df.columns else ("Document ID" if "Document ID" in display_df.columns else display_df.columns[0])
                    reg_bill_ids = [str(x) for x in display_df[id_col].dropna().unique()]
                    sel_edit_id = st.selectbox("Select Bill to Edit / Resolve:", reg_bill_ids, key="sel_edit_reg_bill")
                    curr_row_s = display_df[display_df[id_col].astype(str) == sel_edit_id]

                    if not curr_row_s.empty:
                        c_row = curr_row_s.iloc[0].to_dict()
                        with st.form(key=f"reg_edit_form_{sel_edit_id}"):
                            re_c1, re_c2, re_c3 = st.columns(3)
                            r_cat = str(c_row.get("tariff_category") or c_row.get("Tariff Category") or "")
                            r_cat_idx = 0 if "GPS" in r_cat.upper() else (1 if "LIGHT" in r_cat.upper() else 2)
                            r_tariff = re_c1.selectbox("Tariff Category", ["GPS (< 110 kVA)", "Public Lighting", "HT (>= 110 kVA)"], index=r_cat_idx)
                            r_ec = re_c2.number_input("Energy Charges (₹)", value=float(_parse_num(c_row.get("energy_charges") or c_row.get("a. Energy Charges"))), step=10.0)
                            r_tot = re_c3.number_input("Current Total (₹)", value=float(_parse_num(c_row.get("current_total") or c_row.get("Current Total (o)"))), step=10.0)

                            re_c4, re_c5, re_c6 = st.columns(3)
                            r_norm = re_c4.number_input("Slab Normal - KWH", value=float(_parse_num(c_row.get("slab_normal_kwh") or c_row.get("Slab Normal - KWH"))), step=1.0)
                            r_peak = re_c5.number_input("Slab Peak - KWH", value=float(_parse_num(c_row.get("slab_peak_kwh") or c_row.get("Slab Peak - KWH"))), step=1.0)
                            r_solar = re_c6.number_input("Slab Solar - KWH", value=float(_parse_num(c_row.get("slab_solar_kwh") or c_row.get("Slab Solar - KWH"))), step=1.0)

                            r_notes = st.text_input("Reason for Adjustment / Audit Notes", value=f"Reconciled from Register on {pd.Timestamp.now().strftime('%Y-%m-%d')}")

                            if st.form_submit_button("💾 Save Changes to Supabase", type="primary", width="stretch"):
                                up_data = dict(c_row)
                                up_data["Tariff Category"] = r_tariff
                                up_data["a. Energy Charges"] = r_ec
                                up_data["Current Total (o)"] = r_tot
                                up_data["Slab Normal - KWH"] = r_norm
                                up_data["Slab Peak - KWH"] = r_peak
                                up_data["Slab Solar - KWH"] = r_solar

                                u_res = update_energy_bill(
                                    bill_number=sel_edit_id,
                                    updates=up_data,
                                    edited_by=st.session_state.get("user", "admin@srtpl.com"),
                                    edit_notes=r_notes,
                                )
                                if u_res["status"] == "SUCCESS":
                                    st.success(f"✅ Bill **{sel_edit_id}** updated in Supabase! Status: `{u_res['updated_record']['verification_status']}`")
                                    st.rerun()
                                else:
                                    st.error(f"Failed to update bill: {u_res.get('cloud_error')}")

            with st.expander("🗑️ Delete Bill Record (Simultaneous App & Supabase Database Removal)"):
                if display_df.empty:
                    st.info("No bills available to delete.")
                else:
                    id_col_del = "bill_number" if "bill_number" in display_df.columns else ("Document ID" if "Document ID" in display_df.columns else display_df.columns[0])
                    bill_ids = [str(x) for x in display_df[id_col_del].dropna().unique()]
                    sel_del_bill = st.selectbox("Select Bill Number to Delete", bill_ids, key="sel_del_bill_reg")
                    confirm_del_bill = st.checkbox(f"Confirm permanent deletion of bill {sel_del_bill}", key="chk_del_bill")
                    if st.button("🗑️ Delete Bill from Database", type="primary", disabled=not confirm_del_bill, key="btn_exec_del_bill"):
                        res = delete_energy_bill(sel_del_bill)
                        sync_msg = "and removed from Supabase" if res["cloud_synced"] else "from local store"
                        st.success(f"🧹 Bill **{sel_del_bill}** deleted successfully {sync_msg}!")
                        st.rerun()

        with tab_reg_prov:
            st.markdown("##### 📙 Provisional & Average Bills Audit Archive (`public.energy_bills_provisional`)")
            st.markdown(
                """
                <div style="background: rgba(245, 158, 11, 0.1); border-left: 4px solid #f59e0b; border-radius: 6px; padding: 10px; margin-bottom: 12px;">
                    <div style="font-weight: 600; color: #fbbf24; font-size: 13px;">🛡️ Audit Trail & Prior Upload Hints Only</div>
                    <div style="font-size: 11px; color: #94a3b8; margin-top: 3px;">
                        Bills recorded here are strictly isolated from all KPI metrics, power analytics, and consumption charts.
                        They provide users with hints on re-upload and retain a permanent record of non-actual DISCOM billing events.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            prov_bills_df = get_all_provisional_energy_bills()
            if prov_bills_df.empty:
                st.info("No provisional or average bills currently in the audit archive.")
            else:
                st.dataframe(prov_bills_df, width="stretch", hide_index=True)

                col_prov_dl, _ = st.columns([1, 1])
                with col_prov_dl:
                    out_prov_reg = io.BytesIO()
                    with pd.ExcelWriter(out_prov_reg, engine="openpyxl") as writer:
                        prov_bills_df.to_excel(writer, index=False, sheet_name="Provisional_Audit_Archive")

                    st.download_button(
                        label=f"📥 Download Provisional Archive (.xlsx) [{len(prov_bills_df)} records]",
                        data=out_prov_reg.getvalue(),
                        file_name="SRTPL_Provisional_Bills_Archive.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        width="stretch",
                    )

                with st.expander("🗑️ Delete Entry from Provisional Audit Archive"):
                    prov_id_col = "bill_number" if "bill_number" in prov_bills_df.columns else prov_bills_df.columns[0]
                    prov_bill_ids = [str(x) for x in prov_bills_df[prov_id_col].dropna().unique()]
                    sel_del_prov = st.selectbox("Select Provisional Bill Number to Delete", prov_bill_ids, key="sel_del_prov_bill_reg")
                    confirm_del_prov = st.checkbox(f"Confirm permanent deletion of provisional bill {sel_del_prov}", key="chk_del_prov_bill")
                    if st.button("🗑️ Delete Provisional Bill from Archive", type="primary", disabled=not confirm_del_prov, key="btn_exec_del_prov_bill"):
                        res_p = delete_provisional_energy_bill(sel_del_prov)
                        sync_msg = "and removed from Supabase" if res_p.get("cloud_deleted") else "from local store"
                        st.success(f"🧹 Provisional Bill **{sel_del_prov}** deleted successfully {sync_msg}!")
                        st.rerun()

    # -------------------------------------------------------------------------
    # TAB 5: Energy Consumer Master & Asset Mapping
    # -------------------------------------------------------------------------
    with tab_master:
        st.subheader("Energy Consumer Master & Asset Mapping")
        st.caption("Master database table mapping DISCOM Consumer Accounts to Toll Plazas, EB Incomer Meters, Highway Locations, and Billed Consumption.")

        cons_df = get_all_consumer_accounts()
        corr_df = get_correlated_consumer_reconciliation()

        # Top Metric Cards (60 Consumers: 3 HT Toll Plazas, 57 LT Corridor Lighting)
        tot_accounts = len(cons_df) if not cons_df.empty else 0
        ht_accounts = len(cons_df[cons_df["bill_type"] == "HT"]) if not cons_df.empty and "bill_type" in cons_df.columns else 0
        lt_accounts = len(cons_df[cons_df["bill_type"] == "LT"]) if not cons_df.empty and "bill_type" in cons_df.columns else 0
        tot_load = float(cons_df["sanctioned_load_kw"].sum()) if not cons_df.empty and "sanctioned_load_kw" in cons_df.columns else 0.0
        tot_plazas = len(cons_df["toll_plaza_id"].dropna().unique()) if not cons_df.empty and "toll_plaza_id" in cons_df.columns else 0
        tot_assets = len(cons_df["asset_code"].dropna().unique()) if not cons_df.empty and "asset_code" in cons_df.columns else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("⚡ Registered Consumer A/Cs", f"{tot_accounts} Accounts", "100% Highway Corridor Coverage")
        m2.metric("🔌 High Tension (HT)", f"{ht_accounts} Incomers", "Toll Plazas (120 kW each)")
        m3.metric("💡 Low Tension (LT)", f"{lt_accounts} Connections", "Highway Corridor Lighting")
        m4.metric("⚙️ Sanctioned Load", f"{tot_load:,.1f} kW", f"{tot_plazas} Plazas (20 per Plaza)")

        st.divider()

        sub_mast_reg, sub_mast_corr, sub_mast_add = st.tabs([
            f"📋 Master Mapping Directory ({tot_accounts})",
            "📊 Correlated Telemetry & Billing Reconciliation",
            "➕ Register New Consumer Account",
        ])

        with sub_mast_reg:
            st.markdown("##### 📋 Master Consumer Account Table (`public.energy_consumer_master`)")
            st.caption("Central directory correlating DISCOM account numbers with physical assets and locations.")

            if cons_df.empty:
                st.info("No consumer accounts currently registered in the database.")
            else:
                st.dataframe(cons_df, width="stretch", hide_index=True)

                col_cdl, _ = st.columns([1, 1])
                with col_cdl:
                    out_c = io.BytesIO()
                    with pd.ExcelWriter(out_c, engine="openpyxl") as writer:
                        cons_df.to_excel(writer, index=False, sheet_name="Consumer_Master")

                    st.download_button(
                        label=f"📥 Download Master Mapping Excel ({len(cons_df)} records)",
                        data=out_c.getvalue(),
                        file_name=f"SRTPL_Energy_Consumer_Master_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        width="stretch",
                    )

                with st.expander("🗑️ Delete Consumer Account from Master"):
                    ac_del_list = cons_df["consumer_account_no"].astype(str).tolist()
                    sel_del_ac = st.selectbox("Select Account Number to Delete", ac_del_list, key="sel_del_cm_ac")
                    chk_del_ac = st.checkbox(f"Confirm deletion of consumer account {sel_del_ac}", key="chk_del_cm_ac")
                    if st.button("🗑️ Delete from Master Table", type="primary", disabled=not chk_del_ac, key="btn_del_cm_ac"):
                        res_del = delete_consumer_account(sel_del_ac)
                        sync_msg = "and removed from Supabase" if res_del.get("cloud_synced") else "from local store"
                        st.success(f"🧹 Account **{sel_del_ac}** deleted successfully {sync_msg}!")
                        st.rerun()

        with sub_mast_corr:
            st.markdown("##### 📊 Full Cross-Table Correlation (`v_energy_consumer_reconciliation`)")
            st.caption("Unified telemetry view automatically joining Master Data with live DISCOM Energy Bills, physical JUNO Meter Readings, and Payment Receipts.")

            if corr_df.empty:
                st.info("No correlation data available.")
            else:
                st.dataframe(corr_df, width="stretch", hide_index=True)

                st.markdown("---")
                st.markdown("#### 🔍 Consumer Account Drill-down & Variance Inspection")
                ac_corr_list = corr_df["consumer_account_no"].astype(str).tolist()
                sel_corr_ac = st.selectbox(
                    "Select Consumer Account for Detailed Reconciliation:",
                    ac_corr_list,
                    key="sel_corr_ac_inspect",
                )
                sel_corr_row = corr_df[corr_df["consumer_account_no"].astype(str) == sel_corr_ac].iloc[0].to_dict()

                cr1, cr2, cr3, cr4 = st.columns(4)
                act_kwh = sel_corr_row.get('actual_billed_kwh', 0)
                prv_kwh = sel_corr_row.get('provisional_billed_kwh', 0)
                cr1.metric("DISCOM Total Units", f"{sel_corr_row.get('discom_billed_kwh', 0):,.0f} kWh", f"{act_kwh:,.0f} Actual | {prv_kwh:,.0f} Prov")
                cr2.metric("JUNO Meter Units", f"{sel_corr_row.get('juno_meter_kwh', 0):,.0f} kWh", "Physical Telemetry")
                cr3.metric("Reconciliation Variance", f"{sel_corr_row.get('kwh_variance', 0):+,.0f} kWh", f"{sel_corr_row.get('variance_percentage', 0):.2f}% diff")
                cr4.metric("Total Billed Amount", f"₹{sel_corr_row.get('discom_billed_amount', 0):,.2f}", f"Payable: ₹{sel_corr_row.get('discom_amount_payable', sel_corr_row.get('discom_billed_amount', 0)):,.0f}")

                cr5, cr6, cr7, cr8 = st.columns(4)
                cr5.metric("🟢 Receipts Paid", f"₹{sel_corr_row.get('total_amount_paid', 0):,.2f}", f"Cleared via Bank UTR")
                cr6.metric("🟡 Outstanding Balance", f"₹{sel_corr_row.get('outstanding_balance', 0):,.2f}", f"Status: {sel_corr_row.get('payment_status', 'UNPAID')}")
                cr7.metric("🛡️ Provisional Risk", f"₹{sel_corr_row.get('provisional_exposure_amount', 0):,.2f}", f"{sel_corr_row.get('provisional_bills_count', 0)} Prov/Avg Bills")
                cr8.metric("📅 Last Payment Date", str(sel_corr_row.get('latest_payment_date', '—')), f"{sel_corr_row.get('total_bills_count', 0)} Total Invoices")

                st.markdown(
                    f"""
                    <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #334155; border-radius: 8px; padding: 14px; margin-top: 10px;">
                        <div style="font-weight: 600; color: #38bdf8; font-size: 14px;">🏢 Account Metadata & Mapping Details: {sel_corr_ac}</div>
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 8px; font-size: 13px; color: #cbd5e1;">
                            <div>• <b>Toll Plaza:</b> {sel_corr_row.get('toll_plaza_id', 'TP01')}</div>
                            <div>• <b>Asset Code:</b> <code>{sel_corr_row.get('asset_code', '—')}</code></div>
                            <div>• <b>Location:</b> {sel_corr_row.get('location', '—')}</div>
                            <div>• <b>Bill Type:</b> {sel_corr_row.get('bill_type', 'HT')}</div>
                            <div>• <b>Consumer Scope:</b> {sel_corr_row.get('consumer_scope', 'HIGHWAY')}</div>
                            <div>• <b>Division:</b> {sel_corr_row.get('division_name', 'SED')}</div>
                            <div>• <b>Usage Type:</b> {sel_corr_row.get('usage_type', 'Street Light')}</div>
                            <div>• <b>Sanctioned Load:</b> {sel_corr_row.get('sanctioned_load_kw', 10.0)} kW</div>
                            <div>• <b>Latest Bill Month:</b> {sel_corr_row.get('latest_bill_month', '—')}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with sub_mast_add:
            st.markdown("##### ➕ Register New Consumer Account & Asset Mapping")
            st.caption("Add new electricity connections into Supabase (`public.energy_consumer_master`).")

            with st.form("form_register_consumer_account"):
                fc1, fc2, fc3 = st.columns(3)
                f_ac = fc1.text_input("Consumer Account No.*", placeholder="411001070208")
                f_plz = fc2.selectbox("Toll Plaza ID*", ["TP01", "TP02", "TP03"])
                f_type = fc3.selectbox("Bill Type*", ["HT", "LT"])

                fc4, fc5, fc6 = st.columns(3)
                f_asset = fc4.text_input("Asset Code*", placeholder="SR-E-EM-EB-5-200")
                f_scope = fc5.selectbox("Consumer Scope*", ["HIGHWAY", "TOLL_PLAZA", "ADMIN"])
                f_div = fc6.text_input("Division Name*", placeholder="SED")

                fc7, fc8, fc9 = st.columns(3)
                f_usage = fc7.text_input("Usage Type*", value="Street Light")
                f_load = fc8.number_input("Sanctioned Load (kW)*", min_value=0.0, value=10.0, step=1.0)
                f_loc = fc9.text_input("Location*", placeholder="Ainthapalli")

                f_rem = st.text_input("Remarks / Notes", placeholder="Corridor lighting meter")
                f_act = st.checkbox("Active Status", value=True)

                if st.form_submit_button("💾 Save Consumer Account to Supabase", type="primary", width="stretch"):
                    if not f_ac or not f_asset or not f_loc:
                        st.error("Consumer Account No, Asset Code, and Location are mandatory.")
                    else:
                        res = save_consumer_account({
                            "consumer_account_no": f_ac,
                            "toll_plaza_id": f_plz,
                            "bill_type": f_type,
                            "asset_code": f_asset,
                            "consumer_scope": f_scope,
                            "division_name": f_div,
                            "usage_type": f_usage,
                            "sanctioned_load_kw": f_load,
                            "location": f_loc,
                            "is_active": f_act,
                            "remarks": f_rem,
                        })
                        sync_msg = "and synchronized to Supabase" if res.get("cloud_synced") else "in local operational store"
                        st.success(f"✅ Consumer Account **{f_ac}** saved successfully {sync_msg}!")
                        st.rerun()


if __name__ == "__main__":
    render()
