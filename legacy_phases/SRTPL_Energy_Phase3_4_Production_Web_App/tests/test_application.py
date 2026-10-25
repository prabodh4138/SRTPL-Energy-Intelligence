from pathlib import Path

def test_required_application_files_exist():
    required = [
        "app.py",
        "core/config.py",
        "core/auth.py",
        "core/db.py",
        "pages/import_juno.py",
        "pages/dashboard.py",
    ]
    for name in required:
        assert Path(name).exists()
