"""Party Scraper
================
Run the full pipeline end-to-end (both morning + post flows sequentially).
For the two-phase workflow use ``run_morning.py`` and ``run_post.py`` instead.

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
