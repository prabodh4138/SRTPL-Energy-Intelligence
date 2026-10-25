import streamlit as st
from datetime import date, timedelta
from equipment.services import EquipmentDashboardService
from equipment.components import (
    render_kpis, render_latest, render_parameters,
    render_trend, render_exceptions, render_traceability
)

def render():
    st.title("Equipment Dashboard")
    st.caption("Detailed asset-level energy and electrical analytics")

    service = EquipmentDashboardService()

    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c1:
        source_type = st.selectbox("Equipment Type", service.available_types())
    with c2:
        assets = service.available_assets(source_type)
        asset = st.selectbox("Asset", assets) if assets else None
    with c3:
        from_date = st.date_input("From", date.today() - timedelta(days=30))
        to_date = st.date_input("To", date.today())

    if not asset:
        st.info("No configured asset is available for this equipment type.")
        return

    if from_date > to_date:
        st.error("From date cannot be after To date.")
        return

    data = service.get_dashboard(source_type, asset, from_date, to_date)

    st.subheader(f"{data.asset_name} • {data.plaza}")
    render_kpis(data.kpis)

    st.divider()
    render_latest(data.latest)

    st.divider()
    render_parameters(data.parameters)

    st.divider()
    render_trend(data.trend)

    st.divider()
    render_exceptions(data.exceptions)

    st.divider()
    render_traceability(data.traceability if hasattr(data, "traceability") else None)
