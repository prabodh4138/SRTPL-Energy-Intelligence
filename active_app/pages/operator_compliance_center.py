import streamlit as st
import pandas as pd
from core.demo_store import (
    get_demo_operator_tracking,
    get_demo_plaza_monitoring_compliance,
    get_demo_exceptions,
)
from ui.navigation import navigate_to


def render():
    st.markdown('<div class="eyebrow">SRTPL / AUDIT & ACCOUNTABILITY</div>', unsafe_allow_html=True)
    st.title("Operator Accountability & Plaza Compliance Tracker")
    st.caption("Trace who entered wrong data in raw CSV files, and track which shift supervisors have not monitored plaza energy.")

    op_df = get_demo_operator_tracking()
    comp_df = get_demo_plaza_monitoring_compliance()
    exc_df = get_demo_exceptions()
    open_exc_cnt = len(exc_df[exc_df["Status"] == "OPEN"])

    # Overdue compliance count
    overdue_cnt = len(comp_df[comp_df["Inspection Status"] == "MISSED / OVERDUE"])

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("👥 Field Operators", str(len(op_df)), help="Technicians and operators logging raw CSV data")
    k2.metric("⚠️ Active Raw Typos", str(open_exc_cnt), help="Unresolved typos entered in raw CSV logs")
    k3.metric("📋 Shift SLA Compliance", "89%", help="Percentage of shifts with on-time energy verification")
    k4.metric("🚨 Overdue Plaza Reviews", str(overdue_cnt), help="Shifts exceeding the 24-hour unmonitored threshold")

    st.divider()

    tab_operators, tab_compliance = st.tabs([
        "👤 Raw CSV Data Entry Error Tracking",
        "📋 Plaza Monitoring Inactivity & Compliance",
    ])

    # -------------------------------------------------------------------------
    # TAB 1: WHO ENTERED WRONG DATA IN RAW CSV FILES
    # -------------------------------------------------------------------------
    with tab_operators:
        st.subheader("Operator Error Tracking & Raw Data Entry Scorecard")
        st.caption("Pinpoint which operator entered or transcribed anomalous readings into raw CSV files.")

        c1, c2 = st.columns(2)
        plz_f = c1.selectbox("Filter by Plaza", ["All", "TP01", "TP02", "TP03"], key="op_plz_filter")
        stat_f = c2.selectbox("Filter by Status", ["All", "NEEDS_ATTENTION", "RESOLVED_TRAINED", "VERIFIED_ACCURATE"], key="op_stat_filter")

        f_op = op_df.copy()
        if plz_f != "All":
            f_op = f_op[f_op["Plaza"] == plz_f]
        if stat_f != "All":
            f_op = f_op[f_op["Status"] == stat_f]

        st.dataframe(f_op, width="stretch", hide_index=True)

        st.divider()

        st.subheader("🔍 Detailed Operator Audit Drill-down")
        sel_op_name = st.selectbox(
            "Select Operator to Inspect Error History:",
            op_df["Operator Name"].tolist(),
            index=0,
            key="sel_op_drilldown",
        )

        op_row = op_df[op_df["Operator Name"] == sel_op_name].iloc[0]

        with st.container(border=True):
            st.markdown(f"### 👤 `{op_row['Operator Name']}` ({op_row['Role']}) — ID: `{op_row['Operator ID']}`")
            st.markdown(f"**Assigned Plaza:** `{op_row['Plaza']}` • **Standard Shift:** `{op_row['Shift']}`")
            st.markdown(f"**Historical Accuracy:** `{op_row['Accuracy %']}%` • **Total Logs Monitored:** `{op_row['Total Entries']:,}`")
            st.error(f"**Tracked Errors:** {op_row['Error Details']}")

            st.markdown("#### Traceable Raw CSV Records Associated with this Operator:")
            assoc_exc = exc_df[exc_df["Entered By"].str.contains(op_row["Operator Name"].split()[0])]
            if not assoc_exc.empty:
                cols_to_show = ["Exception ID", "Source File", "Row", "Asset", "Rule", "Offending Value", "Expected", "Status"]
                st.dataframe(assoc_exc[[c for c in cols_to_show if c in assoc_exc.columns]], width="stretch", hide_index=True)
            else:
                st.success("No active open exceptions associated with this operator.")

            b1, b2 = st.columns(2)
            with b1:
                if st.button(f"🎓 Record Refresher Training Completed for {sel_op_name}", width="stretch"):
                    st.success(f"Training record updated: {sel_op_name} completed refresher on decimal notation and meter counter logging.")
            with b2:
                if st.button("🔗 Go to Validation & Exception Center", width="stretch"):
                    navigate_to("Validation & Exceptions")

    # -------------------------------------------------------------------------
    # TAB 2: WHO HAS NOT MONITORED ENERGY CONSUMPTION IN PLAZA
    # -------------------------------------------------------------------------
    with tab_compliance:
        st.subheader("Plaza Energy Monitoring Compliance & Inactivity Board")
        st.caption("Identify which shift supervisors have not monitored or signed off on plaza energy consumption.")

        # Show Overdue Escalation Banner if any shift is overdue
        overdue_rows = comp_df[comp_df["Inspection Status"] == "MISSED / OVERDUE"]
        if not overdue_rows.empty:
            for _, o_row in overdue_rows.iterrows():
                st.error(
                    f"🚨 **CRITICAL INACTIVITY ALERT at {o_row['Plaza']}:** Supervisor `{o_row['Supervisor Name']}` "
                    f"({o_row['Shift']}) has **NOT monitored energy consumption**! "
                    f"Last check was `{o_row['Last Monitored Time']}`. SLA Status: `{o_row['Compliance SLA']}`."
                )

        f_comp_plz = st.selectbox("Filter Compliance by Plaza:", ["All", "TP01", "TP02", "TP03"], key="comp_plz_filter")
        filtered_comp = comp_df.copy()
        if f_comp_plz != "All":
            filtered_comp = filtered_comp[filtered_comp["Plaza"] == f_comp_plz]

        st.dataframe(filtered_comp, width="stretch", hide_index=True)

        st.divider()

        st.subheader("📢 Supervisor Escalation & Reminder Portal")
        c_esc1, c_esc2 = st.columns(2)
        with c_esc1:
            target_supervisor = st.selectbox(
                "Select Supervisor to Notify / Remind:",
                comp_df["Supervisor Name"].tolist(),
                index=comp_df["Supervisor Name"].tolist().index("Sanjeev Sahu") if "Sanjeev Sahu" in comp_df["Supervisor Name"].tolist() else 0,
            )
            reminder_text = st.text_input(
                "Notification Message:",
                value=f"Urgent: Mandatory energy consumption log review overdue at {f_comp_plz if f_comp_plz != 'All' else 'TP03'}. Complete telemetry verification immediately.",
            )
        with c_esc2:
            st.markdown("#### Actions")
            if st.button("📨 Send Direct SMS / Email Reminder", type="primary", width="stretch"):
                st.success(f"✓ Notification dispatched to {target_supervisor} and CC'd to Plaza Manager.")
            if st.button("📝 Log Inactivity Incident in Audit Trail", width="stretch"):
                st.warning(f"Incident recorded: {target_supervisor} logged for compliance SLA review.")


if __name__ == "__main__":
    render()
