from __future__ import annotations

import streamlit as st

PAGES = [
    "Executive Dashboard",
    "Plaza Dashboard",
    "Equipment Dashboard",
    "Bills & Receipts",
    "Operator & Compliance Tracking",
    "EB JUNO Import",
    "DG JUNO Import",
    "Solar JUNO Import",
    "Transformer JUNO Import",
    "UPS JUNO Import",
    "JUNO Import Center",
    "EB",
    "DG",
    "Solar",
    "Transformer",
    "UPS",
    "Import History",
    "Validation & Exceptions",
    "Data Quality",
    "Reports",
    "Audit",
    "Master Data",
    "Administration",
    "System Health",
]


def navigate_to(page_name: str):
    """Safely triggers programmatic navigation without mutating widget session state post-instantiation."""
    if page_name in PAGES:
        st.session_state["pending_nav_page"] = page_name
        st.session_state["nav_page"] = page_name
        st.rerun()


def render_navigation():
    # Process any pending programmatic navigation BEFORE creating the radio widget
    pending = st.session_state.pop("pending_nav_page", None)
    if pending and pending in PAGES:
        st.session_state["nav_page_selector"] = pending
        st.session_state["nav_page"] = pending

    # Fallback initialization if first run
    if "nav_page" not in st.session_state or st.session_state["nav_page"] not in PAGES:
        st.session_state["nav_page"] = "Executive Dashboard"
    if "nav_page_selector" not in st.session_state or st.session_state["nav_page_selector"] not in PAGES:
        st.session_state["nav_page_selector"] = st.session_state["nav_page"]

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
    if st.sidebar.button("🏠 Home (Executive Overview)", width="stretch"):
        navigate_to("Executive Dashboard")

    st.sidebar.divider()

    current_page = st.session_state.get("nav_page", "Executive Dashboard")
    current_idx = PAGES.index(current_page) if current_page in PAGES else 0

    if "nav_page_selector" not in st.session_state:
        selected_page = st.sidebar.radio(
            "Navigation Workspace",
            PAGES,
            index=current_idx,
            key="nav_page_selector",
        )
    else:
        selected_page = st.sidebar.radio(
            "Navigation Workspace",
            PAGES,
            key="nav_page_selector",
        )
    st.session_state["nav_page"] = selected_page

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

    return selected_page
