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


async def process_event(crawler: AsyncWebCrawler, url: str, known_date: str = None, actions_data: list = None) -> EventDetail:
    """
    Crawls a single URL using the provided crawler instance and extracts details.
    """
    logging.info(f"Crawling URL: {url}")

    config = None
    if actions_data:
        logging.info(f"Using custom actions: {actions_data}")
        js_code_blocks = []
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

        config = CrawlerRunConfig(
            js_code=js_code_blocks,
            cache_mode=CacheMode.BYPASS
        )

    result = await crawler.arun(url=url, config=config)

    if not result.markdown:
        logging.warning(f"No content found for {url}")
        return None

    logging.info(
        f"Extracted content length: {len(result.markdown)} chars. Sending to Gemini...")
    event_detail = extract_event_detail(result.markdown)

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
                actions = event.get('actions')

                # Pass the crawler instance and optional actions
                detail = await process_event(crawler, url, known_date, actions)

                if detail:
                    # Enforce venue consistency if missing
                    if not detail.place:
                        detail.place = venue
                    venue_results.append(detail.dict())

            results[venue] = venue_results

    return results
