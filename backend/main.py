import os
import sys
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add active_app to sys.path so all core components are resolvable
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ACTIVE_APP_DIR = os.path.join(ROOT_DIR, "active_app")
if ACTIVE_APP_DIR not in sys.path:
    sys.path.insert(0, ACTIVE_APP_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Load environment
load_dotenv(os.path.join(ROOT_DIR, ".env"))

# Import routers
from backend.routers.dashboard import router as dashboard_router
import time
from backend.routers.bills import router as bills_router
from backend.routers.readings import router as readings_router
from backend.routers.validation import router as validation_router
from backend.routers.juno import router as juno_router
from backend.routers.consumers import router as consumers_router
from backend.routers.reports import router as reports_router
from core.supabase_manager import test_database_connection

# In-memory fast cache for database connection state (60s TTL)
_db_cache = {
    "status": "ONLINE",
    "database": "Active",
    "database_message": "Operational in resilient offline/online cache",
    "timestamp": 0.0,
}


def get_cached_db_status(force_refresh: bool = False) -> dict:
    global _db_cache
    now = time.time()
    if not force_refresh and (now - _db_cache["timestamp"] < 60.0):
        return _db_cache

    try:
        db_res = test_database_connection()
        is_conn = bool(db_res.get("connected", False))
        _db_cache = {
            "status": "ONLINE",
            "database": "CONNECTED" if is_conn else db_res.get("status", "LOCAL_OFFLINE"),
            "database_message": db_res.get("message", "Database operational"),
            "timestamp": now,
        }
    except Exception as exc:
        _db_cache = {
            "status": "ONLINE",
            "database": "LOCAL_OFFLINE",
            "database_message": f"Resilient offline cache: {exc}",
            "timestamp": now,
        }
    return _db_cache

app = FastAPI(
    title="SRTPL Energy Intelligence API",
    description="High-performance backend API for SRTPL Power Consumption Analytics and Bill Reconciliation.",
    version="2.0.0",
)

# CORS configuration to support React UI on port 5173 or any host
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all 6 module routers
app.include_router(dashboard_router)
app.include_router(readings_router)
app.include_router(validation_router)
app.include_router(juno_router)
app.include_router(bills_router)
app.include_router(consumers_router)
app.include_router(reports_router)


@app.get("/")
@app.get("/health")
@app.get("/api/health")
def health_check(refresh: bool = False):
    """Ultra-fast, sub-millisecond health endpoint for Render and React UI."""
    db_info = get_cached_db_status(force_refresh=refresh)
    return {
        "status": "ONLINE",
        "service": "SRTPL Energy Intelligence FastAPI",
        "version": "2.0.0",
        "database": db_info.get("database", "Active"),
        "database_message": db_info.get("database_message", "Operational in resilient cache"),
        "cached": not refresh,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
