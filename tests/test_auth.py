from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app
from database.db import get_recent_radar_items, save_radar_item


def unique_email(label: str) -> str:
    return f"{label}-{uuid4().hex}@example.com"


def register(client: TestClient, name: str, email: str, password: str = "safe-password-123"):
    return client.post("/auth/register", json={"name": name, "email": email, "password": password})


def login(client: TestClient, email: str, password: str = "safe-password-123"):
    return client.post("/auth/login", json={"email": email, "password": password})


def create_radar_item() -> int:
    url = f"https://example.com/auth-test-{uuid4().hex}"
    save_radar_item(
        {
            "title": "Private account test item",
            "url": url,
            "published_at": "2026-01-01",
            "source": "Test Source",
            "summary": "A stored item for account tests.",
            "category": "models",
            "relevance_score": 7,
            "why_it_matters": "It verifies private account data.",
        }
    )
    return next(item["id"] for item in get_recent_radar_items() if item["url"] == url)


def test_registers_a_user_without_returning_password_hash():
    client = TestClient(app)
    response = register(client, "Nani", unique_email("register"))

    assert response.status_code == 201
    assert response.json()["name"] == "Nani"
    assert "password_hash" not in response.json()


def test_registration_rejects_duplicate_and_invalid_accounts():
    client = TestClient(app)
    email = unique_email("duplicate")
    assert register(client, "Nani", email).status_code == 201
    assert register(client, "Nani", email).status_code == 409
    assert register(client, "", "not-an-email", "short").status_code == 422


def test_login_me_and_logout_session_flow():
    client = TestClient(app)
    email = unique_email("session")
    register(client, "Nani", email)

    assert client.get("/auth/me").status_code == 401
    assert login(client, email, "wrong-password").status_code == 401
    login_response = login(client, email)
    assert login_response.status_code == 200
    assert "HttpOnly" in login_response.headers["set-cookie"]
    assert client.get("/auth/me").json()["email"] == email
    assert client.post("/auth/logout").status_code == 204
    assert client.get("/auth/me").status_code == 401


def test_two_users_cannot_access_each_others_preferences_saved_items_or_history():
    client_a, client_b = TestClient(app), TestClient(app)
    email_a, email_b = unique_email("user-a"), unique_email("user-b")
    register(client_a, "User A", email_a)
    register(client_b, "User B", email_b)
    login(client_a, email_a)
    login(client_b, email_b)
    item_id = create_radar_item()

    assert client_a.put("/preferences", json={"categories": ["models", "research"]}).json() == {
        "categories": ["models", "research"]
    }
    assert client_b.get("/preferences").json() == {"categories": []}

    assert client_a.post(f"/items/{item_id}/save").status_code == 201
    assert client_a.post(f"/items/{item_id}/view").status_code == 201
    assert len(client_a.get("/saved-items").json()) == 1
    assert len(client_a.get("/history").json()) == 1
    assert client_b.get("/saved-items").json() == []
    assert client_b.get("/history").json() == []
