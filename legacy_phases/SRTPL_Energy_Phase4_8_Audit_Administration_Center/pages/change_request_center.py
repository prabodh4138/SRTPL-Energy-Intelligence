import streamlit as st
from admin.repository import AdminRepository

def render():
    st.title("Change Request Center")
    st.caption("Controlled master-data and configuration changes.")
    df = AdminRepository().change_requests()
    if df.empty:
        st.info("No production change requests.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
