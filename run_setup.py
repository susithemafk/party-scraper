"""Standalone entry point for verifying the project setup."""
from pathlib import Path

from src.pipeline import run_setup_step

PROJECT_ROOT = Path(__file__).resolve().parent


def main() -> None:
    print("\n[STEP 1] Checking setup...\n")
    success = run_setup_step()
    if success:
        print("[STEP 1] Setup check passed")
    else:
        print("[STEP 1] Setup reported issues but you can continue")
    print(f"Project root: {PROJECT_ROOT}")


if __name__ == "__main__":
    main()
