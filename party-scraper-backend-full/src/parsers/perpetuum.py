"""
Perpetuum parser - extracts event URLs and dates from perpetuumklub.cz
Ported from frontend/src/parsers/perpetuum.ts
"""
import re
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup


def perpetuum_parser(html_string: str) -> List[Dict[str, Optional[str]]]:
    """
    Parse Perpetuum event listing page.
    Looks for a.block-link with .event_title and .event_date.
    """
    soup = BeautifulSoup(html_string, "html.parser")
    items = []

    event_links = soup.select("a.block-link")
    for link in event_links:
        title_el = link.select_one(".event_title")
        date_el = link.select_one(".event_date")

        if not title_el:
            continue

        url = link.get("href", "")
        if url and not url.startswith("http"):
            url = f"https://www.perpetuumklub.cz{'/' if not url.startswith('/') else ''}{url}"

        date_str = None
        if date_el:
            raw_date = date_el.get_text(strip=True)
            match = re.search(r'(\d{1,2})/(\d{1,2})', raw_date)
            if match:
                day = match.group(1).zfill(2)
                month = match.group(2).zfill(2)
                year = datetime.now().year
                date_str = f"{year}-{month}-{day}"

        items.append({"date": date_str, "url": url})

    return items
