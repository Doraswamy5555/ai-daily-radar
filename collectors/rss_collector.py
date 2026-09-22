"""Collect and normalize recent AI news from RSS feeds."""

import logging
import re
from html import unescape
from typing import Any

import feedparser


logger = logging.getLogger(__name__)

RSS_SOURCES = [
    {
        "name": "TechCrunch AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
    },
    {
        "name": "MIT Technology Review AI",
        "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
    },
    {
        "name": "VentureBeat AI",
        "url": "https://venturebeat.com/category/ai/feed/",
    },
]


def collect_recent_items() -> list[dict[str, str]]:
    """Fetch RSS sources and return normalized, unique news items.

    A failed feed is logged and skipped so that the remaining sources can still
    provide results.
    """
    items: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for source in RSS_SOURCES:
        try:
            feed = feedparser.parse(source["url"])
        except Exception as error:
            logger.warning("Could not fetch %s: %s", source["name"], error)
            continue

        if getattr(feed, "bozo", False) and not feed.entries:
            logger.warning("Could not parse %s", source["name"])
            continue

        for entry in feed.entries:
            item = normalize_item(entry, source["name"])
            if item is None or item["url"] in seen_urls:
                continue

            seen_urls.add(item["url"])
            items.append(item)

    return items


def normalize_item(entry: Any, source_name: str) -> dict[str, str] | None:
    """Convert one RSS entry into the API's consistent item structure."""
    title = clean_rss_text(entry.get("title", ""))
    url = entry.get("link", "").strip()

    # A title and URL make an item useful; skip incomplete feed entries.
    if not title or not url:
        return None

    return {
        "title": title,
        "url": url,
        "published_at": entry.get("published", entry.get("updated", "")),
        "source": source_name,
        "summary": clean_rss_text(entry.get("summary", entry.get("description", ""))),
    }


def clean_rss_text(value: str) -> str:
    """Convert RSS HTML and entities into plain text suitable for the UI."""
    without_tags = re.sub(r"<[^>]+>", " ", value or "")
    normalized = " ".join(unescape(without_tags).split())
    return re.sub(r"\s+([,.;:!?])", r"\1", normalized)
