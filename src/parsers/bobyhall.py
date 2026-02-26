"""
Bobyhall parser - extracts event URLs and dates from bobyhall.cz
Ported from frontend/src/parsers/bobyhall.ts
"""
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup


def bobyhall_parser(html_string: str) -> List[Dict[str, Optional[str]]]:
    """
    Parse Bobyhall event listing page.
    Looks for links in .fusion-grid-posts-cards .fusion-title-heading a
    Extracts title and date from text format "Title | DD. MM. YYYY"
    """
    soup = BeautifulSoup(html_string, "html.parser")
    items = []

    event_links = soup.select(".fusion-grid-posts-cards .fusion-title-heading a")
    for link in event_links:
        full_text = link.get_text(strip=False) or ""
        if "|" not in full_text:
            continue

        parts = [p.strip() for p in full_text.split("|")]
        raw_date = parts[1] if len(parts) > 1 else None

        date_str = None
        if raw_date:
            match = re.search(r'(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})', raw_date)
            if match:
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = match.group(3)
                date_str = f"{year}-{month}-{day}"

        url = link.get("href", "")
        items.append({"date": date_str, "url": url})

    return items
