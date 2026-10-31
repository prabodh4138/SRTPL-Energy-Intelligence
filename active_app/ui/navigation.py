from __future__ import annotations

import streamlit as st

PRIMARY_MODULES = [
    "1. Dashboard",
    "2. Reading Section",
    "3. Validation and Exceptions",
    "4. Juno Import Centre",
    "5. Bill Reconcilation",
    "6. Reports",
]

MODULE_DISPLAY_NAMES = {
    "1. Dashboard": "1. Dashboard",
    "2. Reading Section": "2. Reading Section (DG, EB, SOLAR, TRANSFORMER and UPS)",
    "3. Validation and Exceptions": "3. Validation and Exceptions",
    "4. Juno Import Centre": "4. Juno Import Centre (DG, EB, SOLAR, TRANSFORMER and UPS)",
    "5. Bill Reconcilation": "5. Bill Reconcilation (EB Bill Extraction field, and many More)",
    "6. Reports": "6. Reports (Excel, CSV and Pdf)",
}

ADMIN_PAGES = [
    "Master Data Center",
    "Administration Center",
    "System Health",
]

NAVIGATION_MAP: dict[str, tuple[str, str | None, str | None]] = {
    # 1. Dashboard
    "1. Dashboard": ("1. Dashboard", None, None),
    "Dashboard": ("1. Dashboard", None, None),
    "Executive Dashboard": ("1. Dashboard", "dashboard_subtab", "Executive Overview"),
    "Executive Overview": ("1. Dashboard", "dashboard_subtab", "Executive Overview"),
    "Plaza Dashboard": ("1. Dashboard", "dashboard_subtab", "Plaza Dashboard"),
    "Equipment Dashboard": ("1. Dashboard", "dashboard_subtab", "Equipment Dashboard"),
    "Operator & Compliance Tracking": ("1. Dashboard", "dashboard_subtab", "Operator & Compliance"),
    "Operator & Compliance": ("1. Dashboard", "dashboard_subtab", "Operator & Compliance"),

    # 2. Reading Section
    "2. Reading Section": ("2. Reading Section", None, None),
    "Reading Section": ("2. Reading Section", None, None),
    "2. Reading Section(DG,EB,SOLAR,TRANSFORMER and UPS)": ("2. Reading Section", None, None),
    "EB": ("2. Reading Section", "reading_subtab", "⚡ EB Reading"),
    "DG": ("2. Reading Section", "reading_subtab", "⚡ DG Reading"),
    "Solar": ("2. Reading Section", "reading_subtab", "☀️ Solar Reading"),
    "Transformer": ("2. Reading Section", "reading_subtab", "🔌 Transformer Reading"),
    "UPS": ("2. Reading Section", "reading_subtab", "🔋 UPS Reading"),

    # 3. Validation and Exceptions
    "3. Validation and Exceptions": ("3. Validation and Exceptions", None, None),
    "Validation and Exceptions": ("3. Validation and Exceptions", None, None),
    "3. Validation & Exceptions": ("3. Validation and Exceptions", None, None),
    "Validation & Exceptions": ("3. Validation and Exceptions", "validation_subtab", "🚨 Validation & Exceptions Center"),
    "Data Quality": ("3. Validation and Exceptions", "validation_subtab", "📊 Data Quality Monitor"),

    # 4. Juno Import Centre
    "4. Juno Import Centre": ("4. Juno Import Centre", None, None),
    "Juno Import Centre": ("4. Juno Import Centre", None, None),
    "4. Juno Import Centre(DG,EB,SOLAR,TRANSFORMER and UPS)": ("4. Juno Import Centre", None, None),
    "JUNO Import Center": ("4. Juno Import Centre", "juno_import_subtab", "📁 Bulk Import Center"),
    "EB JUNO Import": ("4. Juno Import Centre", "juno_import_subtab", "⚡ EB JUNO Import"),
    "DG JUNO Import": ("4. Juno Import Centre", "juno_import_subtab", "⚡ DG JUNO Import"),
    "Solar JUNO Import": ("4. Juno Import Centre", "juno_import_subtab", "☀️ Solar JUNO Import"),
    "Transformer JUNO Import": ("4. Juno Import Centre", "juno_import_subtab", "🔌 Transformer JUNO Import"),
    "UPS JUNO Import": ("4. Juno Import Centre", "juno_import_subtab", "🔋 UPS JUNO Import"),
    "Import History": ("4. Juno Import Centre", "juno_import_subtab", "📜 Import History"),

    # 5. Bill Reconcilation
    "5. Bill Reconcilation": ("5. Bill Reconcilation", None, None),
    "Bill Reconcilation": ("5. Bill Reconcilation", None, None),
    "5. Bill Reconcilation(EB Bill Extraction field,and many More)": ("5. Bill Reconcilation", None, None),
    "Bills & Receipts": ("5. Bill Reconcilation", None, None),

    # 6. Reports
    "6. Reports": ("6. Reports", "reports_subtab", "📑 Reports & Export Center"),
    "Reports": ("6. Reports", "reports_subtab", "📑 Reports & Export Center"),
    "6. Reports(Excel,CSV and Pdf)": ("6. Reports", "reports_subtab", "📑 Reports & Export Center"),
    "Audit": ("6. Reports", "reports_subtab", "📜 Audit Log & System Trail"),

    # Administrative Workspaces
    "Master Data": ("Master Data Center", None, None),
    "Master Data Center": ("Master Data Center", None, None),
    "Administration": ("Administration Center", None, None),
    "Administration Center": ("Administration Center", None, None),
    "System Health": ("System Health", None, None),
}

