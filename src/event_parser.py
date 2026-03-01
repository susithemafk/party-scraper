"""
Event Parser - Orchestrates fetching HTML and parsing events from all venues.
Applies the appropriate parser for each venue and filters/sorts results.
Replicates the useScraper hook logic from the frontend.
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable

from .parsers.artbar import artbar_parser
from .parsers.bobyhall import bobyhall_parser
from .parsers.fleda import fleda_parser
from .parsers.kabinet import kabinet_parser
from .parsers.metro import metro_parser
from .parsers.patro import patro_parser
from .parsers.perpetuum import perpetuum_parser
from .parsers.ra import ra_parser
from .parsers.sono import sono_parser


# Venue configuration - matches the frontend VENUES array
VENUES = [
    {
        "title": "Bobyhall",
        "url": "https://bobyhall.cz/program-bobyhall/",
        "baseUrl": "https://bobyhall.cz/",
        "parser": bobyhall_parser,
    },
    {
        "title": "Fraktal",
        "url": "https://ra.co/clubs/224489/events",
        "baseUrl": "https://ra.co/",
        "parser": ra_parser,
    },
    {
        "title": "pul.pit",
        "url": "https://ra.co/clubs/206733/events",
        "baseUrl": "https://ra.co/",
        "parser": ra_parser,
    },
    {
        "title": "Metro Music Bar",
        "url": "https://www.metromusic.cz/program/",
        "baseUrl": "https://www.metromusic.cz/",
        "parser": metro_parser,
    },
    {
        "title": "První patro",
        "url": "https://patrobrno.cz/",
        "baseUrl": "https://patrobrno.cz/",
        "parser": patro_parser,
    },
    {
        "title": "Perpetuum",
        "url": "https://www.perpetuumklub.cz/program/",
        "baseUrl": "https://www.perpetuumklub.cz/",
        "parser": perpetuum_parser,
    },
    {
        "title": "Fléda",
        "url": "https://www.fleda.cz/program/",
        "baseUrl": "https://www.fleda.cz/",
        "parser": fleda_parser,
    },
    {
        "title": "Sono Music Club",
        "url": "https://www.sono.cz/program/",
        "baseUrl": "https://www.sono.cz/",
        "parser": sono_parser,
    },
    {
        "title": "Kabinet Múz",
        "url": "https://www.kabinetmuz.cz/program",
        "baseUrl": "https://www.kabinetmuz.cz/",
        "parser": kabinet_parser,
    },
    {
        "title": "Artbar",
        "url": "https://www.artbar.club/shows",
        "baseUrl": "https://www.artbar.club/",
        "parser": artbar_parser,
    },
]


def filter_and_sort_events(
    events: List[dict],
    filter_past: bool = True,
    max_results: int = 4,
) -> List[dict]:
    """
    Filter and sort parsed events.
    Replicates the useScraper hook's useMemo logic.

    Args:
        events: List of parsed event dicts with 'url' and 'date' keys.
        filter_past: Whether to filter out past events.
        max_results: Maximum number of results to return (0 = no limit).

    Returns:
        Filtered and sorted list of events.
    """
    processed = list(events)
    today = datetime.now().strftime("%Y-%m-%d")

    # Filter past events
    if filter_past:
        processed = [
            item for item in processed
            if not item.get("date") or item["date"] >= today
        ]

    # Deduplicate by URL
    seen_urls = set()
    deduped = []
    for item in processed:
        url = item.get("url", "")
        if not url:
            deduped.append(item)
            continue
        if url not in seen_urls:
            seen_urls.add(url)
            deduped.append(item)
    processed = deduped

    # Sort by date
    processed.sort(key=lambda a: a.get("date") or "9999-99-99")

    # Limit results
    if max_results > 0:
        processed = processed[:max_results]

    return processed


def parse_venue_html(html: str, parser: Callable, filter_past: bool = True, max_results: int = 4) -> List[dict]:
    """
    Parse HTML with the given parser function and apply filtering.

    Args:
        html: Raw HTML string.
        parser: Parser function that takes HTML and returns list of event dicts.
        filter_past: Whether to filter past events.
        max_results: Maximum results per venue (0 = no limit).

    Returns:
        Filtered and sorted list of event dicts.
    """
    raw_events = parser(html)
    return filter_and_sort_events(raw_events, filter_past=filter_past, max_results=max_results)


def parse_all_venues(html_results: Dict[str, Optional[str]], filter_past: bool = True, max_results: int = 4) -> Dict[str, List[dict]]:
    """
    Parse HTML for all venues and return structured results.

    Args:
        html_results: Dict mapping venue title to HTML string (or None).
        filter_past: Whether to filter past events.
        max_results: Maximum results per venue (0 = no limit).

    Returns:
        Dict mapping venue title to list of {url, date} dicts.
    """
    # Build parser lookup
    parser_map = {v["title"]: v["parser"] for v in VENUES}

    all_events = {}
    for title, html in html_results.items():
        if not html:
            print(f"[Parser] {title}: No HTML to parse, skipping.")
            all_events[title] = []
            continue

        parser = parser_map.get(title)
        if not parser:
            print(f"[Parser] {title}: No parser found, skipping.")
            all_events[title] = []
            continue

        events = parse_venue_html(html, parser, filter_past=filter_past, max_results=max_results)
        all_events[title] = events
        print(f"[Parser] {title}: Found {len(events)} events")

    return all_events


def filter_today_only(
    events: Dict[str, List[dict]],
    *,
    target_date: Optional[str] = None,
) -> Dict[str, List[dict]]:
    """
    Filter events to only include those happening on *target_date*.
    Defaults to tomorrow so that the post can be prepared a day ahead.
    Events without a date are excluded since we can't confirm the date.

    Args:
        events: Dict mapping venue title to list of event dicts.
        target_date: ISO date string (YYYY-MM-DD). Defaults to tomorrow.

    Returns:
        Dict with only the matching events per venue.
    """
    if target_date is None:
        target_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    filtered = {}
    for venue, venue_events in events.items():
        matched = [e for e in venue_events if e.get("date") == target_date]
        filtered[venue] = matched
        if matched:
            print(f"[Filter] {venue}: {len(matched)} event(s) on {target_date}")
        else:
            print(f"[Filter] {venue}: No events on {target_date}")
    return filtered


def save_fetched_events(events: Dict[str, List[dict]], output_path: str):
    """
    Save parsed events to JSON file.

    Args:
        events: Dict mapping venue title to list of event dicts.
        output_path: Path to save the JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    print(f"[Parser] Saved fetched events to: {output_path}")
