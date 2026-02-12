from .models import EventDetail
from .extractor import extract_event_detail
from .url_parser import parse_url_config
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


async def process_event(crawler: AsyncWebCrawler, url: str, known_date: str = None) -> EventDetail:
    """
    Crawls a single URL using the provided crawler instance and extracts details.
    Auto-detects required actions and selectors based on URL.
    """
    logging.info(f"Crawling URL: {url}")

    # Parse URL to get appropriate configuration
    scraping_config = parse_url_config(url)
    actions_data = scraping_config.actions
    image_selector = scraping_config.image_selector
    description_selector = scraping_config.description_selector

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
            elif a_type == "click_text":
                text = action.get("text")
                if text:
                    # Find and click element containing specific text
                    js_code_blocks.append(
                        f"""(() => {{
                            let elements = Array.from(document.querySelectorAll('*'));
                            let target = elements.find(el => el.textContent && el.textContent.includes('{text}') && !el.querySelector('*'));
                            if (!target) {{
                                target = elements.find(el => el.textContent && el.textContent.includes('{text}'));
                            }}
                            if (target) target.click();
                        }})();""")
            elif a_type == "scroll":
                direction = action.get("direction", "down")
                amount = action.get("amount", 1000)
                if direction == "down":
                    js_code_blocks.append(f"window.scrollBy(0, {amount});")
                else:
                    js_code_blocks.append(f"window.scrollBy(0, -{amount});")

    wait_for = None
    
    # Extract description if selector is provided
    if description_selector:
        extract_description_js = rf"""
        return (() => {{
            let el = document.querySelector('{description_selector}');
            return el ? el.textContent.trim() : null;
        }})();
        """
        js_code_blocks.append(extract_description_js)
    
    if image_selector:
        # Only wait for image selector if there are no actions
        # (actions handle their own timing with clicks/waits)
        if not actions_data:
            wait_for = f"css:{image_selector}"
        # Small grace period after the element appears to allow for high-res image swaps
        js_code_blocks.append("await new Promise(r => setTimeout(r, 2000));")

        # Script to extract the best image URL from all matching elements
        extract_image_js = rf"""
        return (() => {{
            let elements = document.querySelectorAll('{image_selector}');
            let candidates = [];

            for (let el of elements) {{
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

                if (url) {{
                    // Clean up common HTML entities if they somehow leaked into computed style
                    url = url.replace(/&quot;/g, '"').replace(/&amp;/g, '&');
                    try {{
                        candidates.push(new URL(url, document.baseURI).href);
                    }} catch(e) {{}}
                }}
            }}

            if (candidates.length === 0) return null;

            // Heuristic: pick the URL that looks most like a large event image
            // 1. Prefer URLs with "1200", "large", or "/Event/"
            let best = candidates.find(u => u.includes('1200') || u.includes('large') || u.includes('/Event/'));
            if (best) return best;

            // 2. Otherwise pick the longest URL (often has more parameters/higher quality)
            return candidates.sort((a, b) => b.length - a.length)[0];
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

    # Process manual extraction results
    if result.js_execution_result:
        logging.info(f"JS execution result: {result.js_execution_result}")

    if event_detail and result.js_execution_result:
        results_list = result.js_execution_result.get("results", [])
        if results_list and len(results_list) > 0:
            # Filter to only get string results (ignore action results like {'success': True})
            string_results = [r for r in results_list if isinstance(r, str)]
            result_index = 0
            
            # Extract description if we have a description selector
            if description_selector and result_index < len(string_results):
                description_result = string_results[result_index]
                if description_result:
                    logging.info(f"Overriding description with manual extraction: {description_result[:100]}...")
                    event_detail.description = description_result
                result_index += 1
            
            # Extract image URL if we have an image selector
            if image_selector and result_index < len(string_results):
                image_url_result = string_results[result_index]
                if image_url_result:
                    logging.info(f"Overriding image URL with manual extraction: {image_url_result}")
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

                if not url:
                    continue

                # URL parser will automatically determine actions and selectors
                detail = await process_event(crawler, url, known_date)

                if detail:
                    # Enforce venue consistency if missing
                    if not detail.place:
                        detail.place = venue
                    venue_results.append(detail.model_dump())

            results[venue] = venue_results

    return results
