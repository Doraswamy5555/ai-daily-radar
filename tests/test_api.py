from fastapi.testclient import TestClient

from backend.app import main


def test_get_items_returns_collected_items(monkeypatch):
    collected_items = [
        {
            "title": "New AI model launches",
            "url": "https://example.com/ai-news",
            "published_at": "2026-01-01",
            "source": "TechCrunch AI",
            "summary": "Test summary.",
        }
    ]
    processed_items = [
        {
            **collected_items[0],
            "category": "models",
            "relevance_score": 7,
            "why_it_matters": "It may change the AI capabilities available to builders and users.",
        }
    ]
    stored_items = [{**processed_items[0], "id": 1, "created_at": "2026-01-01 12:00:00"}]
    monkeypatch.setattr(main, "collect_recent_items", lambda: collected_items)
    monkeypatch.setattr(main, "save_radar_items", lambda items: None)
    monkeypatch.setattr(main, "get_recent_radar_items", lambda category=None: stored_items)

    client = TestClient(main.app)
    response = client.get("/items")

    assert response.status_code == 200
    assert response.json() == stored_items


def test_get_items_passes_category_to_storage(monkeypatch):
    monkeypatch.setattr(main, "collect_recent_items", lambda: [])
    monkeypatch.setattr(main, "save_radar_items", lambda items: None)
    monkeypatch.setattr(
        main, "get_recent_radar_items", lambda category=None: [{"category": category}]
    )

    client = TestClient(main.app)
    response = client.get("/items?category=models")

    assert response.status_code == 200
    assert response.json() == [{"category": "models"}]
