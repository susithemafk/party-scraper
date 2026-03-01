"""Standalone entry point for verifying the project setup."""
import argparse
from pathlib import Path

from src.config import init_config
from src.pipeline import run_setup_step

PROJECT_ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description="Party Scraper — Setup")
    parser.add_argument("--config", required=True, help="Path to city YAML config file")
    args = parser.parse_args()

    cfg = init_config(args.config)

    print(f"\n[STEP 1] Checking setup for {cfg.display_name}...\n")
    success = run_setup_step()
    if success:
        print("[STEP 1] Setup check passed")
    else:
        print("[STEP 1] Setup reported issues but you can continue")
    print(f"Project root: {PROJECT_ROOT}")


if __name__ == "__main__":
    main()
