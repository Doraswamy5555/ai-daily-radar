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

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_USER_PREFERENCES_TABLE = """
CREATE TABLE IF NOT EXISTS user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    preferred_category TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, preferred_category),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)
"""

CREATE_SAVED_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS saved_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    radar_item_id INTEGER NOT NULL,
    saved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, radar_item_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (radar_item_id) REFERENCES radar_items(id) ON DELETE CASCADE
)
"""

CREATE_VIEWED_ITEMS_TABLE = """
CREATE TABLE IF NOT EXISTS viewed_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    radar_item_id INTEGER NOT NULL,
    viewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, radar_item_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (radar_item_id) REFERENCES radar_items(id) ON DELETE CASCADE
)
"""


def _connect(database_path: Path | str) -> sqlite3.Connection:
    """Open a SQLite connection with foreign-key checks enabled."""
    connection = sqlite3.connect(database_path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(database_path: Path | str = DATABASE_PATH) -> None:
    """Create the database file and its tables when they do not exist."""
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with _connect(path) as connection:
        connection.execute(CREATE_RADAR_ITEMS_TABLE)
        connection.execute(CREATE_USERS_TABLE)
        connection.execute(CREATE_USER_PREFERENCES_TABLE)
        connection.execute(CREATE_SAVED_ITEMS_TABLE)
        connection.execute(CREATE_VIEWED_ITEMS_TABLE)


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

    with _connect(database_path) as connection:
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

    with _connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(query, parameters).fetchall()

    return [RadarItem(**dict(row)).to_dict() for row in rows]


def get_radar_statistics(
    database_path: Path | str = DATABASE_PATH,
) -> dict[str, object]:
    """Calculate dashboard statistics from the stored radar items."""
    initialize_database(database_path)
    categories = ("models", "tools", "research", "funding", "companies", "other")
    category_counts = {category: 0 for category in categories}
    relevance_distribution = {str(score): 0 for score in range(1, 11)}

    with _connect(database_path) as connection:
        total_items = connection.execute("SELECT COUNT(*) FROM radar_items").fetchone()[0]
        high_relevance_items = connection.execute(
            "SELECT COUNT(*) FROM radar_items WHERE relevance_score >= 7"
        ).fetchone()[0]
        category_rows = connection.execute(
            "SELECT category, COUNT(*) FROM radar_items GROUP BY category"
        ).fetchall()
        source_rows = connection.execute(
            "SELECT source, COUNT(*) FROM radar_items GROUP BY source"
        ).fetchall()
        relevance_rows = connection.execute(
            "SELECT relevance_score, COUNT(*) FROM radar_items GROUP BY relevance_score"
        ).fetchall()
        daily_rows = connection.execute(
            """
            SELECT substr(created_at, 1, 10), COUNT(*)
            FROM radar_items
            GROUP BY substr(created_at, 1, 10)
            ORDER BY substr(created_at, 1, 10)
            """
        ).fetchall()
        category_daily_rows = connection.execute(
            """
            SELECT substr(created_at, 1, 10), category, COUNT(*)
            FROM radar_items
            GROUP BY substr(created_at, 1, 10), category
            ORDER BY substr(created_at, 1, 10)
            """
        ).fetchall()

    category_counts.update({category: count for category, count in category_rows})
    relevance_distribution.update({str(score): count for score, count in relevance_rows})

    category_daily_counts: dict[str, dict[str, int]] = {}
    for day, category, count in category_daily_rows:
        category_daily_counts.setdefault(day, {name: 0 for name in categories})[category] = count

    return {
        "total_items": total_items,
        "high_relevance_items": high_relevance_items,
        "category_counts": category_counts,
        "source_counts": dict(source_rows),
        "relevance_distribution": relevance_distribution,
        "daily_counts": dict(daily_rows),
        "category_daily_counts": category_daily_counts,
    }


def search_tool_signals(
    requirement: str, database_path: Path | str = DATABASE_PATH, limit: int = 8
) -> list[dict[str, object]]:
    """Find stored tool-category radar items relevant to a user requirement.

    This is intentionally a transparent keyword match until a verified tools
    directory is added. It never creates or recommends fictional tools.
    """
    terms = [term.lower() for term in requirement.split() if len(term) > 2]
    if not terms:
        return []
    initialize_database(database_path)
    clauses = " OR ".join("LOWER(title || ' ' || summary) LIKE ?" for _ in terms)
    parameters: list[object] = [f"%{term}%" for term in terms] + [limit]
    query = f"""
        SELECT * FROM radar_items
        WHERE category = 'tools' AND ({clauses})
        ORDER BY relevance_score DESC, created_at DESC, id DESC
        LIMIT ?
    """
    with _connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(query, parameters).fetchall()
    return [RadarItem(**dict(row)).to_dict() for row in rows]


def create_user(
    name: str, email: str, password_hash: str, database_path: Path | str = DATABASE_PATH
) -> dict[str, object] | None:
    """Create a user, returning None when the email already exists."""
    initialize_database(database_path)
    try:
        with _connect(database_path) as connection:
            cursor = connection.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, password_hash),
            )
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        return None

    return get_user_by_id(user_id, database_path)


def get_user_by_email(
    email: str, database_path: Path | str = DATABASE_PATH
) -> dict[str, object] | None:
    """Return an internal user record, including its hash for login verification."""
    initialize_database(database_path)
    with _connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return dict(row) if row else None


def get_user_by_id(
    user_id: int, database_path: Path | str = DATABASE_PATH
) -> dict[str, object] | None:
    """Return a public user record without the password hash."""
    initialize_database(database_path)
    with _connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return dict(row) if row else None


def get_user_preferences(
    user_id: int, database_path: Path | str = DATABASE_PATH
) -> list[str]:
    """Return only one user's preferred categories."""
    initialize_database(database_path)
    with _connect(database_path) as connection:
        rows = connection.execute(
            "SELECT preferred_category FROM user_preferences WHERE user_id = ? ORDER BY preferred_category",
            (user_id,),
        ).fetchall()
    return [row[0] for row in rows]


