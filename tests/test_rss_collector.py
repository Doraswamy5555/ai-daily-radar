from types import SimpleNamespace

from collectors import rss_collector


def test_collect_recent_items_normalizes_and_removes_duplicate_urls(monkeypatch):
    feeds = {
        "https://techcrunch.com/category/artificial-intelligence/feed/": SimpleNamespace(
            bozo=False,
            entries=[
                {
                    "title": "First AI story",
                    "link": "https://example.com/first",
                    "published": "Mon, 01 Jan 2026 10:00:00 GMT",
                    "summary": "A short summary.",
                }
            ],
        ),
        "https://www.technologyreview.com/topic/artificial-intelligence/feed/": SimpleNamespace(
            bozo=False,
            entries=[
                {
                    "title": "Duplicate story",
                    "link": "https://example.com/first",
                }
            ],
        ),
        "https://venturebeat.com/category/ai/feed/": SimpleNamespace(
            bozo=False,
            entries=[
                {
                    "title": "Second AI story",
                    "link": "https://example.com/second",
                    "updated": "Tue, 02 Jan 2026 10:00:00 GMT",
                    "description": "Another summary.",
                }
            ],
        ),
    }

    monkeypatch.setattr(rss_collector.feedparser, "parse", lambda url: feeds[url])

    assert rss_collector.collect_recent_items() == [
        {
            "title": "First AI story",
            "url": "https://example.com/first",
            "published_at": "Mon, 01 Jan 2026 10:00:00 GMT",
            "source": "TechCrunch AI",
            "summary": "A short summary.",
        },
        {
            "title": "Second AI story",
            "url": "https://example.com/second",
            "published_at": "Tue, 02 Jan 2026 10:00:00 GMT",
            "source": "VentureBeat AI",
            "summary": "Another summary.",
        },
    ]


def test_collect_recent_items_skips_a_feed_that_fails(monkeypatch):
    def fake_parse(url):
        if "techcrunch" in url:
            raise OSError("Network unavailable")
        return SimpleNamespace(bozo=False, entries=[])

    monkeypatch.setattr(rss_collector.feedparser, "parse", fake_parse)

    assert rss_collector.collect_recent_items() == []


def test_normalize_item_cleans_html_and_entities():
    item = rss_collector.normalize_item(
        {
            "title": "AI&nbsp;<strong>tool</strong>",
            "link": "https://example.com/tool",
            "summary": "<p>A&nbsp;useful <em>update</em>.</p>",
        },
        "Test Source",
    )

    assert item["title"] == "AI tool"
    assert item["summary"] == "A useful update."
