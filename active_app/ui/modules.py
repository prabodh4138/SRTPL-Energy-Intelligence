"""SRTPL Power Intelligence — 6 Consolidated Core Modules.

Visualization modules requested by user:
1. Dashboard (Executive Overview, Plaza Dashboard, Equipment Dashboard, Operator & Compliance)
2. Reading Section (DG, EB, SOLAR, TRANSFORMER and UPS)
3. Validation and Exceptions (Exceptions Center, Data Quality Monitor)
4. Juno Import Centre (DG, EB, SOLAR, TRANSFORMER and UPS, Bulk Import Center, Import History)
5. Bill Reconcilation (EB Bill Extraction field, Review Queue, Receipt Allocation, Missing Bills, and more)
6. Reports (Excel, CSV and Pdf, Audit Log)
"""
from __future__ import annotations

import streamlit as st


def render_dashboard_module() -> None:
    """Module 1: Dashboard suite."""
    st.markdown('<div class="eyebrow">MODULE 1 · DASHBOARD SUITE</div>', unsafe_allow_html=True)
    
    options = [
        "Executive Overview",
        "Plaza Dashboard",
        "Equipment Dashboard",
        "Operator & Compliance",
    ]
    if "dashboard_subtab" not in st.session_state or st.session_state["dashboard_subtab"] not in options:
        st.session_state["dashboard_subtab"] = "Executive Overview"

    selected = st.segmented_control(
        "Dashboard Module Views",
        options=options,
        key="dashboard_subtab",
        label_visibility="collapsed",
    )
    active_tab = selected or st.session_state.get("dashboard_subtab") or "Executive Overview"

    if active_tab == "Executive Overview":
        from pages.executive_dashboard import render
        render()
    elif active_tab == "Plaza Dashboard":
        from pages.plaza_dashboard import render
        render()
    elif active_tab == "Equipment Dashboard":
        from pages.equipment_dashboard import render
        render()
    elif active_tab == "Operator & Compliance":
        from pages.operator_compliance_center import render
        render()


def render_reading_module() -> None:
    """Module 2: Reading Section for DG, EB, Solar, Transformer, and UPS."""
    st.markdown('<div class="eyebrow">MODULE 2 · READING SECTION (DG, EB, SOLAR, TRANSFORMER, UPS)</div>', unsafe_allow_html=True)

    options = [
        "⚡ EB Reading",
        "⚡ DG Reading",
        "☀️ Solar Reading",
        "🔌 Transformer Reading",
        "🔋 UPS Reading",
    ]
    if "reading_subtab" not in st.session_state or st.session_state["reading_subtab"] not in options:
        st.session_state["reading_subtab"] = "⚡ EB Reading"

    selected = st.segmented_control(
        "Equipment Reading Views",
        options=options,
        key="reading_subtab",
        label_visibility="collapsed",
    )
    active_tab = selected or st.session_state.get("reading_subtab") or "⚡ EB Reading"

    if active_tab == "⚡ EB Reading":
        from pages.eb import render
        render()
    elif active_tab == "⚡ DG Reading":
        from pages.dg import render
        render()
    elif active_tab == "☀️ Solar Reading":
        from pages.solar import render
        render()
    elif active_tab == "🔌 Transformer Reading":
        from pages.transformer import render
        render()
    elif active_tab == "🔋 UPS Reading":
        from pages.ups import render
        render()


def render_validation_module() -> None:
    """Module 3: Validation and Exceptions."""
    st.markdown('<div class="eyebrow">MODULE 3 · VALIDATION AND EXCEPTIONS</div>', unsafe_allow_html=True)

    options = [
        "🚨 Validation & Exceptions Center",
        "📊 Data Quality Monitor",
    ]
    if "validation_subtab" not in st.session_state or st.session_state["validation_subtab"] not in options:
        st.session_state["validation_subtab"] = "🚨 Validation & Exceptions Center"

    selected = st.segmented_control(
        "Validation Views",
        options=options,
        key="validation_subtab",
        label_visibility="collapsed",
    )
    active_tab = selected or st.session_state.get("validation_subtab") or "🚨 Validation & Exceptions Center"

    if active_tab == "🚨 Validation & Exceptions Center":
        from pages.validation_exception_center import render
        render()
    elif active_tab == "📊 Data Quality Monitor":
        from pages.data_quality_dashboard import render
        render()


def render_juno_import_module() -> None:
    """Module 4: Juno Import Centre (DG, EB, Solar, Transformer, UPS)."""
    st.markdown('<div class="eyebrow">MODULE 4 · JUNO IMPORT CENTRE (DG, EB, SOLAR, TRANSFORMER, UPS)</div>', unsafe_allow_html=True)

    options = [
        "⚡ EB JUNO Import",
        "⚡ DG JUNO Import",
        "☀️ Solar JUNO Import",
        "🔌 Transformer JUNO Import",
        "🔋 UPS JUNO Import",
        "📁 Bulk Import Center",
        "📜 Import History",
    ]
    if "juno_import_subtab" not in st.session_state or st.session_state["juno_import_subtab"] not in options:
        st.session_state["juno_import_subtab"] = "⚡ EB JUNO Import"

    selected = st.segmented_control(
        "JUNO Ingestion Workspaces",
        options=options,
        key="juno_import_subtab",
        label_visibility="collapsed",
    )
    active_tab = selected or st.session_state.get("juno_import_subtab") or "⚡ EB JUNO Import"

    if active_tab == "⚡ EB JUNO Import":
        from pages.eb_juno_import import render
        render()
    elif active_tab == "⚡ DG JUNO Import":
        from pages.dg_juno_import import render
        render()
    elif active_tab == "☀️ Solar JUNO Import":
        from pages.solar_juno_import import render
        render()
    elif active_tab == "🔌 Transformer JUNO Import":
        from pages.transformer_juno_import import render
        render()
    elif active_tab == "🔋 UPS JUNO Import":
        from pages.ups_juno_import import render
        render()
    elif active_tab == "📁 Bulk Import Center":
        from pages.juno_import_center import render
        render()
    elif active_tab == "📜 Import History":
        from pages.import_history import render
        render()


def render_bill_reconciliation_module() -> None:
    """Module 5: Bill Reconciliation & Energy Accounting."""
    from pages.bills_receipts_center import render
    render()


def render_reports_module() -> None:
    """Module 6: Reports (Excel, CSV and Pdf)."""
    st.markdown('<div class="eyebrow">MODULE 6 · REPORTS (EXCEL, CSV & PDF)</div>', unsafe_allow_html=True)

    options = [
        "📑 Reports & Export Center",
        "📜 Audit Log & System Trail",
    ]
    if "reports_subtab" not in st.session_state or st.session_state["reports_subtab"] not in options:
        st.session_state["reports_subtab"] = "📑 Reports & Export Center"

    selected = st.segmented_control(
        "Reports Views",
        options=options,
        key="reports_subtab",
        label_visibility="collapsed",
    )
    active_tab = selected or st.session_state.get("reports_subtab") or "📑 Reports & Export Center"

    if active_tab == "📑 Reports & Export Center":
        from pages.reports_export_center import render
        render()
    elif active_tab == "📜 Audit Log & System Trail":
        from pages.audit_log import render
        render()
