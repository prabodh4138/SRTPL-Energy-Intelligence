import streamlit as st
from datetime import date, timedelta
from dashboard.services import DashboardService
from dashboard.components import (
    metric_row, energy_mix, trend_chart, plaza_table,
    exception_panel, data_quality_panel
)

def render():
    st.title("Executive Energy Dashboard")
    st.caption("SRTPL Power Consumption Analytics • Management Overview")

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        from_date = st.date_input("From", date.today() - timedelta(days=30))
    with c2:
        to_date = st.date_input("To", date.today())
    with c3:
        plaza = st.multiselect("Plaza", ["TP01", "TP02", "TP03"], default=["TP01", "TP02", "TP03"])

    if from_date > to_date:
        st.error("From date cannot be after To date.")
        return

    service = DashboardService()
    summary = service.executive_summary(from_date, to_date, plaza)

    metric_row(summary)

    st.divider()
    left, right = st.columns(2)
    with left:
        energy_mix(summary)
    with right:
        data_quality_panel(summary)

    st.divider()
    st.subheader("Plaza Comparison")
    plaza_table(summary)

    st.divider()
    st.subheader("Energy Trend")
    trend_chart(summary)

    st.divider()
    st.subheader("Exceptions Requiring Attention")
    exception_panel(summary)

    st.divider()
    st.subheader("Drill-down")
    st.info(
        "Select a KPI in the production dashboard to drill from Management → "
        "Plaza → Asset → Parameter → KPI Result → Normalized Reading → "
        "JUNO Raw Record → Original CSV."
    )
