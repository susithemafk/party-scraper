"""Morning script — fetch, parse, generate images, send Discord poll.

Run this in the morning. The poll stays open for the reviewer to vote on
throughout the day. Results are collected by ``run_post.py`` at 00:01.

Usage:
    python run_morning.py
"""

import asyncio

from src.pipeline import morning_flow


async def main() -> None:
    print("\n" + "=" * 60)
    print("  Party Scraper — Morning")
    print("=" * 60 + "\n")

    await morning_flow()

    print("\n" + "=" * 60)
    print("  Morning flow complete — poll is open!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
