import streamlit as st
import pandas as pd

def render():
    st.title("Report History")
    st.caption("Audit trail of generated reports.")
    # Production integration: energy_audit.report_run
    df = pd.DataFrame(columns=[
        "Report ID", "Report", "Requested By", "Requested At",
        "Date From", "Date To", "Plaza", "Format", "Rows", "Status"
    ])
    if df.empty:
        st.info("No production report runs are available.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
