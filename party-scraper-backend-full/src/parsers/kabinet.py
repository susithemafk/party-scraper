"""
Kabinet Múz parser - extracts event URLs and dates from kabinetmuz.cz
Ported from frontend/src/parsers/kabinet.ts
"""
import re
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

BASE_URL = "https://www.kabinetmuz.cz"


def format_kabinet_date(date_str: Optional[str]) -> Optional[str]:
    """Convert date format 'DD. MM.' to 'YYYY-MM-DD'."""
    if not date_str:
        return None
    match = re.search(r'(\d+)\.\s+(\d+)\.', date_str)
    if not match:
        return None
    day = match.group(1).zfill(2)
    month = match.group(2).zfill(2)
    year = datetime.now().year
    return f"{year}-{month}-{day}"


def kabinet_parser(html_string: str) -> List[Dict[str, Optional[str]]]:
    """
    Parse Kabinet Múz event listing page.
    Looks for a.program__item links within .program__items.
    """
    soup = BeautifulSoup(html_string, "html.parser")
    events = []
    seen_urls = set()

    items = soup.select(".program__items a.program__item")
    for el in items:
        href = el.get("href", "")
        if not href:
            continue

        url = href if href.startswith("http") else BASE_URL + href

        date_el = el.select_one(".program__date")
        raw_date = date_el.get_text(strip=True) if date_el else None

        if url in seen_urls:
            continue
        seen_urls.add(url)

        events.append({
            "url": url,
            "date": format_kabinet_date(raw_date),
        })

    return events
