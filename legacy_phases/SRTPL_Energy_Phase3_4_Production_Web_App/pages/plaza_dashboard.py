import streamlit as st
def render():
    st.title("Plaza Dashboard")
    plaza = st.selectbox("Plaza", ["TP01", "TP02", "TP03"])
    st.info(f"{plaza} dashboard placeholder. KPI drill-down will be connected during final integration.")
