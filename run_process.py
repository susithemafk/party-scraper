"""Process today's events with AI and cache the detailed results."""
import asyncio
from src.pipeline import (
    PROCESSED_EVENTS_PATH,
    build_today_events,
    load_fetched_events,
    process_today_events,
)


async def main() -> None:
    print("\n[STEP 3] Loading fetched events for AI processing...\n")
    try:
        fetched_events = load_fetched_events()
    except FileNotFoundError as exc:
        print("[STEP 3] Cannot load fetched events. Run run_fetch.py first.")
        print(exc)
        return
    today_events = build_today_events(fetched_events)

    today_total = sum(len(events) for events in today_events.values())
    if today_total == 0:
        print("[STEP 3] No events scheduled for today. Aborting processing.")
        return

    processed_events = await process_today_events(today_events)
    processed_count = sum(
        len([e for e in events if not e.get("error")])
        for events in processed_events.values()
    )

    print(f"[STEP 3] Processed {processed_count}/{today_total} events")
    print(f"[STEP 3] AI results written to: {PROCESSED_EVENTS_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
