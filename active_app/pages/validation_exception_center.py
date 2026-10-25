import streamlit as st
import pandas as pd
from core.demo_store import (
    get_demo_exceptions,
    get_raw_exception_detail,
    apply_exception_raw_fix,
    reopen_exception,
    dismiss_exception,
    export_corrected_raw_csv,
    reset_demo_exceptions,
)
from exception_center.repository import ExceptionRepository
from exception_center.service import ExceptionService


def render():
    st.title("Validation & Exception Center")
    st.caption("Inspect raw CSV records, pinpoint errors, modify offending values, and resolve exceptions immediately.")

    # Show one-time flash notification after a resolution or reopening
    if "exception_flash_msg" in st.session_state:
        st.success(st.session_state.pop("exception_flash_msg"))

    repo = ExceptionRepository()
    all_df = repo.list_exceptions({})

    if all_df.empty:
        st.info("No exceptions currently recorded.")
        return

    # Top KPI summary cards
    open_err = len(all_df[(all_df["Status"] == "OPEN") & (all_df["Severity"] == "ERROR")])
    open_warn = len(all_df[(all_df["Status"] == "OPEN") & (all_df["Severity"] == "WARNING")])
    resolved_cnt = len(all_df[all_df["Status"].isin(["RESOLVED", "RESOLVED_BY_CORRECTION", "ACCEPTED_EXCEPTION", "DISMISSED"])])
    total_cnt = len(all_df)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🔴 Open Errors", str(open_err), help="Data rows excluded from KPI calculations until corrected")
    k2.metric("🟡 Open Warnings", str(open_warn), help="Threshold anomalies requiring operator review")
    k3.metric("🟢 Resolved / Fixed", str(resolved_cnt), help="Exceptions corrected or accepted with audit trail")
    k4.metric("📋 Total Monitored", str(total_cnt), help="All flagged entries across 5 sources")

    st.divider()

    # Two clear tabs: Active Open Exceptions vs Resolved History Archive
    tab_open, tab_resolved = st.tabs([
        f"🚨 Active Exceptions ({open_err + open_warn} Open)",
        f"✅ Resolved History ({resolved_cnt} Archived)",
    ])

    # -------------------------------------------------------------------------
    # TAB 1: ACTIVE OPEN EXCEPTIONS (Removed immediately when resolved)
    # -------------------------------------------------------------------------
    with tab_open:
        open_base_df = all_df[all_df["Status"] == "OPEN"].copy()

        if open_base_df.empty:
            st.success("🎉 All exceptions have been successfully resolved!")
            st.info(
                "There are currently zero open exceptions across all assets and toll plazas. "
                "All monitored raw data is validated, consistent, and ready for production KPIs. "
                "You can review previously resolved records or export audit reports in the 'Resolved History' tab."
            )
        else:
            # 1. Filter Controls for Open Exceptions
            f1, f2, f3 = st.columns(3)
            source_filter = f1.selectbox(
                "Filter by Source",
                ["All", "EB", "DG", "SOLAR", "TRANSFORMER", "UPS"],
                key="open_src_filter",
            )
            plaza_filter = f2.selectbox(
                "Filter by Plaza",
                ["All", "TP01", "TP02", "TP03"],
                key="open_plz_filter",
            )
            sev_filter = f3.selectbox(
                "Filter by Severity",
                ["All", "ERROR", "WARNING"],
                key="open_sev_filter",
            )

            open_df = open_base_df.copy()
            if source_filter != "All":
                open_df = open_df[open_df["Source"] == source_filter]
            if plaza_filter != "All":
                open_df = open_df[open_df["Plaza"] == plaza_filter]
            if sev_filter != "All":
                open_df = open_df[open_df["Severity"] == sev_filter]

            st.subheader(f"Active Flagged Exceptions ({len(open_df)} pending)")

            if open_df.empty:
                st.info("No open exceptions match the selected filter criteria.")
            else:
                cols_to_show = [
                    "Exception ID", "Source File", "Row", "Asset", "Plaza",
                    "Rule", "Severity", "Offending Value", "Expected", "Message"
                ]
                display_cols = [c for c in cols_to_show if c in open_df.columns]
                st.dataframe(open_df[display_cols], width="stretch", hide_index=True)

                st.divider()

                # 2. Raw Data Error Inspector & Modifier
                st.subheader("🔍 Raw Data Inspector & Modifier")
                st.caption("Inspect the exact CSV row that triggered the error, modify the value, and resolve it immediately.")

                available_ids = open_df["Exception ID"].tolist()
                selected_id = st.selectbox(
                    "Select Exception to Investigate & Correct:",
                    available_ids,
                    index=0,
                    key="open_selected_id",
                )

                detail = get_raw_exception_detail(selected_id)
                if not detail:
                    st.warning(f"No extended raw diagnostics available for {selected_id}.")
                else:
                    with st.container(border=True):
                        # Header banner
                        sev_icon = "🔴 ERROR" if detail["severity"] == "ERROR" else "🟡 WARNING"
                        st.markdown(f"### {sev_icon} on **{detail['source_file']}** — Row #{detail['row_number']}")
                        st.markdown(
                            f"**Asset:** `{detail['asset']}` ({detail['plaza']}) • "
                            f"**Rule:** `{detail['rule']}` • **Timestamp:** `{detail['timestamp']}`"
                        )
                        st.error(f"**Anomaly Reason:** {detail['message']}")

                        # Operator / Raw Entry Tracking Callout
                        st.warning(
                            f"👤 **Raw CSV Data Entry Tracking (Who entered this data):**\n\n"
                            f"• **Logged By:** `{detail.get('entered_by', 'Field Operator')}` (ID: `{detail.get('operator_id', '-')}`)\n\n"
                            f"• **Shift & Source:** `{detail.get('shift', 'Shift 1')}` • `{detail.get('entry_method', 'Manual Field Log')}`\n\n"
                            f"• **Tracked Root Cause:** {detail.get('root_cause', detail['message'])}"
                        )

                        # Context Comparison: Previous vs Error vs Next
                        st.markdown("#### 📊 Context Window: Previous vs. Error Row vs. Next Row")
                        context_rows = []
                        if detail.get("previous_reading"):
                            context_rows.append({"Position": "Previous Row (Valid)", **detail["previous_reading"]})
                        if detail.get("offending_reading"):
                            context_rows.append({"Position": "⚠️ OFFENDING ROW (ERROR)", **detail["offending_reading"]})
                        if detail.get("next_reading"):
                            context_rows.append({"Position": "Next Row (Valid)", **detail["next_reading"]})

                        if context_rows:
                            ctx_df = pd.DataFrame(context_rows)
                            st.dataframe(ctx_df, width="stretch", hide_index=True)

                        with st.expander("📄 View Complete Raw CSV Row Values"):
                            st.json(detail.get("raw_payload", {}))

                        st.divider()

                        # 3. Interactive Raw Data Modification Form
                        st.markdown("#### ✏️ Modify Raw Data & Remove from Exception List")
                        st.caption(f"Suggested correction: **{detail.get('suggested_fix', 'Review raw reading')}**")

                        mod_fields = detail.get("modifiable_fields", {})
                        if not mod_fields:
                            mod_fields = {
                                detail["parameter"]: {
                                    "label": detail["parameter"],
                                    "default": float(detail["source_value"].replace("%", "").replace("V", "").strip()) if detail["source_value"].replace(".", "", 1).isdigit() else 0.0,
                                    "expected": detail["expected_value"],
                                }
                            }

                        col_inputs = st.columns(len(mod_fields))
                        user_inputs = {}
                        for idx, (f_name, f_info) in enumerate(mod_fields.items()):
                            with col_inputs[idx]:
                                user_inputs[f_name] = st.number_input(
                                    f"Corrected {f_info.get('label', f_name)}:",
                                    value=float(f_info.get("default", 0.0)),
                                    help=f"Expected rule constraint: {f_info.get('expected', '')}",
                                    key=f"mod_input_{selected_id}_{f_name}",
                                )

                        justification = st.text_input(
                            "Correction Note / Root Cause Reason:",
                            value=f"Typo corrected by {st.session_state.get('user', 'admin@srtpl.com')}",
                            key=f"note_{selected_id}",
                        )

                        b1, b2, b3, b4 = st.columns(4)
                        with b1:
                            if st.button("💾 Apply Correction & Resolve", type="primary", width="stretch", key=f"btn_save_{selected_id}"):
                                for f_name, new_val in user_inputs.items():
                                    apply_exception_raw_fix(
                                        selected_id,
                                        f_name,
                                        new_val,
                                        user=st.session_state.get("user", "admin@srtpl.com"),
                                        resolution_type="CORRECTED",
                                        note=justification,
                                    )
                                st.session_state["exception_flash_msg"] = f"✅ Success! Exception {selected_id} corrected and immediately removed from the active list."
                                st.rerun()

                        with b2:
                            if st.button("🏷️ Accept as Meter Reset", width="stretch", key=f"btn_accept_{selected_id}"):
                                for f_name, new_val in user_inputs.items():
                                    apply_exception_raw_fix(
                                        selected_id,
                                        f_name,
                                        new_val,
                                        user=st.session_state.get("user", "admin@srtpl.com"),
                                        resolution_type="METER_RESET_ACCEPTED",
                                        note=f"Meter Reset Accepted: {justification}",
                                    )
                                st.session_state["exception_flash_msg"] = f"🏷️ Exception {selected_id} accepted as legitimate meter reset and removed from the active list."
                                st.rerun()

                        with b3:
                            if st.button("🗑️ Dismiss Exception", width="stretch", key=f"btn_dismiss_{selected_id}"):
                                dismiss_exception(
                                    selected_id,
                                    user=st.session_state.get("user", "admin@srtpl.com"),
                                    note=f"Dismissed by operator: {justification}",
                                )
                                st.session_state["exception_flash_msg"] = f"🗑️ Exception {selected_id} dismissed and removed from active list."
                                st.rerun()

                        with b4:
                            corrected_csv = export_corrected_raw_csv(selected_id)
                            st.download_button(
                                label="📥 Download Clean CSV",
                                data=corrected_csv,
                                file_name=f"CORRECTED_{detail['source_file']}",
                                mime="text/csv",
                                width="stretch",
                                key=f"dl_{selected_id}",
                            )

    # -------------------------------------------------------------------------
    # TAB 2: RESOLVED & ARCHIVED EXCEPTIONS (Audit Trail)
    # -------------------------------------------------------------------------
    with tab_resolved:
        resolved_df = all_df[all_df["Status"].isin(["RESOLVED", "RESOLVED_BY_CORRECTION", "ACCEPTED_EXCEPTION", "DISMISSED"])].copy()

        st.subheader(f"Resolved Exceptions Archive ({len(resolved_df)})")
        st.caption("Full audit trail of all corrected, accepted, or dismissed exceptions.")

        if resolved_df.empty:
            st.info("No exceptions have been resolved yet.")
        else:
            rf1, rf2 = st.columns(2)
            res_src_filter = rf1.selectbox("Filter Source", ["All", "EB", "DG", "SOLAR", "TRANSFORMER", "UPS"], key="res_src_filter")
            res_plz_filter = rf2.selectbox("Filter Plaza", ["All", "TP01", "TP02", "TP03"], key="res_plz_filter")

            if res_src_filter != "All":
                resolved_df = resolved_df[resolved_df["Source"] == res_src_filter]
            if res_plz_filter != "All":
                resolved_df = resolved_df[resolved_df["Plaza"] == res_plz_filter]

            cols_res = [
                "Exception ID", "Source File", "Row", "Asset", "Plaza",
                "Rule", "Offending Value", "Status", "Resolved By", "Resolved At", "Resolution Note"
            ]
            display_res_cols = [c for c in cols_res if c in resolved_df.columns]
            st.dataframe(resolved_df[display_res_cols], width="stretch", hide_index=True)

            st.divider()

            # Actions on resolved exceptions: Reopen or Download Clean CSV
            st.markdown("#### ↩️ Reopen or Export Resolved Record")
            sel_res_id = st.selectbox(
                "Select Resolved Exception:",
                resolved_df["Exception ID"].tolist(),
                index=0,
                key="sel_res_id",
            )

            rc1, rc2 = st.columns(2)
            with rc1:
                if st.button("↩️ Reopen Exception (Move Back to Open List)", width="stretch", key=f"btn_reopen_{sel_res_id}"):
                    reopen_exception(sel_res_id, user=st.session_state.get("user", "admin@srtpl.com"), note="Reopened by user from archive")
                    st.session_state["exception_flash_msg"] = f"↩️ Exception {sel_res_id} reopened and moved back to active exceptions list!"
                    st.rerun()

            with rc2:
                res_csv = export_corrected_raw_csv(sel_res_id)
                res_detail = get_raw_exception_detail(sel_res_id)
                res_fname = res_detail["source_file"] if res_detail else f"{sel_res_id}.csv"
                st.download_button(
                    label=f"📥 Download Corrected CSV ({sel_res_id})",
                    data=res_csv,
                    file_name=f"CORRECTED_{res_fname}",
                    mime="text/csv",
                    width="stretch",
                    key=f"dl_res_{sel_res_id}",
                )

    # -------------------------------------------------------------------------
    # Optional Testing Utility: Reset Demo Exceptions
    # -------------------------------------------------------------------------
    with st.expander("⚙️ Testing Controls"):
        st.caption("Quickly reset exceptions back to default open state for iterative test demonstrations.")
        if st.button("🔄 Reset All Exceptions to Default State", width="content"):
            reset_demo_exceptions()
            st.session_state["exception_flash_msg"] = "🔄 All demo exceptions have been reset to their initial state."
            st.rerun()


if __name__ == "__main__":
    render()
