from fastapi.testclient import TestClient

from backend.app import main


def test_get_items_returns_collected_items(monkeypatch):
    expected_items = [
        {
            "title": "AI news",
            "url": "https://example.com/ai-news",
            "published_at": "2026-01-01",
            "source": "Test Source",
            "summary": "Test summary.",
        }
    ]
    monkeypatch.setattr(main, "collect_recent_items", lambda: expected_items)

    client = TestClient(main.app)
    response = client.get("/items")

    assert response.status_code == 200
    assert response.json() == expected_items
