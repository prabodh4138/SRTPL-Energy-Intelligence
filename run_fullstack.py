"""
SRTPL Energy Intelligence - Full Stack Runner
Starts both the FastAPI Backend (Port 8000) and the React Frontend (Port 5173).
"""
import subprocess
import sys
import time
import os

def main():
    print("===================================================================")
    print("   SRTPL ENERGY INTELLIGENCE — FULL STACK LAUNCHER")
    print("   FastAPI (Port 8000) + React (Port 5173) + Supabase")
    print("===================================================================")

    root_dir = os.path.abspath(os.path.dirname(__file__))
    frontend_dir = os.path.join(root_dir, "frontend")

    # Start FastAPI
    print("\n[1/2] Starting FastAPI Backend on http://localhost:8000...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        cwd=root_dir
    )

    # Start React Vite
    print("[2/2] Starting React Frontend on http://localhost:5173...")
    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"],
        cwd=frontend_dir,
        shell=True
    )

    print("\n" + "="*65)
    print("   🚀 System is LIVE and ready!")
    print("   👉 React User Interface:   http://localhost:5173")
    print("   👉 FastAPI Swagger API:    http://localhost:8000/docs")
    print("   👉 FastAPI Health Check:   http://localhost:8000/api/health")
    print("="*65 + "\n")
    print("Press Ctrl+C to terminate both servers.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
