"""Single browser-facing entry point for the SRTPL Power Analytics master app."""
from pathlib import Path
import sys

APP_ROOT = Path(__file__).resolve().parent
ACTIVE_APP = APP_ROOT / "active_app"
if str(ACTIVE_APP) != sys.path[0]:
    if str(ACTIVE_APP) in sys.path:
        sys.path.remove(str(ACTIVE_APP))
    sys.path.insert(0, str(ACTIVE_APP))

# Avoid collision with legacy root app/ folder
if "app" in sys.modules and not hasattr(sys.modules["app"], "run_app"):
    del sys.modules["app"]

from app import app, run_app  # noqa: F401,E402

run_app()
