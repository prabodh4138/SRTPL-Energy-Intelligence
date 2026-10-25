import streamlit as st

def render():
    st.title("Integration Status")
    st.caption("Master application integration overview.")

    stages = [
        ("JUNO Import", "Phase 4.4"),
        ("Validation & Exceptions", "Phase 4.5"),
        ("Data Quality", "Phase 4.6"),
        ("Reports & Export", "Phase 4.7"),
        ("Audit & Administration", "Phase 4.8"),
        ("Master Data & Configuration", "Phase 4.9"),
    ]

    for name, phase in stages:
        st.write(f"**{name}** — {phase} — Integration adapter required")
