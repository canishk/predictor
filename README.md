# World Cup Predictor

Lightweight web app that combines **Football-Data.org** fixtures with **Polymarket** prediction market data to surface match insights. Read-only — no betting or trading.

## Features

- Today's and tomorrow's FIFA World Cup matches (competition ID 2000)
- Polymarket win probabilities (Gamma + CLOB APIs)
- Predicted winner, goal difference, and confidence score
- Recent team form from last 5 completed matches
- Match detail page with market volume, liquidity, and explanation
- SQLite storage with prediction snapshots
- 15-minute API cache and background refresh (APScheduler)
- Dark, mobile-first React UI

## Architecture

```
Football-Data.org ──┐
                    ├── FastAPI backend ── SQLite ── React frontend
Polymarket Gamma ───┤
Polymarket CLOB  ───┘
```

## Prerequisites

- Python 3.13+
- Node.js 20+
- [Football-Data.org API token](https://www.football-data.org/client/register) (free tier)

## Setup

### 1. Clone and configure

```bash
git clone git@github.com:canishk/predictor.git
cd predictor
cp .env.example .env
```

Edit `.env` and set `FOOTBALL_DATA_API_KEY`.

### 2. Backend

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

Trigger manual refresh:

```bash
curl -X POST http://localhost:8000/api/admin/refresh
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/matches` | Today + tomorrow matches with predictions |
| GET | `/api/matches/{match_id}` | Full match detail |
| POST | `/api/admin/refresh` | Refresh fixtures, markets, predictions |
| GET | `/api/health` | Health check |

## Testing

```bash
pip install -r requirements.txt
pytest -v
```

## Project Structure

```
app/
├── api/           # FastAPI routes
├── clients/       # Football-Data, Polymarket Gamma/CLOB
├── services/      # Matching, predictions, refresh
├── models/        # SQLAlchemy models
├── schemas/       # Pydantic response models
├── repositories/  # DB access
├── database/      # Session, seeds
├── tasks/         # Scheduler reference
└── utils/         # Cache, confidence scoring
frontend/          # React + Vite + Tailwind
tests/             # unit, integration, API tests
docs/mockups/      # UI reference mockups
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FOOTBALL_DATA_API_KEY` | — | Required for fixtures |
| `DATABASE_URL` | `sqlite:///./data/worldcup.db` | SQLite path |
| `CACHE_TTL_SECONDS` | `900` | HTTP cache TTL |
| `REFRESH_INTERVAL_MINUTES` | `15` | Background refresh interval |
| `FOOTBALL_DATA_COMPETITION_ID` | `2000` | FIFA World Cup |
| `CORS_ORIGINS` | `http://localhost:5173` | Frontend origin |

## UI Mockups

Static reference layouts live in [`docs/mockups/`](docs/mockups/). Open `home-mockup.html` or `detail-mockup.html` in a browser.

## Disclaimer

This application displays publicly available prediction market data for informational purposes only. It does not facilitate betting, trading, or financial advice.
