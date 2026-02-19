"""
Setup module - ensures all dependencies are installed and configured.
"""
import subprocess
import sys
import os
import shutil


def check_python_packages(requirements_file: str = None) -> bool:
    """Check and install required Python packages."""
    if requirements_file and os.path.exists(requirements_file):
        print("[Setup] Installing Python packages from requirements.txt...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", requirements_file],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"[Setup] ERROR installing packages: {result.stderr}")
            return False
        print("[Setup] Python packages installed successfully.")
    return True


def check_playwright() -> bool:
    """Check if Playwright browsers are installed."""
    try:
        print("[Setup] Checking Playwright installation...")
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"[Setup] WARNING: Playwright install issue: {result.stderr}")
            return False
        print("[Setup] Playwright Chromium browser is ready.")
        return True
    except Exception as e:
        print(f"[Setup] ERROR checking Playwright: {e}")
        return False


def check_env_file(project_root: str) -> bool:
    """Check if .env file exists with required keys."""
    env_path = os.path.join(project_root, ".env")
    if not os.path.exists(env_path):
        # Check parent directory
        parent_env = os.path.join(os.path.dirname(project_root), ".env")
        if os.path.exists(parent_env):
            print(f"[Setup] Found .env in parent directory, using: {parent_env}")
            return True
        print(f"[Setup] WARNING: No .env file found at {env_path}")
        print("[Setup] Creating template .env file...")
        with open(env_path, "w") as f:
            f.write("GEMINI_API_KEY=your_api_key_here\n")
        print(f"[Setup] Please edit {env_path} and add your GEMINI_API_KEY")
        return False

    # Check for required keys
    with open(env_path, "r") as f:
        content = f.read()

    if "GEMINI_API_KEY" not in content or "your_api_key_here" in content:
        print("[Setup] WARNING: GEMINI_API_KEY not configured in .env file")
        return False

    print("[Setup] .env file is configured.")
    return True


def check_chrome_browser() -> bool:
    """Check if Chrome or Chromium is available for html2image."""
    chrome_paths = [
        # Windows
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        # Linux
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        # macOS
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"[Setup] Chrome found at: {path}")
            return True

    # Try which/where
    if shutil.which("chrome") or shutil.which("chromium") or shutil.which("google-chrome"):
        print("[Setup] Chrome found in PATH.")
        return True

    print("[Setup] WARNING: Chrome/Chromium not found. html2image requires it for image generation.")
    return False


def ensure_temp_dirs(project_root: str):
    """Create necessary temp directories."""
    temp_dir = os.path.join(project_root, "temp")
    images_dir = os.path.join(temp_dir, "images")
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    print(f"[Setup] Temp directories ready: {temp_dir}")


def run_setup(project_root: str) -> bool:
    """Run all setup checks."""
    print("=" * 60)
    print("  Party Scraper - Setup Check")
    print("=" * 60)

    requirements_file = os.path.join(project_root, "requirements.txt")
    all_ok = True

    if not check_python_packages(requirements_file):
        all_ok = False

    if not check_playwright():
        all_ok = False

    if not check_env_file(project_root):
        all_ok = False

    if not check_chrome_browser():
        # Not fatal - image generation is the last step
        print("[Setup] Image generation may not work without Chrome.")

    ensure_temp_dirs(project_root)

    if all_ok:
        print("\n[Setup] All checks passed! Ready to run.")
    else:
        print("\n[Setup] Some checks failed. See warnings above.")

    print("=" * 60)
    return all_ok
