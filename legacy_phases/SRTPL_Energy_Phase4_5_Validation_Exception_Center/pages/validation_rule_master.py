import streamlit as st
from exception_center.rules import RULES

def render():
    st.title("Validation Rule Master")
    st.caption("Reference catalogue for source-specific validation rules.")

    source = st.selectbox("Source", list(RULES))
    rows = [
        {"Rule Code": code, "Description": desc, "Severity": severity}
        for code, desc, severity in RULES[source]
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.info("Production rule thresholds remain database-configurable; this catalogue is not a substitute for the DB rule master.")
