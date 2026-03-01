"""Standalone wrapper — delegates to the src.review_images module.

Usage:
    python review_images.py --config configs/brno.yaml
"""

import argparse
import asyncio

from src.config import init_config
from src.pipeline import _get_generated_images_dir, _get_temp_dir
from src.review_images import run_review


async def main() -> None:
    parser = argparse.ArgumentParser(description="Party Scraper — Review Images")
    parser.add_argument("--config", required=True, help="Path to city YAML config file")
    args = parser.parse_args()

    init_config(args.config)

    approved = await run_review(_get_generated_images_dir(), _get_temp_dir())
    if approved:
        print(f"\nApproved {len(approved)} image(s):")
        for p in approved:
            print(f"  - {p}")
    else:
        print("\nNo images were approved.")


if __name__ == "__main__":
    asyncio.run(main())
