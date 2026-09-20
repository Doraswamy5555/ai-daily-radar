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
- `GET /items` fetches, processes, stores, and returns recent AI Radar items.

## RSS collector

The first collector fetches public AI-focused RSS feeds from TechCrunch, MIT
Technology Review, and VentureBeat. Each result has a title, URL, published
date, source name, and summary when the feed provides one. Duplicate URLs and
feeds that cannot be reached are skipped.

Run the API and open `http://127.0.0.1:8000/items` to see the latest items.

## Rule-based processing

Each raw RSS item is processed locally by `ai/processor.py`; no AI or LLM API
is used. It classifies the title and summary into `models`, `tools`,
`research`, `funding`, `companies`, or `other` using simple keywords.

The processor also returns a relevance score from 1 to 10. Items start at 3
points and receive points for a trusted source, a summary, a category match,
high-impact language such as "launch", and funding news. The
`why_it_matters` field is a short category-specific explanation.

## SQLite storage

The API uses Python's built-in `sqlite3` library. On first start, it creates
`database/ai_daily_radar.db` and a `radar_items` table. Each call to `/items`
collects and processes the latest feed entries, saves any URLs not already in
the database, then returns the most recently stored items.

To return only one category, add the optional `category` query parameter:

```text
http://127.0.0.1:8000/items?category=models
```

Valid current categories are `models`, `tools`, `research`, `funding`,
`companies`, and `other`.

## Run tests

From the repository root, run:

```powershell
pytest
```

The tests use sample feed responses, so they do not need internet access.
