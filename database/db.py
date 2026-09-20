"""Simple SQLite storage for processed AI Daily Radar items."""

import sqlite3
from pathlib import Path
from typing import Any

from database.models import RadarItem


DATABASE_PATH = Path(__file__).with_name("ai_daily_radar.db")

CREATE_RADAR_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS radar_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    published_at TEXT NOT NULL,
    source TEXT NOT NULL,
    summary TEXT NOT NULL,
    category TEXT NOT NULL,
    relevance_score INTEGER NOT NULL,
    why_it_matters TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""


def initialize_database(database_path: Path | str = DATABASE_PATH) -> None:
    """Create the database file and its tables when they do not exist."""
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as connection:
        connection.execute(CREATE_RADAR_ITEMS_TABLE)


def save_radar_item(
    item: dict[str, Any], database_path: Path | str = DATABASE_PATH
) -> bool:
    """Save one processed item, returning False when its URL already exists."""
    initialize_database(database_path)
    values = (
        item.get("title", ""),
        item.get("url", ""),
        item.get("published_at", ""),
        item.get("source", ""),
        item.get("summary", ""),
        item.get("category", "other"),
        item.get("relevance_score", 1),
        item.get("why_it_matters", ""),
    )

    with sqlite3.connect(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO radar_items (
                title, url, published_at, source, summary, category,
                relevance_score, why_it_matters
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )

    return cursor.rowcount == 1


def save_radar_items(
    items: list[dict[str, Any]], database_path: Path | str = DATABASE_PATH
) -> int:
    """Save multiple processed items and return how many were new."""
    return sum(save_radar_item(item, database_path) for item in items)


def get_recent_radar_items(
    category: str | None = None,
    limit: int = 100,
    database_path: Path | str = DATABASE_PATH,
) -> list[dict[str, object]]:
    """Return recent stored items, optionally filtered by category."""
    initialize_database(database_path)
    query = "SELECT * FROM radar_items"
    parameters: list[object] = []

    if category:
        query += " WHERE category = ?"
        parameters.append(category)

    query += " ORDER BY created_at DESC, id DESC LIMIT ?"
    parameters.append(limit)

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(query, parameters).fetchall()

    return [RadarItem(**dict(row)).to_dict() for row in rows]
