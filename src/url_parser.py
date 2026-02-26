"""
URL Parser - Maps URLs to their required scraping configuration.
Reused from src/url_parser.py
"""
from typing import Optional, TypedDict
from urllib.parse import urlparse
import logging


class EventSelectors(TypedDict, total=False):
    title: str
    date: str
    time: str
    place: str
    price: str
    description: str
    image_url: str


class ScrapingConfig:
    def __init__(self, actions: list = None, selectors: EventSelectors = None):
        self.actions = actions or []
        self.selectors = selectors or {}


def parse_url_config(url: str) -> ScrapingConfig:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith('www.'):
        domain = domain[4:]
    print(f"Domain: {domain}")

    if domain == 'artbar.club':
        return ScrapingConfig(actions=[], selectors={})

    elif domain == "facebook.com":
        return ScrapingConfig(
            actions=[
                {"type": "wait", "duration": 3},
                {"type": "click_text", "text": "See more"},
                {"type": "wait", "duration": 1}
            ],
            selectors={"image_url": "div[aria-label='Event photo'] img"}
        )

    elif domain == "fairplay.events":
        return ScrapingConfig(actions=[], selectors={})

    elif domain == "goout.net":
        return ScrapingConfig(actions=[], selectors={
            "description": "div.markdown",
            "image_url": ".image-header-wrapper img.loaded"
        })

    elif domain == 'eventlook.cz':
        return ScrapingConfig(actions=[], selectors={"image_url": "span.wrapper > img"})

    elif domain == 'tootoot.fm':
        return ScrapingConfig(actions=[], selectors={"image_url": "div.main-img"})

    elif domain == 'ticketportal.cz':
        return ScrapingConfig(actions=[], selectors={"image_url": "div.detail-header > img"})

    elif domain == 'sono.cz':
        return ScrapingConfig(actions=[], selectors={"image_url": "div.featured-image > img"})

    elif domain == 'kabinetmuz.cz':
        return ScrapingConfig(actions=[], selectors={"image_url": "div.detail__img"})

    elif domain == 'perpetuumklub.cz':
        return ScrapingConfig(actions=[], selectors={"image_url": "div.event_image > img"})

    elif domain == 'fleda.cz':
        return ScrapingConfig(
            actions=[
                {"type": "wait", "duration": 2},
                {"type": "click", "selector": "div.program-detail > div.clearfix > div.img > div > a > img"},
                {"type": "wait", "duration": 2},
            ],
            selectors={"image_url": "img.fancybox-image"}
        )

    elif domain == 'smsticket.cz':
        return ScrapingConfig(
            actions=[
                {"type": "wait", "duration": 2},
                {"type": "click", "selector": "div.poster > img"},
                {"type": "wait", "duration": 2},
            ],
            selectors={"image_url": "div.featherlight-content > img", "date": ".date-place"}
        )

    elif domain == 'ra.co':
        return ScrapingConfig(actions=[], selectors={
            "image_url": "section[data-tracking-id='event-detail-description'] ul li img"
        })

    logging.info(f"No specific config found for {domain}, using defaults")
    return ScrapingConfig()
