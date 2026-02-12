"""
URL Parser - Maps URLs to their required scraping configuration.
This module determines the appropriate actions and selectors based on URL patterns.
"""
from typing import Optional
from urllib.parse import urlparse
import logging


class ScrapingConfig:
    """Configuration for scraping a specific URL."""

    def __init__(self, actions: list = None, image_selector: str = None):
        self.actions = actions or []
        self.image_selector = image_selector


def parse_url_config(url: str) -> ScrapingConfig:
    """
    Parse a URL and return the appropriate scraping configuration.

    Args:
        url: The URL to parse

    Returns:
        ScrapingConfig with actions and image_selector for this URL
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    # Remove www. prefix for easier matching
    if domain.startswith('www.'):
        domain = domain[4:]

    print(f"Domain: {domain}")

    # Domain-specific configurations
    if domain == 'artbar.club':
        return ScrapingConfig(
            actions=[],
            image_selector=None
        )

    # TODO test
    elif domain == "facebook.com":
        return ScrapingConfig(
            actions=[
                {"type": "wait", "duration": 3},
                {"type": "click_text", "text": "See more"},
                {"type": "wait", "duration": 1}
            ],
            image_selector="div[aria-label='Event photo'] img"
        )

    # TODO test
    elif domain == "fairplay.events":
        return ScrapingConfig(
            actions=[],
            image_selector=""
        )

    elif domain == "goout.net":
        return ScrapingConfig(
            actions=[
                {"type": "click", "selector": ".image-header-wrapper > span:first-child .image-wrapper > img.loaded"},
                {"type": "wait", "duration": 2},
            ],
            image_selector="#lg-item-1-5 > picture > img"
        )

    elif domain == 'eventlook.cz':
        return ScrapingConfig(
            actions=[],
            image_selector="span.wrapper > img"
        )

    elif domain == 'tootoot.fm':
        return ScrapingConfig(
            actions=[],
            image_selector="div.main-img"
        )

    # Add more domain patterns here as needed
    # Example with actions:
    # elif domain == 'example.com':
    #     return ScrapingConfig(
    #         actions=[
    #             {"type": "wait", "duration": 2},
    #             {"type": "click", "selector": ".load-more-button"},
    #             {"type": "scroll", "direction": "down", "amount": 1000}
    #         ],
    #         image_selector=".event-image"
    #     )

    # Default configuration (no special handling)
    logging.info(f"No specific config found for {domain}, using defaults")
    return ScrapingConfig()
