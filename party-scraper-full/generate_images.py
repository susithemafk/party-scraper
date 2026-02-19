"""
Image Generator - Standalone Script
====================================
Reads temp/processed-events.json (input) and generates Instagram-style
images to generated/images/ (output). Use this to iterate on styling
without re-running the full scraping pipeline.

Usage:
    python generate_images.py

Edit build_event_html() and build_title_html() in src/image_generator.py
to tweak styles, then re-run this script.
"""
import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.image_generator import generate_event_images

PROCESSED_EVENTS_PATH = os.path.join(PROJECT_ROOT, "temp", "processed-events.json")
IMAGES_DIR = os.path.join(PROJECT_ROOT, "generated", "images")


def main():
    if not os.path.exists(PROCESSED_EVENTS_PATH):
        print(f"[ERROR] File not found: {PROCESSED_EVENTS_PATH}")
        print("Run main.py first to generate processed-events.json")
        sys.exit(1)

    with open(PROCESSED_EVENTS_PATH, "r", encoding="utf-8") as f:
        processed_events = json.load(f)

    total = sum(
        len([e for e in events if not e.get("error")])
        for events in processed_events.values()
    )
    print(f"\nLoaded {total} events from {PROCESSED_EVENTS_PATH}")
    print(f"Output directory: {IMAGES_DIR}\n")

    generated = generate_event_images(processed_events, IMAGES_DIR)

    print(f"\nDone — {len(generated)} images generated in {IMAGES_DIR}/")


if __name__ == "__main__":
    main()
