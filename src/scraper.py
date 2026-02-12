from .models import EventDetail
from .extractor import extract_event_detail
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
import asyncio
import logging

logging.basicConfig(
    filename='scraper_debug.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8',
    filemode='w'  # Overwrite log each run
)
logging.info("Starting scraper.py imports...")

logging.info("Imported crawl4ai")
logging.info("Imported extractor")
logging.info("Imported models")


async def process_event(crawler: AsyncWebCrawler, url: str, known_date: str = None, actions_data: list = None, image_selector: str = None) -> EventDetail:
    """
    Crawls a single URL using the provided crawler instance and extracts details.
    """
    logging.info(f"Crawling URL: {url}")

    config = None
    js_code_blocks = []

    if actions_data:
        logging.info(f"Using custom actions: {actions_data}")
        for action in actions_data:
            a_type = action.get("type")
            if a_type == "wait":
                duration = action.get("duration", 1)
                js_code_blocks.append(
                    f"await new Promise(r => setTimeout(r, {duration * 1000}));")
            elif a_type == "click":
                selector = action.get("selector")
                if selector:
                    js_code_blocks.append(
                        f"(() => {{ let el = document.querySelector('{selector}'); if(el) el.click(); }})();")
            elif a_type == "scroll":
                direction = action.get("direction", "down")
                amount = action.get("amount", 1000)
                if direction == "down":
                    js_code_blocks.append(f"window.scrollBy(0, {amount});")
                else:
                    js_code_blocks.append(f"window.scrollBy(0, -{amount});")

    wait_for = None
    if image_selector:
        wait_for = f"css:{image_selector}"
        # Script to extract image URL from the selector
        # Returns the URL string directly
        extract_image_js = rf"""
        return (() => {{
            let el = document.querySelector('{image_selector}');
            if (!el) return null;
            let url = null;
            if (el.tagName === 'IMG') {{
                url = el.src || el.getAttribute('data-src');
            }} else {{
                let style = window.getComputedStyle(el);
                let bg = style.backgroundImage;
                if (bg && bg !== 'none') {{
                    let match = bg.match(/url\(["']?(.*?)["']?\)/);
                    if (match) url = match[1];
                }}
                if (!url) url = el.getAttribute('data-src') || el.getAttribute('data-original');
            }}
            return url ? new URL(url, document.baseURI).href : null;
        }})()
        """
        js_code_blocks.append(extract_image_js)

    config = CrawlerRunConfig(
        js_code=js_code_blocks if js_code_blocks else None,
        wait_for=wait_for,
        cache_mode=CacheMode.BYPASS
    )

    result = await crawler.arun(url=url, config=config)

    if not result.markdown:
        logging.warning(f"No content found for {url}")
        return None

    logging.info(
        f"Extracted content length: {len(result.markdown)} chars. Sending to Gemini...")
    event_detail = extract_event_detail(result.markdown)

    # Process manual image extraction result
    if result.js_execution_result:
        logging.info(f"JS execution result: {result.js_execution_result}")

    if event_detail and result.js_execution_result and image_selector:
        results_list = result.js_execution_result.get("results", [])
        if results_list and len(results_list) > 0:
            # The last result is from our image extraction script (appended last)
            image_url_result = results_list[-1]
            if image_url_result and isinstance(image_url_result, str):
                logging.info(
                    f"Overriding image URL with manual extraction: {image_url_result}")
                event_detail.image_url = image_url_result

    if event_detail:
        logging.info(f"Successfully extracted: {event_detail.title}")
        # Backfill date if missing and known
        if not event_detail.date and known_date:
            logging.info(f"Backfilling missing date with: {known_date}")
            event_detail.date = known_date
        return event_detail
    else:
        logging.error(f"Failed to extract details for {url}")
        return None


async def process_batch(input_data: dict) -> dict:
    """
    Processes the entire input dictionary structured as {Venue: [List of events]}.
    """
    results = {}

    # Initialize crawler once for the entire batch
    async with AsyncWebCrawler(verbose=True) as crawler:
        for venue, events in input_data.items():
            logging.info(f"Processing venue: {venue}")
            venue_results = []

            for event in events:
                url = event.get('url')
                known_date = event.get('date')
                actions = event.get('actions')
                image_selector = event.get('image_selector')

                if not url:
                    continue

                # Pass the crawler instance and optional actions/selector
                detail = await process_event(crawler, url, known_date, actions, image_selector)

                if detail:
                    # Enforce venue consistency if missing
                    if not detail.place:
                        detail.place = venue
                    venue_results.append(detail.dict())

            results[venue] = venue_results

    return results
