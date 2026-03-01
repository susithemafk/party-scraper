"""Run the fetch-and-parse stage and write events to disk."""
import argparse
import asyncio

from src.config import init_config
from src.pipeline import (
    fetch_and_parse_events,
    build_today_events,
)


async def main() -> None:
    parser = argparse.ArgumentParser(description="Party Scraper — Fetch")
    parser.add_argument("--config", required=True, help="Path to city YAML config file")
    args = parser.parse_args()

    cfg = init_config(args.config)

    print(f"\n[STEP 2] Fetching and parsing HTML for {cfg.display_name}...\n")
    fetched_events = await fetch_and_parse_events()

    total_events = sum(len(events) for events in fetched_events.values())
    print(f"[STEP 2] Parsed {total_events} events from {len(fetched_events)} venues")
    upcoming = build_today_events(fetched_events)
    print(f"[STEP 2] {sum(len(events) for events in upcoming.values())} of them happen today")


if __name__ == "__main__":
    asyncio.run(main())
