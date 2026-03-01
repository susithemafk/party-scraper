"""Morning script — fetch, parse, generate images, send Discord poll.

Run this in the morning. The poll stays open for the reviewer to vote on
throughout the day. Results are collected by ``run_post.py`` at 00:01.

Usage:
    python run_morning.py --config configs/brno.yaml
"""

import argparse
import asyncio

from src.config import init_config
from src.pipeline import morning_flow


async def main() -> None:
    parser = argparse.ArgumentParser(description="Party Scraper — Morning")
    parser.add_argument("--config", required=True, help="Path to city YAML config file")
    args = parser.parse_args()

    cfg = init_config(args.config)

    print("\n" + "=" * 60)
    print(f"  Party Scraper — Morning ({cfg.display_name})")
    print("=" * 60 + "\n")

    await morning_flow()

    print("\n" + "=" * 60)
    print("  Morning flow complete — poll is open!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
