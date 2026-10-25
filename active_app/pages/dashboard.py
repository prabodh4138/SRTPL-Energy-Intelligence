import streamlit as st
from core.services import EnergyService

def render():
    st.title("Executive Dashboard")
    st.caption("Management overview — live KPI data will appear after Supabase integration.")
    s = EnergyService().dashboard_summary()
    cols = st.columns(5)
    for col, (name, value) in zip(cols, s.items()):
        col.metric(name, "—")
    st.info("Phase 3.4 application shell is active. Production KPI widgets will consume Phase 3.3 KPI results.")
