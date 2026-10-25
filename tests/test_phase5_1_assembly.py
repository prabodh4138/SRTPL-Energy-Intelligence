from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_master_entrypoint_exists():
    assert (ROOT / "streamlit_app.py").exists()
    assert (ROOT / "app" / "app.py").exists()

def test_install_manifest_exists():
    assert (ROOT / "sql" / "master_install" / "INSTALL_ORDER.sql").exists()

def test_legacy_phases_preserved():
    assert (ROOT / "legacy_phases").exists()

def test_env_template_exists():
    assert (ROOT / ".env.example").exists()
