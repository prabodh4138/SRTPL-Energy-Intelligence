import streamlit as st
from admin.repository import AdminRepository

def render():
    st.title("Audit Log")
    df = AdminRepository().audit_log()
    if df.empty:
        st.info("No production audit records.")
    else:
        st.dataframe(df, width="stretch", hide_index=True)
