"""
Artbar parser - extracts event URLs and dates from artbar.club
Ported from frontend/src/parsers/artbar.ts
"""
import re
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup


def format_czech_date(date_str: Optional[str]) -> Optional[str]:
    """Convert Czech date format 'DD. MM.' to 'YYYY-MM-DD'."""
    if not date_str:
        return None
    match = re.search(r'(\d+)\.\s*(\d+)\.', date_str)
    if not match:
        return date_str
    day = match.group(1).zfill(2)
    month = match.group(2).zfill(2)
    year = datetime.now().year
    return f"{year}-{month}-{day}"


def artbar_parser(html_string: str) -> List[Dict[str, Optional[str]]]:
    """
    Parse Artbar event listing page.
    Looks for links with data-hook="ev-rsvp-button" and extracts URL + date.
    """
    soup = BeautifulSoup(html_string, "html.parser")
    events = []
    seen_urls = set()

    buttons = soup.select('a[data-hook="ev-rsvp-button"]')
    for btn in buttons:
        href = btn.get("href", "")
        if not href:
            continue

        # Find the container (parent elements)
        container = btn.find_parent(class_="TYl3A7") or btn.find_parent(class_="LbqWhj") or btn.parent
        raw_date = None
        if container:
            date_el = container.select_one('[data-hook="short-date"]')
            if date_el:
                raw_date = date_el.get_text(strip=True)

        url = href
        if url in seen_urls:
            continue
        seen_urls.add(url)

        events.append({
            "url": url,
            "date": format_czech_date(raw_date),
        })

    return events
