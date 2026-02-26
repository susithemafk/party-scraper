"""Run the fetch-and-parse stage and write events to disk."""
import asyncio

from src.pipeline import (
    FETCHED_EVENTS_PATH,
    fetch_and_parse_events,
    build_today_events,
)


async def main() -> None:
    print("\n[STEP 2] Fetching and parsing HTML from venues...\n")
    fetched_events = await fetch_and_parse_events()

    total_events = sum(len(events) for events in fetched_events.values())
    print(f"[STEP 2] Parsed {total_events} events from {len(fetched_events)} venues")
    print(f"[STEP 2] Saved fetched event snapshot to: {FETCHED_EVENTS_PATH}")
    upcoming = build_today_events(fetched_events)
    print(f"[STEP 2] {sum(len(events) for events in upcoming.values())} of them happen today")


if __name__ == "__main__":
    asyncio.run(main())