PAGES = list(dict.fromkeys(PRIMARY_MODULES + ADMIN_PAGES + list(NAVIGATION_MAP.keys())))


def resolve_page(page_name: str) -> tuple[str, str | None, str | None]:
    """Resolves any module or legacy page name to (target_page, subtab_key, subtab_val)."""
    return NAVIGATION_MAP.get(page_name, (page_name, None, None))


def navigate_to(page_name: str) -> None:
    """Safely triggers programmatic navigation without mutating widget session state post-instantiation."""
    target_page, subtab_key, subtab_val = resolve_page(page_name)
    if subtab_key and subtab_val:
        st.session_state[subtab_key] = subtab_val
    st.session_state["pending_nav_page"] = target_page
    st.session_state["nav_page"] = target_page
    if target_page in PRIMARY_MODULES:
        st.session_state["primary_module_radio"] = target_page
    st.rerun()


def render_navigation() -> str:
    # Process any pending programmatic navigation BEFORE creating the radio widget
    pending = st.session_state.pop("pending_nav_page", None)
    if pending:
        target_page, subtab_key, subtab_val = resolve_page(pending)
        if subtab_key and subtab_val:
            st.session_state[subtab_key] = subtab_val
        st.session_state["nav_page"] = target_page
        if target_page in PRIMARY_MODULES:
            st.session_state["primary_module_radio"] = target_page

    # Fallback initialization if first run
    if "nav_page" not in st.session_state or st.session_state["nav_page"] not in PAGES:
        st.session_state["nav_page"] = "1. Dashboard"

    current_page = st.session_state["nav_page"]

    # If it's a legacy alias, map it to the primary module or admin page
    if current_page not in PRIMARY_MODULES and current_page not in ADMIN_PAGES:
        target_page, subtab_key, subtab_val = resolve_page(current_page)
        if subtab_key and subtab_val:
            st.session_state[subtab_key] = subtab_val
        current_page = target_page
        st.session_state["nav_page"] = current_page
        if target_page in PRIMARY_MODULES:
            st.session_state["primary_module_radio"] = target_page

    st.sidebar.markdown(
        """
        <div style="display:flex;gap:10px;align-items:center;margin-bottom:12px;">
            <div style="width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,#0ea5b7,#1d4267);display:grid;place-items:center;font-size:20px;font-weight:bold;color:#e6edf7;">⚡</div>
            <div><b style="color:#e6edf7;font-size:15px;">SRTPL ENERGY</b><br><small style="color:#91a5bd;font-size:11px;">Intelligence Platform</small></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.caption(f"Signed in as: **{st.session_state.get('user', 'admin@srtpl.com')}**")

    # Quick Home Button
    if st.sidebar.button("🏠 Home (Dashboard)", width="stretch"):
        navigate_to("1. Dashboard")

    st.sidebar.divider()

    if current_page in ADMIN_PAGES:
        st.sidebar.info(f"Viewing: **{current_page}**")
        if st.sidebar.button("← Return to Core Modules", width="stretch", type="primary"):
            navigate_to("1. Dashboard")
        st.sidebar.divider()

    if "primary_module_radio" not in st.session_state or st.session_state["primary_module_radio"] not in PRIMARY_MODULES:
        st.session_state["primary_module_radio"] = current_page if current_page in PRIMARY_MODULES else "1. Dashboard"

    if current_page in PRIMARY_MODULES and st.session_state.get("primary_module_radio") != current_page:
        st.session_state["primary_module_radio"] = current_page

    selected_module = st.sidebar.radio(
        "Application Modules",
        PRIMARY_MODULES,
        format_func=lambda m: MODULE_DISPLAY_NAMES.get(m, m),
        key="primary_module_radio",
    )

    # Only update nav_page from primary radio if user is not in an admin view or if user switched radio
    if current_page not in ADMIN_PAGES:
        current_page = selected_module
        st.session_state["nav_page"] = selected_module
    elif selected_module != st.session_state.get("_last_admin_selected_module", None):
        # User explicitly clicked radio while in admin mode -> switch to that module
        current_page = selected_module
        st.session_state["nav_page"] = selected_module

    st.session_state["_last_admin_selected_module"] = selected_module

    # Secondary Expandable Drawer for Master Data & Administration
    with st.sidebar.expander("⚙️ Master Data & Administration", expanded=(current_page in ADMIN_PAGES)):
        st.caption("Administrative & Master Configuration")
        if st.button("📁 Master Data Center", width="stretch", key="nav_btn_md"):
            navigate_to("Master Data Center")
        if st.button("👥 Administration Center", width="stretch", key="nav_btn_adm"):
            navigate_to("Administration Center")
        if st.button("🩺 System Health", width="stretch", key="nav_btn_sh"):
            navigate_to("System Health")

    st.sidebar.divider()

    # Multi-device link helper
    try:
        from core.supabase_manager import get_network_info
        net = get_network_info()
        st.sidebar.markdown(
            f"""
            <div style="background:rgba(14,165,183,0.08);border:1px solid rgba(14,165,183,0.3);border-radius:8px;padding:8px;margin-bottom:8px;">
                <span style="font-size:11px;font-weight:600;color:#0ea5b7;">📱 MOBILE / LAPTOP ACCESS</span><br>
                <code style="font-size:12px;color:#e2e8f0;word-break:break-all;">{net['network_url']}</code>
            </div>
            """,
            unsafe_allow_html=True,
        )
    except Exception:
        pass

    # Demo Data Toggle Banner
    demo_active = st.session_state.get("demo_mode_active", False)
    if demo_active:
        st.sidebar.success("🟢 Demo Data Active (Preloaded Samples)")
        if st.sidebar.button("🗑️ Clear Demo Data (Switch to Live)", width="stretch"):
            from core.supabase_manager import remove_all_database_data
            remove_all_database_data()
            st.session_state["demo_mode_active"] = False
            st.rerun()
    else:
        st.sidebar.warning("⚪ Live Database Mode (Production)")
        col_wipe, col_demo = st.sidebar.columns(2)
        with col_wipe:
            if st.button("🗑️ Wipe All", width="stretch", help="Wipes all operational telemetry and resets to empty"):
                from core.supabase_manager import remove_all_database_data
                remove_all_database_data()
                st.session_state["demo_mode_active"] = False
                st.rerun()
        with col_demo:
            if st.button("🔄 Samples", width="stretch", help="Load sample demonstration data"):
                st.session_state["demo_mode_active"] = True
                st.rerun()

    st.sidebar.divider()
    if st.sidebar.button("🚪 Logout", width="stretch"):
        st.session_state.clear()
        st.rerun()

    return current_page
