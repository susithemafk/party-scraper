"""
Party Scraper - Full Backend
============================
A standalone script that scrapes party event listings from Brno venues,
extracts detailed event information using AI (Gemini), and generates
Instagram-style images.

Usage:
    python main.py

Steps:
    1. Setup check (dependencies, env, Playwright browsers)
    2. Fetch HTML from all venue websites
    3. Parse events from HTML using venue-specific parsers
    4. Save parsed events to temp/fetched-events.json
    5. AI-process each event URL for detailed extraction
    6. Save processed events to temp/processed-events.json
    7. Generate Instagram-style images to generated/images/
"""
import asyncio
import json
import os
import platform
import sys

# Critical for Windows
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Project root
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.setup import run_setup
from src.fetcher import fetch_all_venues
from src.event_parser import VENUES, parse_all_venues, save_fetched_events, filter_today_only
from src.ai_scraper import process_all_events
from src.image_generator import generate_event_images


async def main():
    """Main orchestrator - runs all steps sequentially."""
    print("\n" + "=" * 60)
    print("  Party Scraper - Full Backend")
    print("=" * 60 + "\n")

    # ──────────────────────────────────────────────
    # STEP 1: Setup check
    # ──────────────────────────────────────────────
    print("\n[STEP 1] Checking setup...\n")
    setup_ok = run_setup(PROJECT_ROOT)
    if not setup_ok:
        print("\n[WARNING] Setup issues detected. Continuing anyway...")

    # ──────────────────────────────────────────────
    # STEP 2: Fetch HTML from all venues
    # ──────────────────────────────────────────────
    print("\n[STEP 2] Fetching HTML from all venue websites...\n")
    html_results = await fetch_all_venues(VENUES)

    fetched_count = sum(1 for v in html_results.values() if v)
    print(f"\n[STEP 2] Fetched HTML from {fetched_count}/{len(VENUES)} venues")

    # ──────────────────────────────────────────────
    # STEP 3: Parse events from HTML
    # ──────────────────────────────────────────────
    print("\n[STEP 3] Parsing events from HTML...\n")
    fetched_events = parse_all_venues(html_results, filter_past=True, max_results=4)

    total_events = sum(len(events) for events in fetched_events.values())
    print(f"\n[STEP 3] Found {total_events} events across all venues")

    # ──────────────────────────────────────────────
    # STEP 4 (save): Save fetched events to JSON
    # ──────────────────────────────────────────────
    fetched_path = os.path.join(PROJECT_ROOT, "temp", "fetched-events.json")
    save_fetched_events(fetched_events, fetched_path)
    print(f"[STEP 3] Saved to: {fetched_path}")

    if total_events == 0:
        print("\n[WARNING] No events found. Exiting.")
        return

    # ──────────────────────────────────────────────
    # STEP 4b: Filter to today's events only
    # ──────────────────────────────────────────────
    print("\n[STEP 3b] Filtering events to today only...\n")
    today_events = filter_today_only(fetched_events)

    today_total = sum(len(events) for events in today_events.values())
    print(f"\n[STEP 3b] {today_total} events happening today")

    if today_total == 0:
        print("\n[WARNING] No events today. Exiting.")
        return

    # ──────────────────────────────────────────────
    # STEP 5: AI-process each event URL
    # ──────────────────────────────────────────────
    print("\n[STEP 4] Running AI extraction on today's event URLs...\n")
    processed_path = os.path.join(PROJECT_ROOT, "temp", "processed-events.json")
    processed_events = await process_all_events(today_events, processed_path)

    processed_count = sum(
        len([e for e in events if not e.get("error")])
        for events in processed_events.values()
    )
    print(f"\n[STEP 4] Successfully processed {processed_count}/{total_events} events")

    # ──────────────────────────────────────────────
    # STEP 6-7: Generate images
    # ──────────────────────────────────────────────
    print("\n[STEP 5] Generating Instagram-style images...\n")
    images_dir = os.path.join(PROJECT_ROOT, "generated", "images")
    generated_files = generate_event_images(processed_events, images_dir)

    print(f"\n[STEP 5] Generated {len(generated_files)} images")

    # ──────────────────────────────────────────────
    # DONE
    # ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Party Scraper - Complete!")
    print("=" * 60)
    print(f"\n  Fetched events:   {fetched_path}")
    print(f"  Processed events: {processed_path}")
    print(f"  Images:           {images_dir}/")
    print(f"  Total images:     {len(generated_files)}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
