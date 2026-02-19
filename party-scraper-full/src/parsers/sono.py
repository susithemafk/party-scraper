"""
Sono Music Club parser - extracts event URLs and dates from sono.cz
Ported from frontend/src/parsers/sono.ts
"""
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup


def format_sono_date(date_str: Optional[str]) -> Optional[str]:
    """Convert date format 'DD.MM.YYYY' to 'YYYY-MM-DD'."""
    if not date_str:
        return None
    match = re.search(r'(\d+)\.(\d+)\.(\d+)', date_str)
    if not match:
        return None
    day = match.group(1).zfill(2)
    month = match.group(2).zfill(2)
    year = match.group(3)
    return f"{year}-{month}-{day}"


def sono_parser(html_string: str) -> List[Dict[str, Optional[str]]]:
    """
    Parse Sono Music Club event listing page.
    Looks for a.link elements and finds dates from parent containers.
    """
    soup = BeautifulSoup(html_string, "html.parser")
    events = []
    seen_urls = set()

    items = soup.select("a.link")
    for el in items:
        href = el.get("href", "")
        if not href:
            continue

        # Find parent container
        container = el.find_parent(class_="item") or el.find_parent(class_="post") or el.parent
        raw_date = None
        if container:
            date_el = container.select_one("p.date")
            if date_el:
                raw_date = date_el.get_text(strip=True)

        url = href
        if url in seen_urls:
            continue
        seen_urls.add(url)

        events.append({
            "url": url,
            "date": format_sono_date(raw_date),
        })

    return events
