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

Open the dashboard at `http://127.0.0.1:8000/dashboard`.

- `GET /` returns the API welcome message.
- `GET /health` returns the service health status.
- `GET /items` fetches, processes, stores, and returns recent AI Radar items.
- `GET /stats` returns dashboard analytics calculated from stored items.

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

## Dashboard frontend

The frontend is a dependency-free vanilla HTML, CSS, and JavaScript dashboard:

```text
frontend/
├── index.html
├── style.css
└── app.js
```

It is served by FastAPI at `/dashboard` and loads `/items` before `/stats` on
initial refresh so the analytics include newly stored items. It includes a persistent dark/light theme, category
filters, client-side search, refresh and retry controls, skeleton loading,
empty and error states, accessible keyboard focus styles, and responsive news
cards.

Analytics use only stored SQLite data. `/stats` calculates the total item
count, items with relevance score 7 or above, counts by category and source,
the score distribution, and a daily time series based on `created_at`. The
dashboard renders these values as a trend line, category doughnut, source bar
chart, and relevance bar chart using the browser's built-in Canvas API—no
external chart library is used.

## Discovery dashboard

The dashboard is now organized around AI discovery rather than generic
analytics. It includes:

- An AI requirement search that queries real stored tool-category radar items.
  If no matching verified tool signal exists, it says so instead of inventing a
  recommendation.
- A real multi-series **AI Growth Trend** for tools, models, and research. It
  only renders when two or more stored days are available.
- A real **AI Category Activity** bar chart for tools, models, research,
  funding, and companies.
- A live AI Activity summary and relevance-prioritized “Today's Important
  Updates” feed.
- Category navigation, private library links, and an explicit placeholder for
  the future verified AI Tools Directory.

RSS titles and summaries are converted to plain text before storage/display,
so HTML markup and entities such as `&nbsp;` are not shown in cards.

The requirement-search endpoint is `POST /tool-search` with a JSON body such
as `{"requirement":"create a video"}`. It searches the existing stored radar
data only; it is a foundation for the later tools directory, not a claim that
the returned update is universally the best tool.

## Run tests

From the repository root, run:

```powershell
pytest
```

The tests use sample feed responses, so they do not need internet access.

## User accounts and personalization

AI Daily Radar uses the existing `database/ai_daily_radar.db` file for local
accounts and private personalization data. Global radar items remain shared;
only preferences, saved items, and view history belong to an account.

Available account endpoints:

- `POST /auth/register` — create an account with `name`, `email`, and `password`.
- `POST /auth/login` — start an authenticated session with `email` and `password`.
- `POST /auth/logout` — end the current session.
- `GET /auth/me` — get the signed-in user's public profile.
- `GET` and `PUT /preferences` — read or replace preferred categories.
- `POST` and `DELETE /items/{item_id}/save`, plus `GET /saved-items` — manage saved items.
- `POST /items/{item_id}/view`, plus `GET /history` — manage private view history.

Passwords are hashed with bcrypt before storage and are never returned by the
API. Login uses a signed, HTTP-only, same-site cookie; authentication tokens
are never placed in browser local storage. Email validation, minimum password
length, unique emails, protected private routes, user-specific database
queries, and SQLite foreign keys provide the MVP security foundation.

Set `SESSION_SECRET` to a long random value in production. When it is not set,
the development server generates a temporary secret at startup, which signs
users out after a restart. The dashboard at `/dashboard` displays a sign-in or
sign-up experience until `/auth/me` confirms a session.

## Deployment

For production, set `APP_ENV=production`, configure a long random
`SESSION_SECRET`, and set a database URL. The production process command is:

```text
gunicorn backend.app.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
```

`Dockerfile` and `Procfile` use this command. Never commit a real `.env` file,
database password, or session secret. A production startup intentionally fails
when `SESSION_SECRET` is missing, and production cookies are marked `Secure`.

SQLite remains the zero-configuration development default:

```text
DATABASE_URL=sqlite:///database/ai_daily_radar.db
```

For PostgreSQL, provision a database, set `DATABASE_URL` to a standard
`postgresql://username:password@host:5432/database_name` URL, and apply
[`database/postgresql_schema.sql`](database/postgresql_schema.sql). The
project includes the `psycopg` PostgreSQL driver and matching production schema
so the current SQLite tables can be migrated without changing application
models. The active MVP repository layer continues to use SQLite locally; a
full production cutover should replace its SQLite query dialect with the
PostgreSQL adapter before directing production traffic to the PostgreSQL URL.
