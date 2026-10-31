import pytest
from unittest.mock import patch, MagicMock
import streamlit as st
from ui.navigation import (
    PRIMARY_MODULES,
    MODULE_DISPLAY_NAMES,
    ADMIN_PAGES,
    NAVIGATION_MAP,
    resolve_page,
    navigate_to,
    render_navigation,
)
from ui.modules import (
    render_dashboard_module,
    render_reading_module,
    render_validation_module,
    render_juno_import_module,
    render_bill_reconciliation_module,
    render_reports_module,
)


@pytest.fixture(autouse=True)
def clean_session_state():
    st.session_state.clear()
    yield
    st.session_state.clear()


def test_primary_modules_defined():
    assert len(PRIMARY_MODULES) == 6
    assert PRIMARY_MODULES == [
        "1. Dashboard",
        "2. Reading Section",
        "3. Validation and Exceptions",
        "4. Juno Import Centre",
        "5. Bill Reconcilation",
        "6. Reports",
    ]
    for mod in PRIMARY_MODULES:
        assert mod in MODULE_DISPLAY_NAMES


def test_navigation_mapping_resolution():
    # Module 1 mappings
    target, sub_key, sub_val = resolve_page("Executive Dashboard")
    assert target == "1. Dashboard"
    assert sub_key == "dashboard_subtab"
    assert sub_val == "Executive Overview"

    # Module 2 mappings
    target, sub_key, sub_val = resolve_page("EB")
    assert target == "2. Reading Section"
    assert sub_key == "reading_subtab"
    assert sub_val == "⚡ EB Reading"

    target, sub_key, sub_val = resolve_page("DG")
    assert target == "2. Reading Section"
    assert sub_val == "⚡ DG Reading"

    target, sub_key, sub_val = resolve_page("Solar")
    assert target == "2. Reading Section"
    assert sub_val == "☀️ Solar Reading"

    target, sub_key, sub_val = resolve_page("Transformer")
    assert target == "2. Reading Section"
    assert sub_val == "🔌 Transformer Reading"

    target, sub_key, sub_val = resolve_page("UPS")
    assert target == "2. Reading Section"
    assert sub_val == "🔋 UPS Reading"

    # Module 3 mappings
    target, sub_key, sub_val = resolve_page("Validation & Exceptions")
    assert target == "3. Validation and Exceptions"
    assert sub_key == "validation_subtab"
    assert sub_val == "🚨 Validation & Exceptions Center"

    # Module 4 mappings
    target, sub_key, sub_val = resolve_page("EB JUNO Import")
    assert target == "4. Juno Import Centre"
    assert sub_key == "juno_import_subtab"
    assert sub_val == "⚡ EB JUNO Import"

    # Module 5 mappings
    target, sub_key, sub_val = resolve_page("Bills & Receipts")
    assert target == "5. Bill Reconcilation"

    target, sub_key, sub_val = resolve_page("Bill Reconcilation")
    assert target == "5. Bill Reconcilation"

    # Module 6 mappings
    target, sub_key, sub_val = resolve_page("Reports")
    assert target == "6. Reports"
    assert sub_key == "reports_subtab"
    assert sub_val == "📑 Reports & Export Center"


def test_navigate_to_behavior():
    with patch("streamlit.rerun") as mock_rerun:
        navigate_to("EB")
        assert st.session_state["nav_page"] == "2. Reading Section"
        assert st.session_state["reading_subtab"] == "⚡ EB Reading"
        assert st.session_state["pending_nav_page"] == "2. Reading Section"
        mock_rerun.assert_called_once()


def test_radio_selection_persistence_no_revert():
    """Verify that when a user selects module 2, 3, 4, 5, or 6, it NEVER reverts to module 1."""
    for mod in PRIMARY_MODULES:
        st.session_state["nav_page"] = mod
        with patch("streamlit.sidebar.radio", return_value=mod):
            active_page = render_navigation()
            assert active_page == mod, f"Expected {mod} to remain active, but got {active_page}"


def test_render_reading_module_dispatch():
    with patch("streamlit.segmented_control", return_value="⚡ EB Reading") as mock_sc:
        with patch("pages.eb.render") as mock_eb_render:
            render_reading_module()
            mock_eb_render.assert_called_once()


def test_render_validation_module_dispatch():
    with patch("streamlit.segmented_control", return_value="🚨 Validation & Exceptions Center"):
        with patch("pages.validation_exception_center.render") as mock_val_render:
            render_validation_module()
            mock_val_render.assert_called_once()


def test_render_juno_import_module_dispatch():
    with patch("streamlit.segmented_control", return_value="⚡ DG JUNO Import"):
        with patch("pages.dg_juno_import.render") as mock_dg_render:
            render_juno_import_module()
            mock_dg_render.assert_called_once()


def test_render_reports_module_dispatch():
    with patch("streamlit.segmented_control", return_value="📑 Reports & Export Center"):
        with patch("pages.reports_export_center.render") as mock_rep_render:
            render_reports_module()
            mock_rep_render.assert_called_once()
