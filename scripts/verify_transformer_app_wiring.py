from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
entry = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
app = (ROOT / "active_app" / "app.py").read_text(encoding="utf-8")
page = (ROOT / "active_app" / "pages" / "transformer_juno_import.py").read_text(encoding="utf-8")
nav = (ROOT / "active_app" / "ui" / "navigation.py").read_text(encoding="utf-8")

assert "ACTIVE_APP" in entry
assert "from app import app" in entry
assert 'page == "Transformer JUNO Import"' in app
assert "Transformer JUNO Import" in nav
assert "from pages.transformer_juno_import import render" in app
assert "ImportPipeline" in page
assert "NormalizationPersistence" in page
assert "calculate_transformer_kpis" in page

print("TRANSFORMER APPLICATION WIRING: PASS")
