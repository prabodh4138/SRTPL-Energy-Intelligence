import streamlit as st
from core.config import settings

@st.cache_resource
def get_supabase():
    if not settings.supabase_url or not settings.supabase_key:
        return None
    from supabase import create_client
    return create_client(settings.supabase_url, settings.supabase_key)
