"""
První patro parser - extracts event URLs and dates from patrobrno.cz
Ported from frontend/src/parsers/patro.ts
"""
from datetime import datetime
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

MONTH_MAP = {
    "leden": "01", "únor": "02", "březen": "03", "duben": "04",
    "květen": "05", "červen": "06", "červenec": "07", "srpen": "08",
    "září": "09", "říjen": "10", "listopad": "11", "prosinec": "12",
}


def patro_parser(html_string: str) -> List[Dict[str, Optional[str]]]:
    """
    Parse První patro event listing page.
    Looks for articles in .event-list with a.event__link.
    """
    soup = BeautifulSoup(html_string, "html.parser")
    items = []

    event_articles = soup.select(".event-list article")
    for article in event_articles:
        link_el = article.select_one("a.event__link")
        title_el = article.select_one("h2")
        date_el = article.select_one(".event__date")

        if not link_el or not title_el:
            continue

        url = link_el.get("href", "")

        date_str = None
        if date_el:
            day_el = date_el.select_one(".event__day")
            month_el = date_el.select_one(".event__month")

            day_text = ""
            if day_el:
                day_text = day_el.get_text(strip=True).replace(".", "")

            month_text = ""
            if month_el:
                month_text = month_el.get_text(strip=True).lower()

            day = day_text.zfill(2) if day_text else ""
            month = MONTH_MAP.get(month_text, "")

            if day and month:
                year = datetime.now().year
                date_str = f"{year}-{month}-{day}"

        items.append({"date": date_str, "url": url})

    return items
