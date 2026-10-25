import streamlit as st
from datetime import date, timedelta
from plaza.services import PlazaDashboardService
from plaza.components import (
    render_kpis,
    render_energy_mix,
    render_asset_status,
    render_trends,
    render_exceptions,
    render_quality,
    render_asset_table,
)

def render():
    st.title("Plaza Energy Dashboard")
    st.caption("Operational view by toll plaza")

    service = PlazaDashboardService()
    plazas = service.available_plazas()

    c1, c2, c3 = st.columns([1.2, 1, 1])
    with c1:
        plaza = st.selectbox("Plaza", plazas, index=0 if plazas else None)
    with c2:
        from_date = st.date_input("From", date.today() - timedelta(days=30))
    with c3:
        to_date = st.date_input("To", date.today())

    if not plaza:
        st.warning("No plaza master data is available.")
        return

    if from_date > to_date:
        st.error("From date cannot be after To date.")
        return

    data = service.get_dashboard(plaza, from_date, to_date)

    render_kpis(data)

    st.divider()
    left, right = st.columns(2)
    with left:
        render_energy_mix(data)
    with right:
        render_quality(data)

    st.divider()
    render_asset_status(data)

    st.divider()
    render_trends(data)

    st.divider()
    render_asset_table(data)

    st.divider()
    render_exceptions(data)

    st.divider()
    st.subheader("Operational Drill-down")
    st.info(
        "Plaza → Asset → Parameter → KPI → normalized reading → "
        "JUNO raw record → import row → original CSV."
    )
