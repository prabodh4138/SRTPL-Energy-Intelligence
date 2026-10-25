import streamlit as st
from integration.startup import run_startup_checks
from integration.settings import load_settings

def render():
    st.title("System Health")
    st.caption("Production configuration and dependency checks.")

    settings = load_settings()
    checks = run_startup_checks(settings)

    for check in checks:
        icon = "✅" if check.status == "PASS" else "⛔"
        st.write(f"{icon} **{check.name}** — {check.message}")

    if all(c.status == "PASS" for c in checks):
        st.success("Configured dependencies passed the startup checks.")
    else:
        st.error("One or more required production dependencies are not configured.")
