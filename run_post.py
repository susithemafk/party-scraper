"""Post script — collect poll results, generate title, finalize, upload.

Scheduled to run at 00:01. Reads the Discord poll that was sent by
``run_morning.py``, ends it, and processes the results. If nobody voted,
all images are approved automatically.

Usage:
    python run_post.py --config configs/brno.yaml
"""

import argparse
import asyncio

from src.config import init_config
from src.pipeline import post_flow


async def main() -> None:
    parser = argparse.ArgumentParser(description="Party Scraper — Post")
    parser.add_argument("--config", required=True, help="Path to city YAML config file")
    args = parser.parse_args()

    cfg = init_config(args.config)

    print("\n" + "=" * 60)
    print(f"  Party Scraper — Post ({cfg.display_name})")
    print("=" * 60 + "\n")

    await post_flow()

    print("\n" + "=" * 60)
    print("  Post flow complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
