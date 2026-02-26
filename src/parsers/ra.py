"""
Resident Advisor (RA) parser - extracts event URLs and dates from ra.co
Ported from frontend/src/parsers/ra.ts
"""
import re
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

RA_MONTH_MAP = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "may": "05", "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
}


def ra_parser(html_string: str) -> List[Dict[str, Optional[str]]]:
    """
    Parse Resident Advisor event listing page.
    Looks for event cards with data-testid="event-listing-card".
    """
    soup = BeautifulSoup(html_string, "html.parser")
    items = []

    event_cards = soup.select('[data-testid="event-listing-card"]')
    for card in event_cards:
        # Find title link
        title_el = (
            card.select_one('[data-pw-test-id="event-title"] a')
            or card.select_one("h3 a")
        )
        if not title_el:
            continue

        url = title_el.get("href", "")
        if url and url.startswith("/"):
            url = f"https://ra.co{url}"

        # Find date
        date_el = (
            card.select_one('span[color="secondary"]')
            or card.select_one(".Text-sc-wks9sf-0.dhcUaC")
        )

        date_str = None
        if date_el:
            raw_date = date_el.get_text(strip=True)
            match = re.search(r'(\d{1,2})\s+([a-zA-Z]{3})', raw_date)
            if match:
                day = match.group(1).zfill(2)
                month_name = match.group(2).lower()
                month = RA_MONTH_MAP.get(month_name)
                if month:
                    year = datetime.now().year
                    date_str = f"{year}-{month}-{day}"

        items.append({"date": date_str, "url": url})

    return items
