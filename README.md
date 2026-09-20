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
