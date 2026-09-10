# SatQuery AI

Satellite imagery analysis app. Ask natural-language questions about satellite images and get structured results.

## Running

### Docker (recommended)

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs
- PostgreSQL: localhost:5433 (user: `satquery`, pass: `satquery`, db: `satquery`)

### Manual

**PostgreSQL** — create the database first:

```sql
CREATE USER satquery WITH PASSWORD 'satquery';
CREATE DATABASE satquery OWNER satquery;
```

**Backend** (http://localhost:8000):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit if your postgres runs elsewhere
uvicorn app.main:app --reload --port 8000
```

**Frontend** (http://localhost:5173):

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

### Backend (`backend/.env`)

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://satquery:satquery@localhost:5432/satquery` | PostgreSQL connection string |
| `JWT_SECRET_KEY` | `change-me` | Secret for signing JWT tokens |
| `UPLOAD_DIR` | `./uploads` | Where uploaded images are stored |
| `MAX_UPLOAD_SIZE_MB` | `50` | Max upload size in MB |
| `FRONTEND_URL` | `http://localhost:5173` | Frontend origin for CORS |
| `AI_MODE` | `mock` | `mock` or `real` |
| `MODEL_PATH` | (empty) | Path to trained model files (required when `AI_MODE=real`) |

### Frontend (`frontend/.env`)

| Variable | Default | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend URL |
| `VITE_DEMO_MODE` | `false` | Set `true` for offline demo |

## AI Mode

**`AI_MODE=mock`** (default) — returns deterministic mock results. No GPU, no model downloads, no HuggingFace. Works on any machine.

**`AI_MODE=real`** — loads a trained model from `MODEL_PATH`. Requires the model files to be placed locally.

### Adding a real model

1. Pull the repository
2. Place your trained model files in a local directory (e.g. `./model/`)
3. Set in `backend/.env`:
   ```
   AI_MODE=real
   MODEL_PATH=./model/
   ```
4. Implement inference in `ai_service/real_service.py` — the `RealAIService.analyze()` method
5. Restart the backend

The frontend, API endpoints, database schema, and response format remain unchanged.

## Project Structure

```
SatQuery/
├── frontend/          React + Vite (port 5173)
├── backend/           FastAPI + PostgreSQL (port 8000)
├── ai_service/        AI interface + mock + real placeholder
│   ├── base.py        Abstract AIService interface
│   ├── mock_service.py    Mock implementation (no model needed)
│   ├── real_service.py    Placeholder for trained model
│   └── factory.py     Selects service based on AI_MODE
├── docker-compose.yml
└── README.md
```

## What Your Friend Needs to Do

1. `git pull` the repository
2. Place trained model files locally
3. Set `AI_MODE=real` and `MODEL_PATH=/path/to/model/` in `backend/.env`
4. Implement `ai_service/real_service.py` — fill in the `analyze()` method
5. Run with Docker or manually — frontend and API remain identical
