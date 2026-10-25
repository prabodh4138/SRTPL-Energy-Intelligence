"""SRTPL Energy Intelligence — Phase 5.1 master entry point.

This is the single browser-facing Streamlit entry point for the assembled project.
It deliberately uses configuration/service discovery instead of embedding business
rules or production credentials in the UI.
"""
from __future__ import annotations

import importlib
import os
from pathlib import Path

import streamlit as st

APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(APP_ROOT))

st.set_page_config(
    page_title="SRTPL Energy Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("SRTPL Energy Intelligence")
st.caption("Phase 5.1 Master Project Assembly")

pages = {
    "Executive Dashboard": "pages.executive_dashboard",
    "Plaza Dashboard": "pages.plaza_dashboard",
    "Equipment Dashboard": "pages.equipment_dashboard",
    "JUNO Import Center": "pages.juno_import_center",
    "Import History": "pages.import_history",
    "Validation & Exceptions": "pages.validation_exception_center",
    "Data Quality": "pages.data_quality_dashboard",
    "Reports & Export": "pages.reports_export_center",
    "Audit / Administration": "pages.admin_center",
    "Master Data": "pages.master_data_center",
    "Integration Status": "pages.integration_status",
    "System Health": "pages.system_health",
}

choice = st.sidebar.selectbox("Module", list(pages))
st.sidebar.caption("Source: JUNO CSV → validated readings → KPI → dashboard/report")
st.sidebar.divider()

try:
    mod = importlib.import_module(pages[choice])
    render = getattr(mod, "render", None)
    if callable(render):
        render()
    else:
        # Some phase pages expose Streamlit UI directly at import time.
        st.info(f"{choice} loaded. This module does not expose a `render()` function yet.")
except Exception as exc:
    st.error(f"Module could not be loaded: {type(exc).__name__}: {exc}")
    st.caption("Use the Integration Status / System Health modules and logs before production deployment.")
