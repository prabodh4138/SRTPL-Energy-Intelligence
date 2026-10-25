# Legacy root app package proxy to active_app
from pathlib import Path
import sys

_ACTIVE = Path(__file__).resolve().parent / "active_app"
if str(_ACTIVE) not in sys.path:
    sys.path.insert(0, str(_ACTIVE))

try:
    from active_app.app import app, run_app
except ImportError:
    pass
