"""
Image Generator - Creates Instagram-style event images using html2image.
Replicates the InstagramGenerator component's visual design.
"""
import base64
import os
import re
import json
import unicodedata
from typing import Dict, List, Optional
from urllib.request import urlopen, Request
from urllib.error import URLError
from html2image import Html2Image


def download_image_as_data_uri(url: str) -> Optional[str]:
    """Download an image URL and return it as a base64 data URI."""
    if not url:
        return None
    try:
        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        with urlopen(req, timeout=15) as resp:
            content_type = resp.headers.get("Content-Type", "image/jpeg")
            # Normalize content type
            if ";" in content_type:
                content_type = content_type.split(";")[0].strip()
            if content_type == "application/octet-stream":
                content_type = "image/jpeg"
            data = resp.read()
            b64 = base64.b64encode(data).decode("ascii")
            return f"data:{content_type};base64,{b64}"
    except Exception as e:
        print(f"[ImageGen] WARNING: Could not download image {url[:80]}... : {e}")
        return None


def slugify(text: str) -> str:
    """Convert text to a URL/filename-friendly slug."""
    # Normalize unicode characters
    text = unicodedata.normalize("NFD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    # Replace non-alphanumeric with hyphens
    text = re.sub(r'[^a-zA-Z0-9]+', '-', text)
    # Remove leading/trailing hyphens
    text = text.strip('-').lower()
    return text or "event"


def format_date_display(date_str: str) -> str:
    """Convert 'YYYY-MM-DD' to 'DD. MM. YYYY' for display."""
    if not date_str:
        return ""
    parts = date_str.split("-")
    if len(parts) == 3:
        year, month, day = parts
        return f"{day}. {month}. {year}"
    return date_str


def build_event_html(event: dict, venue: str) -> str:
    """
    Build the HTML for a single event Instagram post (1080x1080).
    Replicates the InstagramPost component design exactly.
    """
    title = event.get("title", "Název akce")
    time_str = event.get("time", "")
    place = event.get("place", venue)
    price = event.get("price", "")
    image_url = event.get("image_url", "")

    # Background image or fallback div
    # image_url may already be a data URI (pre-downloaded) or a remote URL
    bg_html = ""
    if image_url:
        bg_html = f'''<img src="{image_url}" class="background-image" alt="{title}" />'''
    else:
        bg_html = '<div class="fallback-background"></div>'

    # Location container (top-right badge)
    location_label = venue or place or "Brno"

    # Build detail items as separate divs with " | " separators (matches React)
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

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
        html, body {{ margin: 0; padding: 0; height: 100%; width: 100%; }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ margin: 0; padding: 0; }}
        .export-canvas {{
            width: 1080px;
            height: 1080px;
            position: relative;
            overflow: visible;
            background-color: #000;
            font-family: 'Inter', 'Helvetica', 'Arial', sans-serif;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            text-align: left;
            color: white;
        }}
        .background-image {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            z-index: 1;
        }}
        .fallback-background {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: #1e293b;
            z-index: 1;
        }}
        .location-container {{
            margin: 44px;
            padding: 16px 20px;
            border: 1px solid white;
            box-shadow: 0 0 32px -12px rgba(0, 0, 0, 1);
            position: absolute;
            top: 0;
            right: 0;
            color: white;
            z-index: 4;
            font-size: 36px;
            line-height: 1.1;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 2px;
            word-wrap: break-word;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            background: black;
            display: none;
        }}
        .gradient-overlay {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 60%;
            background: linear-gradient(to top, rgb(0 0 0 / 80%) 0%, rgba(0, 0, 0, 0.6) 60%, transparent 100%);
            z-index: 2;
        }}
        .text-content {{
            position: relative;
            z-index: 3;
            padding: 40px 60px;
        }}
        .time-badge-container {{
        }}
        .time-badge {{
            display: inline-block;
            background-color: #00af1e;
            color: white;
            padding: 8px 20px;
            font-size: 28px;
            font-weight: 600;
            border-radius: 50px;
            margin-bottom: 16px;
            text-transform: uppercase;
            display: none;
        }}
        .location-badge {{
            font-size: 24px;
            margin-bottom: 8px;
        }}
        .action-title {{
            font-size: 72px;
            line-height: 1.1;
            font-weight: 900;
            margin: 0 0 20px 0;
            text-transform: uppercase;
            letter-spacing: -1px;
            word-wrap: break-word;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
            background: none;
        }}
        .action-details {{
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 30px;
        }}
        .detail-item {{
            font-size: 32px;
            font-weight: 400;
            line-height: 30px;
        }}
    </style>
</head>
<body>
    <div class="export-canvas">
        {bg_html}
        <div class="location-container">{location_label}</div>
        <div class="gradient-overlay"></div>
        <div class="text-content">
            <div class="time-badge-container">
                <div class="time-badge">DNES{' | ' + time_str if time_str else ''}</div>
            </div>
            <h1 class="action-title">{title}</h1>
            <div class="action-details">
                {details_html}
            </div>
        </div>
    </div>
