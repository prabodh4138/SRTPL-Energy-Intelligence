import streamlit as st
def render():
    st.title("Import History")
    st.dataframe([], use_container_width=True)
    st.info("Production view will read energy_import.import_batch/import_file/import_row.")
