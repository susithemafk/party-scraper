"""Party Scraper
================
Run the full pipeline: fetch, parse, AI-process, generate images,
then launch the Discord review poll.

Usage:
    python main.py
"""

import asyncio

from src.pipeline import ensure_main_flow


async def main() -> None:
    print("\n" + "=" * 60)
    print("  Party Scraper")
    print("=" * 60 + "\n")

    await ensure_main_flow()

    print("\n" + "=" * 60)
    print("  Party Scraper - Complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
