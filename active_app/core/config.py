import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _get_secret(key: str, default: str = "") -> str:
    val = os.getenv(key, "")
    if val:
        return val.strip()
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return default


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "SRTPL Power Consumption Analytics")
    app_env: str = os.getenv("APP_ENV", "development")
    supabase_url: str = _get_secret("SUPABASE_URL")
    supabase_key: str = (
        _get_secret("SUPABASE_SERVICE_ROLE_KEY")
        or _get_secret("SUPABASE_KEY")
        or _get_secret("SUPABASE_ANON_KEY")
    )


settings = Settings()
