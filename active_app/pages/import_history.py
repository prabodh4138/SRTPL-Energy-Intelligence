import streamlit as st
from import_center.history import ImportHistoryRepository

def render():
    st.title("JUNO Import History")
    repo = ImportHistoryRepository()
    df = repo.list_recent()
    if df.empty:
        st.info("No production import batches are available yet.")
    else:
        st.dataframe(df, width="stretch", hide_index=True)
