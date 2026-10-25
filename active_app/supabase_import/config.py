import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    supabase_url: str = ""
    supabase_key: str = ""
    storage_bucket: str = "energy-original-files"
    parser_version: str = "0.1.0"


def load_settings() -> Settings:
    url = os.getenv("SUPABASE_URL", "").strip()
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.getenv("SUPABASE_KEY", "").strip()
        or os.getenv("SUPABASE_ANON_KEY", "").strip()
    )

    # Check Streamlit Cloud secrets if environment variables are not set
    if not url or not key:
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                if "SUPABASE_URL" in st.secrets:
                    url = str(st.secrets["SUPABASE_URL"]).strip()
                if "SUPABASE_SERVICE_ROLE_KEY" in st.secrets:
                    key = str(st.secrets["SUPABASE_SERVICE_ROLE_KEY"]).strip()
                elif "SUPABASE_KEY" in st.secrets:
                    key = str(st.secrets["SUPABASE_KEY"]).strip()
                elif "SUPABASE_ANON_KEY" in st.secrets:
                    key = str(st.secrets["SUPABASE_ANON_KEY"]).strip()
        except Exception:
            pass

    return Settings(supabase_url=url, supabase_key=key)
