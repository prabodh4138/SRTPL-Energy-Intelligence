import sys
from pathlib import Path
import streamlit as st
from core.config import settings
from core.auth import AuthService
from ui.navigation import render_navigation
from ui.styles import load_styles


def run_app():
    try:
        st.set_page_config(
            page_title=settings.app_name,
            page_icon="⚡",
            layout="wide",
            initial_sidebar_state="expanded",
        )
    except Exception:
        # Ignore if set_page_config already called in session
        pass

    load_styles()

    # Testing phase: remove password hurdle as explicitly requested by user
    st.session_state.setdefault("authenticated", True)
    st.session_state.setdefault("user", "admin@srtpl.com")
    st.session_state.setdefault("role", "SUPER_ADMIN")
    has_supabase = bool(settings.supabase_url and settings.supabase_key)
    st.session_state.setdefault("demo_mode_active", not has_supabase)

    auth = AuthService()
    if not auth.is_authenticated():
        from pages.login import render
        render(auth)
        st.stop()

    page = render_navigation()
    try:
        if page == "Executive Dashboard":
            from pages.executive_dashboard import render
        elif page == "Plaza Dashboard":
            from pages.plaza_dashboard import render
        elif page == "Equipment Dashboard":
            from pages.equipment_dashboard import render
        elif page == "Bills & Receipts":
            from pages.bills_receipts_center import render
        elif page == "Operator & Compliance Tracking":
            from pages.operator_compliance_center import render
        elif page == "EB JUNO Import":
            from pages.eb_juno_import import render
        elif page == "DG JUNO Import":
            from pages.dg_juno_import import render
        elif page == "Solar JUNO Import":
            from pages.solar_juno_import import render
        elif page == "Transformer JUNO Import":
            from pages.transformer_juno_import import render
        elif page == "UPS JUNO Import":
            from pages.ups_juno_import import render
        elif page == "JUNO Import Center":
            from pages.juno_import_center import render
        elif page == "EB":
            from pages.eb import render
        elif page == "DG":
            from pages.dg import render
        elif page == "Solar":
            from pages.solar import render
        elif page == "Transformer":
            from pages.transformer import render
        elif page == "UPS":
            from pages.ups import render
        elif page == "Import History":
            from pages.import_history import render
        elif page == "Validation & Exceptions":
            from pages.validation_exception_center import render
        elif page == "Data Quality":
            from pages.data_quality_dashboard import render
        elif page == "Reports":
            from pages.reports_export_center import render
        elif page == "Audit":
            from pages.audit_log import render
        elif page == "Master Data":
            from pages.master_data_center import render
        elif page == "Administration":
            from pages.admin_center import render
        elif page == "System Health":
            from pages.system_health import render

        render()
    except Exception as exc:
        st.error(f"An error occurred on the '{page}' view: {exc}")
        if st.button("Return to Executive Dashboard", width="stretch"):
            from ui.navigation import navigate_to
            navigate_to("Executive Dashboard")


app = "SRTPL Energy Intelligence"

if __name__ == "__main__":
    run_app()
