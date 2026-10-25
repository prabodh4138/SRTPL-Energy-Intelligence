import streamlit as st
from core.config import settings
from core.auth import AuthService
from ui.navigation import render_navigation
from ui.styles import load_styles

st.set_page_config(
    page_title=settings.app_name,
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)
load_styles()

auth = AuthService()
if not auth.is_authenticated():
    from pages.login import render
    render(auth)
    st.stop()

page = render_navigation()
if page == "Executive Dashboard":
    from pages.dashboard import render
elif page == "Plaza Dashboard":
    from pages.plaza_dashboard import render
elif page == "JUNO CSV Import":
    from pages.import_juno import render
elif page == "Import History":
    from pages.import_history import render
elif page == "Validation & Exceptions":
    from pages.validation import render
elif page == "Solar":
    from pages.solar import render
elif page == "DG":
    from pages.dg import render
elif page == "EB":
    from pages.eb import render
elif page == "Transformer":
    from pages.transformer import render
elif page == "UPS":
    from pages.ups import render
elif page == "Reports":
    from pages.reports import render
elif page == "Audit":
    from pages.audit import render
elif page == "Master Data":
    from pages.master_data import render
elif page == "Administration":
    from pages.administration import render
elif page == "System Health":
    from pages.health import render
render()
