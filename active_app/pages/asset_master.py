import streamlit as st
from master_data.repository import MasterDataRepository

def render():
    st.title("Asset / Equipment Master")
    df = MasterDataRepository().assets()
    if df.empty:
        st.info("No production assets configured.")
    else:
        st.dataframe(df, width="stretch", hide_index=True)
