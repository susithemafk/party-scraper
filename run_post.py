"""Post script — collect poll results, generate title, finalize, upload.

Scheduled to run at 00:01. Reads the Discord poll that was sent by
``run_morning.py``, ends it, and processes the results. If nobody voted,
all images are approved automatically.

Usage:
    python run_post.py
"""

import asyncio

from src.pipeline import post_flow


async def main() -> None:
    print("\n" + "=" * 60)
    print("  Party Scraper — Post")
    print("=" * 60 + "\n")

    await post_flow()

    print("\n" + "=" * 60)
    print("  Post flow complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
