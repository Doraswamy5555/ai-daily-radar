from fastapi import FastAPI

from ai.processor import process_item
from collectors.rss_collector import collect_recent_items
from database.db import get_recent_radar_items, initialize_database, save_radar_items


app = FastAPI(title="AI Daily Radar API")
initialize_database()


@app.get("/")
def read_root() -> dict[str, str]:
    """Return a short welcome message for the API."""
    return {"message": "AI Daily Radar API"}


@app.get("/health")
def health_check() -> dict[str, str]:
    """Report whether the API is running."""
    return {"status": "ok"}


@app.get("/items")
def get_items(category: str | None = None) -> list[dict[str, object]]:
    """Collect, process, store, and return recent AI Radar items."""
    processed_items = [process_item(item) for item in collect_recent_items()]
    save_radar_items(processed_items)
    return get_recent_radar_items(category=category)
