"""Party Scraper
================
Run the full pipeline end-to-end (both morning + post flows sequentially).
For the two-phase workflow use ``run_morning.py`` and ``run_post.py`` instead.

Usage:
    python main.py --config configs/brno.yaml
"""

import argparse
import asyncio

from src.config import init_config
from src.pipeline import ensure_main_flow


async def main() -> None:
    parser = argparse.ArgumentParser(description="Party Scraper")
    parser.add_argument("--config", required=True, help="Path to city YAML config file")
    args = parser.parse_args()

    cfg = init_config(args.config)

    print("\n" + "=" * 60)
    print(f"  Party Scraper — {cfg.display_name}")
    print("=" * 60 + "\n")

    await ensure_main_flow()

    print("\n" + "=" * 60)
    print("  Party Scraper - Complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
