import streamlit as st

PAGES = [
    "Executive Dashboard", "Plaza Dashboard", "JUNO CSV Import",
    "Import History", "Validation & Exceptions",
    "Solar", "DG", "EB", "Transformer", "UPS",
    "Reports", "Audit", "Master Data", "Administration", "System Health"
]

def render_navigation():
    st.sidebar.title("⚡ SRTPL Energy")
    st.sidebar.caption(f"User: {st.session_state.get('user','-')}")
    page = st.sidebar.radio("Navigation", PAGES)
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
    return page
