import sqlite3

from database.db import (
    get_recent_radar_items,
    initialize_database,
    save_radar_item,
    save_radar_items,
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
