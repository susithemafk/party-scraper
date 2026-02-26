"""Standalone wrapper — delegates to the src.review_images module.

Usage:
    python review_images.py
"""

import asyncio

from src.pipeline import GENERATED_IMAGES_DIR, TEMP_DIR
from src.review_images import run_review


async def main() -> None:
    approved = await run_review(GENERATED_IMAGES_DIR, TEMP_DIR)
    if approved:
        print(f"\nApproved {len(approved)} image(s):")
        for p in approved:
            print(f"  - {p}")
    else:
        print("\nNo images were approved.")


if __name__ == "__main__":
    asyncio.run(main())
