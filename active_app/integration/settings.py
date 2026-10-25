import os

def load_settings():
    return {
        "environment": os.getenv("APP_ENV", "development"),
        "supabase_url": os.getenv("SUPABASE_URL"),
        "supabase_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        "storage_bucket": os.getenv("ENERGY_STORAGE_BUCKET", "energy-original-files"),
    }

def validate_production_settings(settings):
    required = ["supabase_url", "supabase_key", "storage_bucket"]
    missing = [k for k in required if not settings.get(k)]
    if missing:
        raise RuntimeError("Missing production settings: " + ", ".join(missing))
