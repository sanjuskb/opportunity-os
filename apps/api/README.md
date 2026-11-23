# Opportunity OS API Backend

FastAPI application providing:
- Core REST API endpoints (`/api/v1`)
- LangGraph orchestration for opportunity discovery, eligibility verification, and resume synthesis
- Multilingual voice streaming gateway with Gemini Live
- Grounded data integrations (Olostep and Crustdata)
- Playwright-based automated form execution with human approval checkpoints

## Running Locally

```bash
# Sync dependencies via uv
uv sync

# Run development server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run automated tests
uv run pytest

# Run lint and formatting
uv run ruff check .
uv run ruff format --check .
```
