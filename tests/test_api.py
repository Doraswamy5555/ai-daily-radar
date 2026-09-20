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
    monkeypatch.setattr(main, "collect_recent_items", lambda: collected_items)

    client = TestClient(main.app)
    response = client.get("/items")

    assert response.status_code == 200
    assert response.json() == [
        {
            **collected_items[0],
            "category": "models",
            "relevance_score": 7,
            "why_it_matters": "It may change the AI capabilities available to builders and users.",
        }
    ]
