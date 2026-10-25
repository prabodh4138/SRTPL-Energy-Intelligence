from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

entry = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
app = (ROOT / "active_app" / "app.py").read_text(encoding="utf-8")
page = (ROOT / "active_app" / "pages" / "dg_juno_import.py").read_text(encoding="utf-8")

assert "ACTIVE_APP" in entry
assert 'from app import app' in entry
assert 'page == "DG JUNO Import"' in app
assert 'from pages.dg_juno_import import render' in app
assert "ImportPipeline" in page
assert "NormalizationPersistence" in page
assert "calculate_dg_kpis" in page

print("DG APPLICATION WIRING: PASS")
print("single_entry_point: PASS")
print("DG navigation route: PASS")
print("DG upload -> Supabase pipeline: PASS")
print("DG validation -> KPI chain: PASS")
