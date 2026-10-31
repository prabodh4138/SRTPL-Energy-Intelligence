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
from backend.routers.bills import router as bills_router
from backend.routers.readings import router as readings_router
from backend.routers.validation import router as validation_router
from backend.routers.juno import router as juno_router
from backend.routers.consumers import router as consumers_router
from backend.routers.reports import router as reports_router
from core.supabase_manager import test_database_connection

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


@app.get("/api/health")
def health_check():
    db_status = test_database_connection()
    return {
        "status": "ONLINE",
        "service": "SRTPL Energy Intelligence FastAPI",
        "version": "2.0.0",
        "database": db_status.get("status", "OFFLINE_CACHE"),
        "database_message": db_status.get("message", "Running in offline resilient session cache"),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
