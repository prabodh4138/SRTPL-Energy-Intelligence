import streamlit as st
from core.services import EnergyService

def render():
    st.title("JUNO CSV Import")
    st.caption("Upload the original JUNO CSV. The file is never edited or stripped by the application.")
    uploaded = st.file_uploader("Upload JUNO CSV", type=["csv"])
    if uploaded:
        st.write({"filename": uploaded.name, "size_bytes": uploaded.size})
        if st.button("Start Import", type="primary"):
            result = EnergyService().import_juno_csv(uploaded)
            st.info(result.message)
            st.json({
                "status": result.status,
                "report_type": result.report_type,
                "rows_received": result.rows_received
            })