def set_user_preferences(
    user_id: int, categories: list[str], database_path: Path | str = DATABASE_PATH
) -> list[str]:
    """Replace one user's category preferences."""
    initialize_database(database_path)
    with _connect(database_path) as connection:
        connection.execute("DELETE FROM user_preferences WHERE user_id = ?", (user_id,))
        connection.executemany(
            "INSERT INTO user_preferences (user_id, preferred_category) VALUES (?, ?)",
            [(user_id, category) for category in categories],
        )
    return get_user_preferences(user_id, database_path)


def _radar_item_exists(item_id: int, database_path: Path | str) -> bool:
    with _connect(database_path) as connection:
        return connection.execute("SELECT 1 FROM radar_items WHERE id = ?", (item_id,)).fetchone() is not None


def save_item_for_user(
    user_id: int, item_id: int, database_path: Path | str = DATABASE_PATH
) -> bool:
    """Save an existing radar item for one user."""
    initialize_database(database_path)
    if not _radar_item_exists(item_id, database_path):
        return False
    with _connect(database_path) as connection:
        connection.execute(
            "INSERT OR IGNORE INTO saved_items (user_id, radar_item_id) VALUES (?, ?)",
            (user_id, item_id),
        )
    return True


def remove_saved_item_for_user(
    user_id: int, item_id: int, database_path: Path | str = DATABASE_PATH
) -> bool:
    """Remove a saved item belonging to one user only."""
    initialize_database(database_path)
    with _connect(database_path) as connection:
        cursor = connection.execute(
            "DELETE FROM saved_items WHERE user_id = ? AND radar_item_id = ?", (user_id, item_id)
        )
    return cursor.rowcount == 1


def get_saved_items_for_user(
    user_id: int, database_path: Path | str = DATABASE_PATH
) -> list[dict[str, object]]:
    """Return saved radar items for one user only."""
    return _get_user_radar_items(user_id, "saved_items", "saved_at", database_path)


def mark_item_viewed_by_user(
    user_id: int, item_id: int, database_path: Path | str = DATABASE_PATH
) -> bool:
    """Record that one user viewed an existing radar item."""
    initialize_database(database_path)
    if not _radar_item_exists(item_id, database_path):
        return False
    with _connect(database_path) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO viewed_items (user_id, radar_item_id, viewed_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (user_id, item_id),
        )
    return True


def get_view_history_for_user(
    user_id: int, database_path: Path | str = DATABASE_PATH
) -> list[dict[str, object]]:
    """Return viewing history for one user only."""
    return _get_user_radar_items(user_id, "viewed_items", "viewed_at", database_path)


def _get_user_radar_items(
    user_id: int, table: str, timestamp_column: str, database_path: Path | str
) -> list[dict[str, object]]:
    """Fetch user-specific saved or viewed items joined with global radar data."""
    initialize_database(database_path)
    with _connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            f"""
            SELECT radar_items.*, {table}.{timestamp_column} AS user_activity_at
            FROM {table}
            JOIN radar_items ON radar_items.id = {table}.radar_item_id
            WHERE {table}.user_id = ?
            ORDER BY {table}.{timestamp_column} DESC, radar_items.id DESC
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]