</body>
</html>"""
    return html


def build_title_html(venues_str: str, date_str: str) -> str:
    """
    Build the HTML for the title/cover Instagram post (1080x1080).
    Replicates the InstagramTitlePost component design exactly.
    """
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap');
        html, body {{ margin: 0; padding: 0; height: 100%; width: 100%; }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ margin: 0; padding: 0; }}
        .export-canvas {{
            width: 1080px;
            height: 1080px;
            position: relative;
            overflow: visible;
            background-color: #000;
            font-family: 'Inter', 'Helvetica', 'Arial', sans-serif;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            text-align: left;
            color: white;
        }}
        .fallback-background {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: #1e293b;
            z-index: 1;
        }}
        .gradient-overlay {{
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: linear-gradient(to top, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.4) 100%);
            z-index: 2;
        }}
        .text-content {{
            position: relative;
            z-index: 3;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            padding: 0 80px;
        }}
        .action-title {{
            font-size: 72px;
            line-height: 1.1;
            font-weight: 900;
            margin: 0 0 20px 0;
            text-transform: uppercase;
            letter-spacing: -1px;
            word-wrap: break-word;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
            background: none;
        }}
        .main-title {{
            font-size: 120px;
            margin-bottom: 40px;
            -webkit-line-clamp: unset;
        }}
        .date-title {{
            font-size: 100px;
            opacity: 0.9;
        }}
        .divider {{
            width: 200px;
            height: 12px;
            background: #306be1;
            margin-bottom: 40px;
        }}
        .venues {{
            font-size: 32px;
            font-weight: 800;
            margin-top: 40px;
            text-transform: uppercase;
            letter-spacing: 4px;
            opacity: 0.8;
            border-top: 2px solid rgba(255, 255, 255, 0.8);
            padding-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="export-canvas">
        <div class="fallback-background"></div>
        <div class="gradient-overlay"></div>
        <div class="text-content">
            <h1 class="action-title main-title">AKCE V BRNĚ</h1>
            <div class="divider"></div>
            <h2 class="action-title date-title">{date_str}</h2>
            <div class="venues">{venues_str}</div>
        </div>
    </div>
</body>
</html>"""
    return html


def generate_event_images(
    processed_events: Dict[str, List[dict]],
    output_dir: str,
    generate_title: bool = True,
) -> List[str]:
    """
    Generate Instagram-style images for all processed events.
    
    Args:
        processed_events: Dict mapping venue name to list of event detail dicts.
        output_dir: Base directory for saving images (e.g., 'temp/images').
        generate_title: Whether to generate a title/cover image.
        
    Returns:
        List of generated image file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    generated_files = []

    # Create single Html2Image instance with 1080x1080 size
    hti = Html2Image(size=(1080, 1080))

    # Generate title image
    if generate_title:
        all_venues = [v for v in processed_events.keys() if processed_events[v]]
        venues_str = " | ".join(all_venues)

        from datetime import datetime
        today = datetime.now()
        date_display = f"{today.day:02d}. {today.month:02d}."

        title_html = build_title_html(venues_str, date_display)
        title_path = os.path.join(output_dir, "title-post.png")

        try:
            hti.output_path = output_dir
            hti.screenshot(html_str=title_html, save_as="title-post.png")
            generated_files.append(title_path)
            print(f"[ImageGen] Generated title image: {title_path}")
        except Exception as e:
            print(f"[ImageGen] ERROR generating title image: {e}")

    # Generate event images per venue
    for venue, events in processed_events.items():
        if not events:
            continue

        venue_dir = os.path.join(output_dir, venue)
        os.makedirs(venue_dir, exist_ok=True)

        for event in events:
            if event.get("error"):
                continue

            title = event.get("title", "event")
            slug = slugify(title)
            if not slug:
                slug = "event"
            filename = f"{slug}.png"

            # Pre-download remote image and convert to data URI
            original_url = event.get("image_url", "")
            if original_url and not original_url.startswith("data:"):
                print(f"[ImageGen] Downloading image for '{title}'...")
                data_uri = download_image_as_data_uri(original_url)
                if data_uri:
                    event = {**event, "image_url": data_uri}
                else:
                    event = {**event, "image_url": ""}

            event_html = build_event_html(event, venue)

            try:
                hti.output_path = venue_dir
                hti.screenshot(html_str=event_html, save_as=filename)
                full_path = os.path.join(venue_dir, filename)
                generated_files.append(full_path)
                print(f"[ImageGen] Generated: {full_path}")
            except Exception as e:
                print(f"[ImageGen] ERROR generating image for '{title}': {e}")

    print(f"\n[ImageGen] Total images generated: {len(generated_files)}")
    return generated_files
