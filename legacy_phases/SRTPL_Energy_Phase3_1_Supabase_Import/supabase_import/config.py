import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_key: str
    storage_bucket: str = "energy-original-files"
    parser_version: str = "0.1.0"

def load_settings() -> Settings:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError(
            "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY "
            "(or SUPABASE_KEY) before database integration."
        )
    return Settings(url, key)
