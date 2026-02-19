"""
Fléda parser - extracts event URLs and dates from fleda.cz
Ported from frontend/src/parsers/fleda.ts
"""
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

MONTH_MAP = {
    "leden": "01", "únor": "02", "březen": "03", "duben": "04",
    "květen": "05", "červen": "06", "červenec": "07", "srpen": "08",
    "září": "09", "říjen": "10", "listopad": "11", "prosinec": "12",
}


def fleda_parser(html_string: str) -> List[Dict[str, Optional[str]]]:
    """
    Parse Fléda event listing page.
    Looks for events in .program-archive > div > div with a.img links.
    """
    soup = BeautifulSoup(html_string, "html.parser")
    items = []

    program_archive = soup.select_one(".program-archive")
    if not program_archive:
        return items

    # Select direct children divs, then their children divs
    outer_divs = program_archive.find_all("div", recursive=False)
    event_elements = []
    for outer in outer_divs:
        inner_divs = outer.find_all("div", recursive=False)
        event_elements.extend(inner_divs)

    for el in event_elements:
        link_el = el.select_one("a.img")
        if not link_el:
            continue

        # Find title
        title_el = (
            el.select_one("h3 a") or el.select_one("h3")
            or el.select_one("h2 a") or el.select_one(".info h3")
        )
        title = title_el.get_text(strip=True) if title_el else ""
        if not title:
            continue

        url = link_el.get("href", "")
        if url and not url.startswith("http"):
            url = f"https://www.fleda.cz{'/' if not url.startswith('/') else ''}{url}"

        date_str = None
        date_el = el.select_one(".date")
        if date_el:
            day_el = date_el.select_one(".num")
            month_el = date_el.select_one(".month")
            year_el = date_el.select_one(".year")

            day_num = day_el.get_text(strip=True).zfill(2) if day_el else None
            month_name = month_el.get_text(strip=True).lower() if month_el else ""
            year_num = year_el.get_text(strip=True) if year_el else None
            month_num = MONTH_MAP.get(month_name)

            if day_num and month_num and year_num:
                date_str = f"{year_num}-{month_num}-{day_num}"

        items.append({"date": date_str, "url": url})

    return items
