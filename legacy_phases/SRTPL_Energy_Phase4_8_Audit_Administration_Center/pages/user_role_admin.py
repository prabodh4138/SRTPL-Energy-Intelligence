import streamlit as st
from admin.repository import AdminRepository

def render():
    st.title("User & Role Administration")
    st.caption("RBAC administration foundation.")
    df = AdminRepository().users()
    if df.empty:
        st.info("No production users are available.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
