from dataclasses import dataclass

@dataclass
class StartupCheck:
    name: str
    status: str
    message: str

def run_startup_checks(settings):
    checks = []

    checks.append(StartupCheck(
        "ENVIRONMENT",
        "PASS" if settings.get("environment") else "FAIL",
        "Application environment configured."
        if settings.get("environment") else "Missing environment."
    ))

    checks.append(StartupCheck(
        "SUPABASE_URL",
        "PASS" if settings.get("supabase_url") else "FAIL",
        "Supabase URL configured."
        if settings.get("supabase_url") else "Supabase URL missing."
    ))

    checks.append(StartupCheck(
        "SUPABASE_KEY",
        "PASS" if settings.get("supabase_key") else "FAIL",
        "Server-side Supabase credential available."
        if settings.get("supabase_key") else "Supabase credential missing."
    ))

    checks.append(StartupCheck(
        "STORAGE_BUCKET",
        "PASS" if settings.get("storage_bucket") else "FAIL",
        "Original-file storage configured."
        if settings.get("storage_bucket") else "Storage bucket missing."
    ))

    return checks
