import streamlit as st
def render():
    st.title("Audit Trail")
    st.write("Import → validation → normalized reading → KPI → report traceability.")
    st.info("Production audit records will be read from energy_audit tables.")
