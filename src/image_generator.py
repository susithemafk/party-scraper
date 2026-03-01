"""
Image Generator - Creates Instagram-style event images using Playwright.
Replicates the InstagramGenerator component's visual design.
"""
import base64
import random
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Dict, List, Optional, Tuple
from urllib.request import Request, urlopen
from playwright.sync_api import sync_playwright


def _get_fallback_location() -> str:
    """Return the city display name for use as a fallback location label."""
    try:
        from .config import get_config
        return get_config().fallback_location_label
    except Exception:
        return "City"


def _get_title_text() -> str:
    """Return the title text for the title-post image."""
    try:
        from .config import get_config
        return get_config().title_text or "EVENTS"
    except Exception:
        return "EVENTS"


def _get_title_alt() -> str:
    """Return alt text for the title-post background image."""
    try:
        from .config import get_config
        return get_config().title_alt or "Events"
    except Exception:
        return "Events"


def download_image_as_data_uri(url: str) -> Optional[str]:
    """Download an image URL and return it as a base64 data URI."""
    if not url:
        return None
    try:
        req = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            },
        )
        with urlopen(req, timeout=15) as resp:
            content_type = resp.headers.get("Content-Type", "image/jpeg")
            if ";" in content_type:
                content_type = content_type.split(";")[0].strip()
            if content_type == "application/octet-stream":
                content_type = "image/jpeg"
            data = resp.read()
            b64 = base64.b64encode(data).decode("ascii")
            return f"data:{content_type};base64,{b64}"
    except Exception as exc:
        print(f"[ImageGen] WARNING: Could not download image {url[:80]}... : {exc}")
        return None


TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def _load_template(name: str) -> Template:
    path = TEMPLATES_DIR / name
    return Template(path.read_text(encoding="utf-8"))


EVENT_TEMPLATE = _load_template("event.html")
TITLE_TEMPLATE = _load_template("title.html")


def render_html_with_playwright(html: str, html_path: Path, screenshot_path: Path) -> Tuple[bool, Optional[str]]:
    html_path.parent.mkdir(parents=True, exist_ok=True)
    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")

    try:
        with sync_playwright() as playwright:
            with playwright.chromium.launch(headless=True) as browser:
                page = browser.new_page(viewport={"width": 1080, "height": 1080})
                page.goto(html_path.as_uri(), wait_until="networkidle", timeout=60000)
                page.wait_for_timeout(500)
                page.screenshot(path=str(screenshot_path), full_page=True)
        return True, None
    except Exception as exc:
        return False, str(exc)


def slugify(text: str) -> str:
    """Convert text to a URL/filename-friendly slug."""
    text = unicodedata.normalize("NFD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text)
    text = text.strip("-").lower()
    return text or "event"


def build_event_html(event: dict, venue: str) -> str:
    title = event.get("title", "Název akce")
    time_str = event.get("time", "")
    place = event.get("place", venue)
    price = event.get("price", "")
    image_url = event.get("image_url", "")

    bg_html = ""
    if image_url:
        bg_html = f'''<img src="{image_url}" class="background-image" alt="{title}" />'''
    else:
        bg_html = '<div class="fallback-background"></div>'

    location_label = venue or place or _get_fallback_location()

    detail_parts = []
    if venue:
        detail_parts.append(f'<div class="detail-item">{venue}</div>')
    if time_str:
        if detail_parts:
            detail_parts.append(' | ')
        detail_parts.append(f'<div class="detail-item">{time_str}</div>')
    if price:
        if detail_parts:
            detail_parts.append(' | ')
        detail_parts.append(f'<div class="detail-item">{price}</div>')
    details_html = "".join(detail_parts)

    time_badge = "DNES"
    if time_str:
        time_badge += f" | {time_str}"

    return EVENT_TEMPLATE.substitute(
        bg_html=bg_html,
        location_label=location_label,
        time_badge=time_badge,
        title=title,
        details_html=details_html,
    )


def build_title_html(venues_str: str, date_str: str, background_html: str = "", title_text: str = "") -> str:
    return TITLE_TEMPLATE.substitute(
        venues_str=venues_str, date_str=date_str,
        background_html=background_html, title_text=title_text or "EVENTS",
    )


def generate_event_images(
    processed_events: Dict[str, List[dict]],
    output_dir: str,
    generate_title: bool = False,
) -> List[str]:
    output_dir_path = Path(output_dir)
    html_dir = output_dir_path / "html"
    output_dir_path.mkdir(parents=True, exist_ok=True)
    generated_files: List[str] = []
    background_candidates: List[str] = []

    for venue, events in processed_events.items():
        if not events:
            continue

        venue_dir = output_dir_path / venue
        venue_dir.mkdir(parents=True, exist_ok=True)

        for event in events:
            if event.get("error"):
                continue

            title = event.get("title", "event")
            slug = slugify(title)
            if not slug:
                slug = "event"
            filename = f"{slug}.png"

            original_url = event.get("image_url", "")
            if original_url and not original_url.startswith("data:"):
                print(f"[ImageGen] Downloading image for '{title}'...")
                data_uri = download_image_as_data_uri(original_url)
                if data_uri:
                    event = {**event, "image_url": data_uri}
                else:
                    event = {**event, "image_url": ""}

            final_image_url = event.get("image_url", "")
            if final_image_url:
                background_candidates.append(final_image_url)

            event_html = build_event_html(event, venue)
            full_path = venue_dir / filename
            html_path = html_dir / venue / f"{slug}.html"

            try:
                success, error = render_html_with_playwright(event_html, html_path, full_path)
                if success:
                    generated_files.append(str(full_path))
                    print(f"[ImageGen] Generated: {full_path}")
                else:
                    print(f"[ImageGen] ERROR generating image for '{title}': {error}")
            except Exception as exc:
                print(f"[ImageGen] ERROR generating image for '{title}': {exc}")

    if generate_title:
        all_venues = [v for v in processed_events.keys() if processed_events[v]]
        venues_str = " | ".join(all_venues)

        today = datetime.now()
        date_display = f"{today.day:02d}. {today.month:02d}."

        background_html = ""
        if background_candidates:
            chosen_background = random.choice(background_candidates)
            background_html = (
                f'<img src="{chosen_background}" class="background-image" '
                f'alt="{_get_title_alt()}" />'
            )

        title_html = build_title_html(venues_str, date_display, background_html,
                                      title_text=_get_title_text())
        title_path = output_dir_path / "title-post.png"
        title_html_path = html_dir / "title-post.html"

        try:
            success, error = render_html_with_playwright(title_html, title_html_path, title_path)
            if success:
                generated_files.append(str(title_path))
                print(f"[ImageGen] Generated title image: {title_path}")
            else:
                print(f"[ImageGen] ERROR generating title image: {error}")
        except Exception as exc:
            print(f"[ImageGen] ERROR generating title image: {exc}")

    print(f"\n[ImageGen] Total images generated: {len(generated_files)}")
    return generated_files
