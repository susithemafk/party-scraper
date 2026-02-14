import subprocess
import os
import time
import sys


def run():
    # Paths
    root_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(root_dir, "frontend")
    backend_dir = os.path.join(root_dir, "backend")

    # Python executable from venv - adjust if your venv is named differently
    python_exe = os.path.join(root_dir, "venv", "Scripts", "python.exe")
    if not os.path.exists(python_exe):
        python_exe = sys.executable  # fallback

    print("--- Starting Party Scraper Full Stack ---")

    # 1. Start Backend (FastAPI)
    print("[1/2] Starting FastAPI backend on http://localhost:8000...")
    backend_process = subprocess.Popen(
        [python_exe, "main.py"],
        cwd=backend_dir
    )

    # Give backend a moment to start
    time.sleep(2)

    # 2. Start Frontend (Vite + React)
    print("[2/2] Starting Vite frontend on http://localhost:5173...")
    frontend_process = subprocess.Popen(
        ["pnpm", "dev"],
        cwd=frontend_dir,
        shell=True
    )

    print("\nApplication is ready!")
    print("- Frontend: http://localhost:5173")
    print("- Backend API: http://localhost:8000")
    print("Press Ctrl+C to stop both services.\n")

    try:
        # Keep the script running
        while True:
            if backend_process.poll() is not None:
                print("Backend process stopped unexpectedly.")
                break
            if frontend_process.poll() is not None:
                print("Frontend process stopped unexpectedly.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping services...")
    finally:
        backend_process.terminate()
        frontend_process.terminate()
        print("Done.")


if __name__ == "__main__":
    run()
