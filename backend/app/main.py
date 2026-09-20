from pathlib import Path
import os
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field

from backend.app.auth import (
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE_SECONDS,
    create_session_value,
    hash_password,
    read_session_user_id,
    verify_password,
)
from ai.processor import process_item
from collectors.rss_collector import collect_recent_items
from database.db import (
    get_radar_statistics,
    create_user,
    get_saved_items_for_user,
    get_recent_radar_items,
    get_user_by_email,
    get_user_by_id,
    get_user_preferences,
    get_view_history_for_user,
    initialize_database,
    mark_item_viewed_by_user,
    remove_saved_item_for_user,
    save_item_for_user,
    save_radar_items,
    set_user_preferences,
)


app = FastAPI(title="AI Daily Radar API")
initialize_database()
FRONTEND_DIRECTORY = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/frontend", StaticFiles(directory=FRONTEND_DIRECTORY), name="frontend")

VALID_CATEGORIES = ("models", "tools", "research", "funding", "companies", "other")


class RegistrationInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class PreferencesInput(BaseModel):
    categories: list[Literal["models", "tools", "research", "funding", "companies", "other"]]


def get_current_user(request: Request) -> dict[str, object]:
    """Require a valid signed session and return its public user record."""
    user_id = read_session_user_id(request.cookies.get(SESSION_COOKIE_NAME))
    user = get_user_by_id(user_id) if user_id else None
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user


def set_session_cookie(response: Response, user_id: int) -> None:
    """Set an HTTP-only signed session cookie suitable for local development."""
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_session_value(user_id),
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=os.getenv("APP_ENV") == "production",
    )


@app.get("/")
def read_root() -> dict[str, str]:
    """Return a short welcome message for the API."""
    return {"message": "AI Daily Radar API"}


@app.get("/health")
def health_check() -> dict[str, str]:
    """Report whether the API is running."""
    return {"status": "ok"}


@app.get("/dashboard", include_in_schema=False)
def dashboard() -> FileResponse:
    """Serve the AI Daily Radar dashboard."""
    return FileResponse(FRONTEND_DIRECTORY / "index.html")


@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register_account(payload: RegistrationInput) -> dict[str, object]:
    """Create a new account without ever storing a plain-text password."""
    user = create_user(
        name=payload.name.strip(),
        email=str(payload.email).lower(),
        password_hash=hash_password(payload.password),
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account already uses this email")
    return user


@app.post("/auth/login")
def login(payload: LoginInput, response: Response) -> dict[str, object]:
    """Verify credentials and establish an HTTP-only user session."""
    internal_user = get_user_by_email(str(payload.email).lower())
    if internal_user is None or not verify_password(payload.password, str(internal_user["password_hash"])):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    set_session_cookie(response, int(internal_user["id"]))
    return get_user_by_id(int(internal_user["id"]))  # Public fields only.


@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> Response:
    """Clear the local authenticated session cookie."""
    response.delete_cookie(SESSION_COOKIE_NAME, samesite="lax")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@app.get("/auth/me")
def get_me(user: dict[str, object] = Depends(get_current_user)) -> dict[str, object]:
    """Return the logged-in user's safe public profile."""
    return user


@app.get("/preferences")
def get_preferences(user: dict[str, object] = Depends(get_current_user)) -> dict[str, list[str]]:
    """Return the logged-in user's private category preferences."""
    return {"categories": get_user_preferences(int(user["id"]))}


@app.put("/preferences")
def update_preferences(
    payload: PreferencesInput, user: dict[str, object] = Depends(get_current_user)
) -> dict[str, list[str]]:
    """Replace the logged-in user's private category preferences."""
    categories = list(dict.fromkeys(payload.categories))
    return {"categories": set_user_preferences(int(user["id"]), categories)}


@app.post("/items/{item_id}/save", status_code=status.HTTP_201_CREATED)
def save_item(item_id: int, user: dict[str, object] = Depends(get_current_user)) -> dict[str, str]:
    """Save a global radar item for the logged-in user."""
    if not save_item_for_user(int(user["id"]), item_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Radar item not found")
    return {"status": "saved"}


@app.delete("/items/{item_id}/save", status_code=status.HTTP_204_NO_CONTENT)
def unsave_item(item_id: int, user: dict[str, object] = Depends(get_current_user)) -> Response:
    """Remove a saved radar item for the logged-in user only."""
    if not remove_saved_item_for_user(int(user["id"]), item_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved item not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/saved-items")
def get_saved_items(user: dict[str, object] = Depends(get_current_user)) -> list[dict[str, object]]:
    """Return only the logged-in user's saved radar items."""
    return get_saved_items_for_user(int(user["id"]))


@app.post("/items/{item_id}/view", status_code=status.HTTP_201_CREATED)
def mark_viewed(item_id: int, user: dict[str, object] = Depends(get_current_user)) -> dict[str, str]:
    """Record that the logged-in user viewed one radar item."""
    if not mark_item_viewed_by_user(int(user["id"]), item_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Radar item not found")
    return {"status": "viewed"}


@app.get("/history")
def get_history(user: dict[str, object] = Depends(get_current_user)) -> list[dict[str, object]]:
    """Return only the logged-in user's view history."""
    return get_view_history_for_user(int(user["id"]))


@app.get("/items")
def get_items(category: str | None = None) -> list[dict[str, object]]:
    """Collect, process, store, and return recent AI Radar items."""
    processed_items = [process_item(item) for item in collect_recent_items()]
    save_radar_items(processed_items)
    return get_recent_radar_items(category=category)


@app.get("/stats")
def get_stats() -> dict[str, object]:
    """Return analytics calculated from stored AI Radar items."""
    return get_radar_statistics()
