import os
print("SRTPL Energy application configuration check")
for key in ["SUPABASE_URL","SUPABASE_KEY","ADMIN_EMAIL","ADMIN_TOKEN"]:
    print(f"{key}: {'SET' if os.getenv(key) else 'MISSING'}")
