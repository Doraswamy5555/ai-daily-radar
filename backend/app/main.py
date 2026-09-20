from fastapi import FastAPI


app = FastAPI(title="AI Daily Radar API")


@app.get("/")
def read_root() -> dict[str, str]:
    """Return a short welcome message for the API."""
    return {"message": "AI Daily Radar API"}


@app.get("/health")
def health_check() -> dict[str, str]:
    """Report whether the API is running."""
    return {"status": "ok"}
