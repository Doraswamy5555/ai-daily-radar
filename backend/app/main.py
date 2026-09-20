from fastapi import FastAPI

from ai.processor import process_item
from collectors.rss_collector import collect_recent_items


app = FastAPI(title="AI Daily Radar API")


@app.get("/")
def read_root() -> dict[str, str]:
    """Return a short welcome message for the API."""
    return {"message": "AI Daily Radar API"}


@app.get("/health")
def health_check() -> dict[str, str]:
    """Report whether the API is running."""
    return {"status": "ok"}


@app.get("/items")
def get_items() -> list[dict[str, object]]:
    """Collect and process recent AI news from the configured RSS sources."""
    return [process_item(item) for item in collect_recent_items()]
