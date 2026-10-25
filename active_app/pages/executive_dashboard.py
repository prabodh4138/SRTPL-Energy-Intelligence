import streamlit as st
from datetime import date, timedelta
from dashboard.services import DashboardService
from dashboard.components import (
    metric_row, energy_mix, trend_chart, plaza_table,
    exception_panel, data_quality_panel
)
from core.demo_store import (
    get_demo_bills,
    get_demo_operator_tracking,
    get_demo_plaza_monitoring_compliance,
)
from ui.navigation import navigate_to


def render():
    st.markdown('<div class="eyebrow">SRTPL / ENERGY INTELLIGENCE</div>', unsafe_allow_html=True)
    st.title("Executive Overview")
    st.caption("Energy performance, data reliability and financial control across three toll plazas (TP01, TP02, TP03)")

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        from_date = st.date_input("From", date.today() - timedelta(days=30), key="exec_from")
    with c2:
        to_date = st.date_input("To", date.today(), key="exec_to")
    with c3:
        plaza = st.multiselect("Plaza Filter", ["TP01", "TP02", "TP03"], default=["TP01", "TP02", "TP03"], key="exec_plz")

    if from_date > to_date:
        st.error("From date cannot be after To date.")
        return

    service = DashboardService()
    summary = service.executive_summary(from_date, to_date, plaza)

    st.markdown('<div class="eyebrow" style="margin-top:14px;">ENERGY SNAPSHOT · TELEMETRY TOTALS</div>', unsafe_allow_html=True)
    metric_row(summary)

    st.divider()

    # 1. Energy Trend & Plaza Comparison
    g1, g2 = st.columns([1.3, 1])
    with g1:
        st.subheader("Energy Trend · Last 30 Days")
        st.caption("Combined daily energy activity across EB, DG, and Solar")
        trend_chart(summary)
    with g2:
        st.subheader("Energy Mix & Data Reliability")
        energy_mix(summary)
        st.divider()
        data_quality_panel(summary)

    st.divider()

    st.subheader("Toll Plaza Operational Comparison")
    st.caption("Relative performance, energy consumption, and exception tally by toll plaza.")
    plaza_table(summary)

    st.divider()

    # 2. Interconnected Intelligence Modules matching HTML Prototype
    st.markdown('<div class="eyebrow">INTERCONNECTED OPERATIONAL INTELLIGENCE</div>', unsafe_allow_html=True)
    st.subheader("Actionable Controls & Exception Queues")

    grid_left, grid_right = st.columns(2)

    with grid_left:
        with st.container(border=True):
            st.markdown("#### 🚨 Data Quality & Raw Exception Queue")
            exception_panel(summary)
            st.caption("Inspect raw CSV records, pinpoint transcription typos, and correct offending data.")
            if st.button("Open Validation & Exceptions Center →", type="primary", width="stretch", key="exec_btn_val"):
                navigate_to("Validation & Exceptions")

    with grid_right:
        with st.container(border=True):
            st.markdown("#### ▤ Financial Controls (Bills & Receipts)")
            bills = get_demo_bills()
            elec = bills[bills["Type"] == "Electricity Bill"]
            b_tot = float(elec["Amount"].sum())
            p_tot = float(elec["Paid"].sum())
            o_tot = b_tot - p_tot

            f1, f2, f3 = st.columns(3)
            f1.metric("Billed", f"₹{b_tot/100000:.2f}L")
            f2.metric("Paid", f"₹{p_tot/100000:.2f}L")
            f3.metric("Outstanding", f"₹{o_tot/100000:.2f}L")

            st.caption("Month-wise DISCOM electricity bills, automated OCR extraction, and meter reconciliation.")
            if st.button("View Bills & Monthly EB Consumption →", width="stretch", key="exec_btn_bills"):
                navigate_to("Bills & Receipts")

    row2_left, row2_right = st.columns(2)

    with row2_left:
        with st.container(border=True):
            st.markdown("#### 👤 Raw CSV Data Entry Tracking (Who Entered Wrong Data)")
            op_data = get_demo_operator_tracking()
            active_errors = int(op_data["Active Errors"].sum())
            if active_errors > 0:
                st.warning(f"⚠️ **{active_errors} raw data transcription error(s)** logged by shift operators requiring review.")
            else:
                st.success("✓ All raw CSV log entries verified accurate with zero operator errors.")
            st.caption("Identifies the specific operator, shift, and station responsible for each raw data entry.")
            if st.button("Inspect Operator Accountability →", width="stretch", key="exec_btn_op"):
                navigate_to("Operator & Compliance Tracking")

    with row2_right:
        with st.container(border=True):
            st.markdown("#### 📋 Plaza Energy Monitoring Compliance (Who Has Not Monitored)")
            comp_data = get_demo_plaza_monitoring_compliance()
            overdue = comp_data[comp_data["Inspection Status"] == "MISSED / OVERDUE"]
            if not overdue.empty:
                st.error(f"🚨 **1 Critical Inactivity Alert:** {overdue.iloc[0]['Supervisor Name']} ({overdue.iloc[0]['Plaza']}) has **NOT monitored energy in over 28 hrs**!")
            else:
                st.success("✓ 100% of shift supervisors have completed daily energy consumption reviews.")
            st.caption("Tracks daily telemetry checklists and alerts if a supervisor misses mandatory inspections.")
            if st.button("Open Plaza Compliance Tracker →", width="stretch", key="exec_btn_comp"):
                navigate_to("Operator & Compliance Tracking")


if __name__ == "__main__":
    render()
