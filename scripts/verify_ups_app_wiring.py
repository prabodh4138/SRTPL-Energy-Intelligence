from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
entry = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
app = (ROOT / "active_app" / "app.py").read_text(encoding="utf-8")
page = (ROOT / "active_app" / "pages" / "ups_juno_import.py").read_text(encoding="utf-8")
nav = (ROOT / "active_app" / "ui" / "navigation.py").read_text(encoding="utf-8")

assert "ACTIVE_APP" in entry
assert "from app import app" in entry
assert 'page == "UPS JUNO Import"' in app
assert "UPS JUNO Import" in nav
assert "from pages.ups_juno_import import render" in app
assert "ImportPipeline" in page
assert "NormalizationPersistence" in page
assert "calculate_ups_kpis" in page

print("UPS APPLICATION WIRING: PASS")
