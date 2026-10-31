import sys
from pathlib import Path
import streamlit as st
from core.config import settings
from core.auth import AuthService
from ui.navigation import render_navigation, resolve_page, navigate_to
from ui.styles import load_styles
from ui.modules import (
    render_dashboard_module,
    render_reading_module,
    render_validation_module,
    render_juno_import_module,
    render_bill_reconciliation_module,
    render_reports_module,
)


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
        if page == "1. Dashboard":
            render_dashboard_module()
        elif page == "2. Reading Section":
            render_reading_module()
        elif page == "3. Validation and Exceptions":
            render_validation_module()
        elif page == "4. Juno Import Centre":
            render_juno_import_module()
        elif page == "5. Bill Reconcilation":
            render_bill_reconciliation_module()
        elif page == "6. Reports":
            render_reports_module()
        elif page == "Master Data Center":
            from pages.master_data_center import render
            render()
        elif page == "Administration Center":
            from pages.admin_center import render
            render()
        elif page == "System Health":
            from pages.system_health import render
            render()
        else:
            # Fallback resolver for any programmatic navigation alias
            target, sub_key, sub_val = resolve_page(page)
            if sub_key and sub_val:
                st.session_state[sub_key] = sub_val
            if target == "1. Dashboard":
                render_dashboard_module()
            elif target == "2. Reading Section":
                render_reading_module()
            elif target == "3. Validation and Exceptions":
                render_validation_module()
            elif target == "4. Juno Import Centre":
                render_juno_import_module()
            elif target == "5. Bill Reconcilation":
                render_bill_reconciliation_module()
            elif target == "6. Reports":
                render_reports_module()
            elif target == "Master Data Center":
                from pages.master_data_center import render
                render()
            elif target == "Administration Center":
                from pages.admin_center import render
                render()
            elif target == "System Health":
                from pages.system_health import render
                render()
            else:
                render_dashboard_module()
    except Exception as exc:
        st.error(f"An error occurred on the '{page}' view: {exc}")
        if st.button("Return to Dashboard", width="stretch"):
            navigate_to("1. Dashboard")


app = "SRTPL Energy Intelligence"

if __name__ == "__main__":
    run_app()
