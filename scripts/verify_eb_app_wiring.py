from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "active_app"

checks = [
    APP / "pages" / "eb_juno_import.py",
    APP / "analytics" / "eb_phase5_4.py",
    ROOT / "scripts" / "verify_eb_phase5_4.py",
]
for path in checks:
    assert path.exists(), path

app_text = (APP / "app.py").read_text(encoding="utf-8")
nav_text = (APP / "ui" / "navigation.py").read_text(encoding="utf-8")
assert "EB JUNO Import" in app_text
assert "EB JUNO Import" in nav_text
assert "from pages.eb_juno_import import render" in app_text
assert "ImportPipeline" in (APP / "pages" / "eb_juno_import.py").read_text(encoding="utf-8")
assert "NormalizationPersistence" in (APP / "pages" / "eb_juno_import.py").read_text(encoding="utf-8")
assert "calculate_eb_kpis" in (APP / "pages" / "eb_juno_import.py").read_text(encoding="utf-8")
print("EB APPLICATION WIRING: PASS")
