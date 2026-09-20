# ai-daily-radar
AI-powered platform that discovers, analyzes, and tracks the latest AI tools and developments.

## Run locally

1. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install the dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Start the API from the repository root:

   ```powershell
   uvicorn backend.app.main:app --reload
   ```

The API will be available at `http://127.0.0.1:8000`.

- `GET /` returns the API welcome message.
- `GET /health` returns the service health status.
- `GET /items` fetches and returns recent AI news from the configured RSS feeds.

## RSS collector

The first collector fetches public AI-focused RSS feeds from TechCrunch, MIT
Technology Review, and VentureBeat. Each result has a title, URL, published
date, source name, and summary when the feed provides one. Duplicate URLs and
feeds that cannot be reached are skipped.

Run the API and open `http://127.0.0.1:8000/items` to see the latest items.

## Run tests

From the repository root, run:

```powershell
pytest
```

The tests use sample feed responses, so they do not need internet access.
