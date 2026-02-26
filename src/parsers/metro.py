"""
Metro Music Bar parser - extracts event URLs and dates from metromusic.cz
Ported from frontend/src/parsers/metro.ts
"""
import re
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup


def metro_parser(html_string: str) -> List[Dict[str, Optional[str]]]:
    """
    Parse Metro Music Bar event listing page.
    Looks for event items in #form-ajax-content or .program sections.
    """
    soup = BeautifulSoup(html_string, "html.parser")
    items = []
    seen_urls = set()

    event_elements = soup.select(
        "#form-ajax-content div.item, #form-ajax-content .item-inner, .program .item"
    )

    for el in event_elements:
        link_el = el.select_one("a")
        if not link_el:
            continue

        url = link_el.get("href", "")
        if not url or url == "#":
            continue

        # Find title
        title_el = el.select_one("h2, h3, .title")
        date_el = el.select_one("p.date")

        title = ""
        if title_el:
            title = title_el.get_text(strip=True)
        else:
            # Fallback: first line of link text
            link_text = link_el.get_text(strip=False)
            if link_text:
                title = link_text.split("\n")[0].strip()

        if not title:
            continue

        date_str = None
        date_source = ""
        if date_el:
            date_source = date_el.get_text(strip=False)
        else:
            date_source = link_el.get_text(strip=False) or ""

        match = re.search(r'(\d{1,2})/(\d{1,2})', date_source)
        if match:
            day = match.group(1).zfill(2)
            month = match.group(2).zfill(2)
            year = datetime.now().year
            date_str = f"{year}-{month}-{day}"

        if url in seen_urls:
            continue
        seen_urls.add(url)

        items.append({"date": date_str, "url": url})

    return items
