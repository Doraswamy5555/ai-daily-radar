import sqlite3

from database.db import (
    get_radar_statistics,
    get_recent_radar_items,
    initialize_database,
    save_radar_item,
    save_radar_items,
    search_tool_signals,
)


def sample_item(url="https://example.com/first", category="models"):
    return {
        "title": "A sample AI item",
        "url": url,
        "published_at": "2026-01-01",
        "source": "Test Source",
        "summary": "A test summary.",
        "category": category,
        "relevance_score": 6,
        "why_it_matters": "It is a useful test item.",
    }


def test_initialize_database_creates_radar_items_table(tmp_path):
    database_path = tmp_path / "ai_daily_radar.db"

    initialize_database(database_path)

    with sqlite3.connect(database_path) as connection:
        columns = connection.execute("PRAGMA table_info(radar_items)").fetchall()

    assert database_path.exists()
    assert [column[1] for column in columns] == [
        "id",
        "title",
        "url",
        "published_at",
        "source",
        "summary",
        "category",
        "relevance_score",
        "why_it_matters",
        "created_at",
    ]
    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        }
    assert {"users", "user_preferences", "saved_items", "viewed_items"}.issubset(tables)


def test_save_radar_item_and_retrieve_it(tmp_path):
    database_path = tmp_path / "ai_daily_radar.db"

    assert save_radar_item(sample_item(), database_path) is True
    stored_items = get_recent_radar_items(database_path=database_path)

    assert len(stored_items) == 1
    assert stored_items[0]["title"] == "A sample AI item"
    assert stored_items[0]["id"] == 1
    assert stored_items[0]["created_at"]


def test_save_radar_item_ignores_duplicate_urls(tmp_path):
    database_path = tmp_path / "ai_daily_radar.db"

    assert save_radar_item(sample_item(), database_path) is True
    assert save_radar_item(sample_item(), database_path) is False

    assert len(get_recent_radar_items(database_path=database_path)) == 1


def test_get_recent_radar_items_filters_by_category(tmp_path):
    database_path = tmp_path / "ai_daily_radar.db"
    save_radar_items(
        [
            sample_item(url="https://example.com/model", category="models"),
            sample_item(url="https://example.com/tool", category="tools"),
        ],
        database_path,
    )

    stored_items = get_recent_radar_items(category="models", database_path=database_path)

    assert len(stored_items) == 1
    assert stored_items[0]["url"] == "https://example.com/model"
    assert stored_items[0]["category"] == "models"


def test_get_radar_statistics_uses_stored_data(tmp_path):
    database_path = tmp_path / "ai_daily_radar.db"
    save_radar_items(
        [
            sample_item(url="https://example.com/model", category="models"),
            {**sample_item(url="https://example.com/tool", category="tools"), "source": "Second Source", "relevance_score": 8},
        ],
        database_path,
    )

    statistics = get_radar_statistics(database_path)

    assert statistics["total_items"] == 2
    assert statistics["high_relevance_items"] == 1
    assert statistics["category_counts"]["models"] == 1
    assert statistics["category_counts"]["tools"] == 1
    assert statistics["source_counts"] == {"Second Source": 1, "Test Source": 1}
    assert statistics["relevance_distribution"]["6"] == 1
    assert statistics["relevance_distribution"]["8"] == 1
    assert sum(statistics["daily_counts"].values()) == 2


def test_get_radar_statistics_returns_empty_database_counts(tmp_path):
    statistics = get_radar_statistics(tmp_path / "ai_daily_radar.db")

    assert statistics["total_items"] == 0
    assert statistics["high_relevance_items"] == 0
    assert statistics["category_counts"] == {
        "models": 0,
        "tools": 0,
        "research": 0,
        "funding": 0,
        "companies": 0,
        "other": 0,
    }
    assert statistics["source_counts"] == {}
    assert statistics["daily_counts"] == {}


def test_statistics_include_real_category_daily_counts_and_tool_search(tmp_path):
    database_path = tmp_path / "ai_daily_radar.db"
    save_radar_items(
        [
            {**sample_item(url="https://example.com/video-tool", category="tools"), "title": "Video creation tool"},
            sample_item(url="https://example.com/model-2", category="models"),
        ], database_path,
    )

    statistics = get_radar_statistics(database_path)
    assert sum(day["tools"] for day in statistics["category_daily_counts"].values()) == 1
    matches = search_tool_signals("create video", database_path)
    assert matches[0]["title"] == "Video creation tool"
