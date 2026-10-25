import streamlit as st
from core.config import settings
from core.db import get_supabase

def render():
    st.title("System Health")
    st.write({"environment": settings.app_env, "supabase_configured": bool(get_supabase())})
    st.caption("Health endpoint is intended for deployment verification.")
