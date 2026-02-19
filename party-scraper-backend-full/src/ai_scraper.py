"""
AI Scraper - Uses crawl4ai + Gemini to extract detailed event information.
Replicates the /scrape-batch-stream logic from the backend.
Reused from src/scraper.py
"""
import asyncio
import json
import logging
import os
from typing import Optional, Dict, Any, List

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

from .models import EventDetail
from .extractor import extract_event_detail
from .url_parser import parse_url_config

logging.basicConfig(
    filename='scraper_debug.log', level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8', filemode='w'
)


async def process_event(crawler: AsyncWebCrawler, url: str, known_date: Optional[str] = None) -> Optional[EventDetail]:
    """
    Process a single event URL: crawl the page and extract details via Gemini.
    
    Args:
        crawler: An active AsyncWebCrawler instance.
        url: The event page URL.
        known_date: Optional pre-known date to backfill if extraction misses it.
        
    Returns:
        EventDetail or None on failure.
    """
    logging.info(f"Crawling URL: {url}")
    scraping_config = parse_url_config(url)
    actions_data = scraping_config.actions
    selectors = scraping_config.selectors
    js_code_blocks = []

    if actions_data:
        logging.info(f"Using custom actions: {actions_data}")
        for action in actions_data:
            a_type = action.get("type")
            if a_type == "wait":
                duration = action.get("duration", 1)
                js_code_blocks.append(f"await new Promise(r => setTimeout(r, {duration * 1000}));")
            elif a_type == "click":
                selector = action.get("selector")
                if selector:
                    js_code_blocks.append(
                        f"(() => {{ let el = document.querySelector('{selector}'); if(el) el.click(); }})();"
                    )
            elif a_type == "click_text":
                text = action.get("text")
                if text:
                    js_code_blocks.append(
                        f"""(() => {{
                            let elements = Array.from(document.querySelectorAll('*'));
                            let target = elements.find(el => el.textContent && el.textContent.includes('{text}') && !el.querySelector('*'));
                            if (!target) {{ target = elements.find(el => el.textContent && el.textContent.includes('{text}')); }}
                            if (target) target.click();
                        }})();"""
                    )
            elif a_type == "scroll":
                direction = action.get("direction", "down")
                amount = action.get("amount", 1000)
                if direction == "down":
                    js_code_blocks.append(f"window.scrollBy(0, {amount});")
                else:
                    js_code_blocks.append(f"window.scrollBy(0, -{amount});")

    wait_for = None
    extraction_fields = []

    for field_name, selector in selectors.items():
        if not selector:
            continue
        extraction_fields.append(field_name)
        if field_name == "image_url":
            if not actions_data:
                wait_for = f"css:{selector}"
            js_code_blocks.append("await new Promise(r => setTimeout(r, 2000));")
            extract_image_js = rf"""
            return (() => {{
                let elements = document.querySelectorAll({json.dumps(selector)});
                let candidates = [];
                for (let el of elements) {{
                    let url = null;
                    if (el.tagName === 'IMG') {{ url = el.src || el.getAttribute('data-src'); }}
                    else {{
                        let style = window.getComputedStyle(el);
                        let bg = style.backgroundImage;
                        if (bg && bg !== 'none') {{ let match = bg.match(/url\(["']?(.*?)["']?\)/); if (match) url = match[1]; }}
                        if (!url) url = el.getAttribute('data-src') || el.getAttribute('data-original');
                    }}
                    if (url) {{
                        url = url.replace(/&quot;/g, '"').replace(/&amp;/g, '&');
                        try {{ candidates.push(new URL(url, document.baseURI).href); }} catch(e) {{}}
                    }}
                }}
                if (candidates.length === 0) return null;
                let best = candidates.find(u => u.includes('1200') || u.includes('large') || u.includes('/Event/'));
                if (best) return best;
                return candidates.sort((a, b) => b.length - a.length)[0];
            }})();
            """
            js_code_blocks.append(extract_image_js)
        else:
            extract_text_js = rf"""
            return (() => {{
                let el = document.querySelector({json.dumps(selector)});
                return el ? el.textContent.trim() : null;
            }})();
            """
            js_code_blocks.append(extract_text_js)

    config = CrawlerRunConfig(
        js_code=js_code_blocks if js_code_blocks else [],
        wait_for=wait_for if wait_for else "",
        cache_mode=CacheMode.BYPASS,
        session_id="session_1",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    result: Any = await crawler.arun(url=url, config=config)

    if not result.markdown:
        logging.warning(f"No content found for {url}")
        return None

    logging.info(f"Extracted content length: {len(result.markdown)} chars. Sending to Gemini...")
    event_detail = extract_event_detail(result.markdown)

    if hasattr(result, 'js_execution_result') and result.js_execution_result:
        logging.info(f"JS execution result: {result.js_execution_result}")

    if event_detail and hasattr(result, 'js_execution_result') and result.js_execution_result and extraction_fields:
        results_list = result.js_execution_result.get("results", [])
        if results_list and len(results_list) > 0:
            string_results = [r for r in results_list if isinstance(r, str)]
            for idx, field_name in enumerate(extraction_fields):
                if idx < len(string_results) and string_results[idx]:
                    extracted_value = string_results[idx]
                    logging.info(
                        f"Overriding {field_name} with manual extraction: "
                        f"{extracted_value[:100] if len(extracted_value) > 100 else extracted_value}..."
                    )
                    setattr(event_detail, field_name, extracted_value)

    if event_detail:
        logging.info(f"Successfully extracted: {event_detail.title}")
        if not event_detail.date and known_date:
            logging.info(f"Backfilling missing date with: {known_date}")
            event_detail.date = known_date
        return event_detail
    else:
        logging.error(f"Failed to extract details for {url}")
        return None


async def process_all_events(input_data: Dict[str, List[dict]], output_path: str) -> Dict[str, list]:
    """
    Process all events for all venues using crawl4ai + Gemini extraction.
    Saves results incrementally to output_path.
    
    Args:
        input_data: Dict mapping venue name to list of {url, date} dicts.
        output_path: Path to save the processed-events.json file.
        
    Returns:
        Dict mapping venue name to list of EventDetail dicts.
    """
    results: Dict[str, list] = {}

    async with AsyncWebCrawler(verbose=True) as crawler:
        total_events = sum(len(events) for events in input_data.values())
        processed_count = 0

        for venue, events in input_data.items():
            print(f"\n{'='*40}")
            print(f"  AI Processing: {venue} ({len(events)} events)")
            print(f"{'='*40}")

            venue_results = []
            for event in events:
                url = event.get("url")
                date = event.get("date")
                if not url:
                    continue

                processed_count += 1
                print(f"  [{processed_count}/{total_events}] Processing: {url}")

                try:
                    detail = await asyncio.wait_for(
                        process_event(crawler, url, date or ""),
                        timeout=60.0
                    )
                    if detail:
                        if not detail.place:
                            detail.place = venue
                        venue_results.append(detail.model_dump())
                        print(f"    -> Extracted: {detail.title}")
                    else:
                        venue_results.append({"url": url, "error": "Extraction failed"})
                        print(f"    -> FAILED: No data extracted")
                except asyncio.TimeoutError:
                    venue_results.append({"url": url, "error": "Timeout after 60s"})
                    print(f"    -> TIMEOUT")
                except Exception as e:
                    venue_results.append({"url": url, "error": str(e)})
                    print(f"    -> ERROR: {e}")

            results[venue] = venue_results

            # Save incrementally
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n[AI Scraper] All done! Results saved to: {output_path}")
    return results
