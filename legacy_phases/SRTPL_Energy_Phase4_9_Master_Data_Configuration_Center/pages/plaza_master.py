import streamlit as st
from master_data.repository import MasterDataRepository

def render():
    st.title("Plaza Master")
    df = MasterDataRepository().plazas()
    if df.empty:
        st.info("No production plazas configured.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
