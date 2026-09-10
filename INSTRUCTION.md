# INSTRUCTION.md — Complete Run + Wiring Guide for SatQuery AI

This document explains, in full detail, how to understand, run, and develop against this project. It is written so that someone who just cloned the repository can get the app running immediately.

---

## 1. PREREQUISITES

| Tool | Version | Notes |
|------|---------|-------|
| **Python** | 3.12+ | Backend and AI service. Docker uses `python:3.12-slim`. |
| **Node.js** | 20+ | Frontend build and dev server. Docker uses `node:20-alpine`. |
| **npm** | (bundled with Node) | Used to install frontend dependencies. |
| **PostgreSQL** | 16 | Database. Docker provides this automatically; manual setup needs a local PostgreSQL. |
| **Docker** | (optional) | For the one-command `docker compose up` workflow. |
| **Docker Compose** | (optional) | Orchestrates the three containers. |

**You do NOT need:** Qwen, LORE, GPU, HuggingFace, or any AI model files. The default setup uses `AI_MODE=mock` which requires zero model dependencies.

---

## 2. PROJECT STRUCTURE

```
satquery/
├── frontend/               React + Vite app (port 5173 dev, port 80 in Docker)
│   ├── src/
│   │   ├── main.jsx              App entry point (login + main layout)
│   │   ├── SatelliteViewer.jsx   Leaflet map + satellite image viewer
│   │   ├── styles.css            Full stylesheet (Tailwind)
│   │   ├── config/env.js         Reads VITE_* env vars into a config object
│   │   ├── services/
│   │   │   ├── api.js            Base HTTP client (fetch wrapper, auth headers, timeout)
│   │   │   ├── chatService.js    Conversation + query + report API functions
│   │   │   └── imageService.js   Image upload/metadata/delete API functions
│   │   ├── components/
│   │   │   ├── layout/           Sidebar, Header
│   │   │   ├── chat/             WelcomeScreen, MessageList, Message, Composer
│   │   │   ├── image/            ImageUploadZone, FileCard
│   │   │   ├── results/          AnalysisResult, ConfidenceBadge, ExecutionSummary
│   │   │   └── settings/         SettingsPanel (ChatGPT-style, 7 pages)
│   │   └── utils/                constants.js, fileUtils.js
│   ├── nginx.conf                Production reverse proxy config
│   ├── Dockerfile                Multi-stage: node build → nginx serve
│   ├── package.json              npm scripts: dev, build, preview
│   └── vite.config.js            Vite dev server on port 5173
│
├── backend/                FastAPI REST API (port 8000)
│   ├── app/
│   │   ├── main.py               FastAPI app entry point, CORS, router registration
│   │   ├── config.py             Pydantic Settings — reads .env
│   │   ├── database.py           SQLAlchemy engine, session, Base
│   │   ├── models/               ORM models: User, Chat, Analysis, Image
│   │   ├── schemas/              Pydantic request/response schemas
│   │   ├── routers/              API route handlers (auth, chats, analysis, users, images, query, reports)
│   │   ├── services/             Business logic (auth, analysis, file handling)
│   │   └── utils/                JWT security, FastAPI dependencies
│   ├── uploads/                  Runtime storage for user-uploaded files (by user ID)
│   ├── requirements.txt          Python dependencies
│   ├── .env.example              Template env file
│   └── Dockerfile                Python 3.12-slim + uvicorn
│
├── ai_service/             Standalone Python AI module (copied into backend container)
│   ├── base.py                   Abstract AIService interface
│   ├── mock_service.py           MockAIService — deterministic, no model needed
│   ├── real_service.py           RealAIService — placeholder for trained model
│   ├── qwen_placeholder.py       Template for Qwen-based service (unused)
│   └── factory.py                Selects mock vs real based on AI_MODE env var
│
├── storage/                External storage (empty by default, gitignored)
│   ├── results/
│   └── uploads/
│
├── docker-compose.yml      Orchestrates db, backend, frontend containers
└── INSTRUCTION.md          This file
```

### What each directory does

| Directory | Purpose |
|-----------|---------|
| `frontend/` | React SPA. ChatGPT-style UI for satellite image analysis. Connects to backend API. |
| `backend/` | FastAPI REST server. Handles auth, file uploads, analysis orchestration, database CRUD. |
| `ai_service/` | Pluggable AI module. Factory pattern selects MockAIService or RealAIService based on `AI_MODE`. No GPU required for mock mode. |
| `storage/` | Optional external storage directory. Not used by default; gitignored. |

---

## 3. ENVIRONMENT VARIABLES

### Backend (`backend/.env`)

Create this file by copying the template:

```bash
cp backend/.env.example backend/.env
```

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://satquery:satquery@localhost:5432/satquery` | PostgreSQL connection string |
| `JWT_SECRET_KEY` | `change-me-in-production` | Secret for signing JWT tokens |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token expiry in minutes |
| `UPLOAD_DIR` | `./uploads` | Where uploaded images are stored on disk |
| `MAX_UPLOAD_SIZE_MB` | `50` | Max upload size in megabytes |
| `FRONTEND_URL` | `http://localhost:5173` | Frontend origin for CORS allowlist |
| `AI_MODE` | `mock` | `mock` (no model) or `real` (trained model required) |
| `MODEL_PATH` | (empty) | Path to model files on disk. Required only when `AI_MODE=real` |

**Safe example (`backend/.env`):**

```env
DATABASE_URL=postgresql://satquery:satquery@localhost:5432/satquery
JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=50
FRONTEND_URL=http://localhost:5173
AI_MODE=mock
MODEL_PATH=
```

> **Never put real secrets, production database URLs, or API keys in the repository.**

### Frontend (`frontend/.env`)

Create this file by copying the template:

```bash
cp frontend/.env.example frontend/.env
```

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend API base URL |
| `VITE_DEMO_MODE` | `false` | `true` for offline demo mode (mock data, no API calls) |
| `VITE_APP_VERSION` | `1.0.0` | Display version in UI |
| `VITE_MAX_FILE_SIZE_MB` | `500` | Max file size for upload validation (client-side) |
| `VITE_REQUEST_TIMEOUT_MS` | `120000` | Request timeout in milliseconds (default 2 min) |

**Safe example (`frontend/.env`):**

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_DEMO_MODE=false
VITE_APP_VERSION=1.0.0
VITE_MAX_FILE_SIZE_MB=500
VITE_REQUEST_TIMEOUT_MS=120000
```

---

## 4. STARTING THE PROJECT WITHOUT DOCKER

### Step 1: Start PostgreSQL

If PostgreSQL is installed locally, create the database:

```sql
CREATE USER satquery WITH PASSWORD 'satquery';
CREATE DATABASE satquery OWNER satquery;
```

If PostgreSQL runs on a non-default port or host, update `DATABASE_URL` in `backend/.env` accordingly.

### Step 2: Start the backend (Terminal 1)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # skip if .env already exists
uvicorn app.main:app --reload --port 8000
```

The backend will:
1. Read `backend/.env` via pydantic-settings
2. Create the `uploads/` directory if missing
3. Auto-create all database tables via SQLAlchemy `Base.metadata.create_all()`
4. Start serving on `http://localhost:8000`

Verify: `curl http://localhost:8000/health` should return `{"status":"ok","database":"connected"}`

API docs available at: `http://localhost:8000/docs`

### Step 3: Start the frontend (Terminal 2)

```bash
cd frontend
npm install
npm run dev
```

Vite dev server starts on `http://localhost:5173` and proxies API calls to `http://localhost:8000`.

### Step 4: Open the app

Navigate to `http://localhost:5173` in your browser.

---

## 5. STARTING WITH DOCKER

### One command:

```bash
docker compose up --build
```

This starts three containers:

| Container | Service | Image | Port Mapping | Description |
|-----------|---------|-------|-------------|-------------|
| `satquery-db` | `db` | `postgres:16-alpine` | `5433:5432` | PostgreSQL database |
| `satquery-backend` | `backend` | Custom (Python 3.12-slim) | `8000:8000` | FastAPI backend |
| `satquery-frontend` | `frontend` | Custom (nginx:alpine) | `5173:80` | React app served by nginx |

### Container startup order:

1. `db` starts first. Healthcheck runs `pg_isready -U satquery` every 5s.
2. `backend` starts after `db` is healthy. Uses `DATABASE_URL=postgresql://satquery:satquery@db:5432/satquery` (Docker network DNS).
3. `frontend` starts after `backend` is healthy.

### What Docker sets automatically:

- `AI_MODE=mock` (no real AI model)
- `DATABASE_URL` points to the `db` container (not localhost)
- `UPLOAD_DIR=/app/uploads` inside the container, mounted from `./backend/uploads` on the host

### Exposed ports:

- `http://localhost:5173` — Frontend (nginx serves built React app, proxies `/api/*` to backend)
- `http://localhost:8000` — Backend API directly (for Postman, curl, API docs at `/docs`)
- `localhost:5433` — PostgreSQL (if you need direct DB access)

### Nginx routing (production):

Nginx in the frontend container handles:
- `/` → serves static React files from `/usr/share/nginx/html`
- `/api/*` → reverse proxies to `http://backend:8000`
- `/health` → reverse proxies to `http://backend:8000`
- `client_max_body_size 50M` for file uploads

---

## 6. COMPLETE REQUEST FLOW

### Overview

```
Browser (http://localhost:5173)
    ↓
Frontend (React + Vite)
    ↓ HTTP requests (fetch API, Bearer token in Authorization header)
Backend API (FastAPI, port 8000)
    ↓
PostgreSQL (data persistence)
    ↓
AI Service (MockAIService or RealAIService)
    ↓
Backend response (JSON)
    ↓
Frontend (React renders result)
    ↓
Browser (user sees analysis result)
```

### What happens when the user logs in

1. User enters email + password in the `LoginPage` component (`frontend/src/main.jsx`)
2. Frontend sends `POST /api/auth/login` with `{email, password}`
3. Backend `auth.py::login` validates credentials against bcrypt hash in the `users` table
4. Backend returns `{access_token, token_type, user: {id, email}}`
5. Frontend stores `access_token` in `localStorage` as `satquery_token`
6. Frontend re-renders, now showing the main app layout (Sidebar + Chat area)
7. All subsequent requests include `Authorization: Bearer <token>` header

### What happens when the user uploads an image

1. User drags an image onto the `ImageUploadZone` or clicks the attach button in `Composer`
2. Frontend `imageService.js::uploadImage(file, onProgress)` creates a `FormData` with the file
3. Frontend sends `POST /api/images/upload` (multipart form data, Bearer token)
4. Backend `images.py::upload_image` validates file type and size
5. Backend saves the file to `uploads/images/{user_id}/{stored_filename}`
6. Backend creates an `Image` record in the database
7. Backend returns `{image_id, metadata: {filename, content_type, file_size, ...}}`
8. Frontend displays the file as a `FileCard` in the Composer area

### What happens when the user asks a question

1. User types a question in `Composer` and optionally attaches images
2. Frontend `chatService.js::sendQuery({conversationId, query, imageIds})` is called
3. Frontend sends `POST /api/query` with `{conversation_id, query, image_ids}`
4. Backend `query.py::handle_query`:
   a. Validates the conversation exists and belongs to the user
   b. Resolves image paths from `image_ids` if provided
   c. Calls `get_ai_service().analyze(image_path, query)` — this goes through `ai_service/factory.py`
   d. Factory reads `AI_MODE` env var and returns either `MockAIService` or `RealAIService`
   e. The AI service processes the image + query and returns a result dict
   f. Backend saves an `Analysis` record to the database with the result
   g. Backend returns the full analysis as JSON
5. Frontend `chatService.js` normalizes the response via `adaptAnalysisResponse()`
6. Frontend `Message.jsx` renders the assistant's response with `AnalysisResult`, `ConfidenceBadge`, `ExecutionSummary`

### What happens when the user receives an analysis

The `AnalysisResult` component renders:
- **Answer text** — the natural language response from the AI
- **Task type** — "Water Detection", "Built-up Detection", "Change Detection", or "Scene Understanding"
- **Confidence badge** — shows percentage with a color-coded bar
- **Stats** — key metrics like built-up area, vegetation area, water area
- **Regions** — detected regions with labels and types
- **Execution summary** — expandable panel showing task detected, tools used, input type, duration
- **Map** — Leaflet map centered on the analysis location (Bengaluru in mock mode)

### What happens when the user opens conversation history

1. User clicks a conversation in the `Sidebar`
2. Frontend `chatService.js::getConversation(conversationId)` sends `GET /api/conversations/{conv_id}`
3. Backend `query.py::get_conversation` fetches the chat and all its analyses from the database
4. Backend returns `{id, title, messages: [{role, content, analysis, timestamp}, ...]}`
5. Frontend `MessageList.jsx` renders each message pair (user query + assistant response)
6. The conversation state is restored in the UI

---

## 7. API WIRING

This section documents every frontend service function and which backend endpoint it calls. All endpoints require a `Authorization: Bearer <token>` header unless noted.

### `frontend/src/services/api.js` — Base HTTP client

| Method | Description |
|--------|-------------|
| `api.get(path)` | `GET {baseUrl}{path}` with Bearer token |
| `api.post(path, body)` | `POST {baseUrl}{path}` with JSON body and Bearer token |
| `api.delete(path)` | `DELETE {baseUrl}{path}` with Bearer token |
| `api.postFormData(path, formData)` | `POST {baseUrl}{path}` with FormData (no Content-Type header — browser sets multipart boundary) |
| `api.ping()` | `GET /health` — returns `true` or `false` |

### `frontend/src/services/chatService.js` — Conversation + query management

| Function | Backend Endpoint | Request Body |
|----------|-----------------|--------------|
| `sendQuery({conversationId, query, imageIds})` | `POST /api/query` | `{conversation_id, query, image_ids}` |
| `getConversation(conversationId)` | `GET /api/conversations/{conversationId}` | — |
| `listConversations()` | `GET /api/conversations` | — |
| `deleteConversation(conversationId)` | `DELETE /api/conversations/{conversationId}` | — |
| `requestReport(conversationId, analysisId)` | `POST /api/reports` | `{conversation_id, analysis_id}` |
| `checkBackendHealth()` | `GET /health` | — |

### `frontend/src/services/imageService.js` — Image upload/management

| Function | Backend Endpoint | Request Body |
|----------|-----------------|--------------|
| `uploadImage(file, onProgress)` | `POST /api/images/upload` | FormData with `file` field |
| `getImageMetadata(imageId)` | `GET /api/images/{imageId}/metadata` | — |
| `deleteImage(imageId)` | `DELETE /api/images/{imageId}` | — |

### `frontend/src/main.jsx` — Auth + chat creation (inline calls)

| Action | Backend Endpoint | Request Body |
|--------|-----------------|--------------|
| Login | `POST /api/auth/login` | `{email, password}` |
| Register | `POST /api/auth/register` | `{email, password}` |
| Create new chat | `POST /api/chats` | `{title}` |
| List conversations (sidebar init) | `GET /api/conversations` | — |

### Complete backend endpoint reference

| Method | Endpoint | Handler | Description |
|--------|----------|---------|-------------|
| `POST` | `/api/auth/register` | `routers/auth.py` | Register new user |
| `POST` | `/api/auth/login` | `routers/auth.py` | Login, returns JWT |
| `GET` | `/api/auth/me` | `routers/auth.py` | Get current user info |
| `POST` | `/api/auth/logout` | `routers/auth.py` | Logout (client removes token) |
| `GET` | `/api/users/me` | `routers/users.py` | Get current user info |
| `POST` | `/api/chats` | `routers/chats.py` | Create a new chat |
| `GET` | `/api/chats` | `routers/chats.py` | List user's chats |
| `GET` | `/api/chats/{chat_id}` | `routers/chats.py` | Get a specific chat |
| `GET` | `/api/chats/{chat_id}/analyses` | `routers/chats.py` | List analyses for a chat |
| `DELETE` | `/api/chats/{chat_id}` | `routers/chats.py` | Delete a chat + its analyses |
| `POST` | `/api/analysis` | `routers/analysis.py` | Create analysis with file upload (Form data) |
| `GET` | `/api/analysis/{analysis_id}` | `routers/analysis.py` | Get analysis result |
| `DELETE` | `/api/analysis/{analysis_id}` | `routers/analysis.py` | Delete analysis + file |
| `GET` | `/api/analysis/{analysis_id}/file` | `routers/analysis.py` | Download the uploaded image |
| `POST` | `/api/images/upload` | `routers/images.py` | Upload an image |
| `GET` | `/api/images/{image_id}/metadata` | `routers/images.py` | Get image metadata |
| `DELETE` | `/api/images/{image_id}` | `routers/images.py` | Delete an image |
| `POST` | `/api/query` | `routers/query.py` | Send query, run AI, save result |
| `GET` | `/api/conversations` | `routers/query.py` | List user's conversations |
| `GET` | `/api/conversations/{conv_id}` | `routers/query.py` | Get conversation with messages |
| `DELETE` | `/api/conversations/{conv_id}` | `routers/query.py` | Delete a conversation |
| `POST` | `/api/reports` | `routers/reports.py` | Request a report download URL |
| `GET` | `/health` | `main.py` | Health check (DB connectivity) |

---

## 8. MOCK AI

### What `AI_MODE=mock` means

When `AI_MODE=mock` (the default), no real AI model is loaded. No GPU is needed. No files are downloaded from HuggingFace. The app works on any machine with Python installed.

### How a query travels through the system in mock mode

```
Frontend: sendQuery({conversationId, query: "Is there water in this area?", imageIds: ["42"]})
    ↓ POST /api/query
Backend: query.py::handle_query()
    ↓ validates conversation, resolves image path
    ↓ calls get_ai_service()
Backend: ai_service/factory.py::get_ai_service()
    ↓ reads os.environ.get("AI_MODE", "mock") → "mock"
    ↓ returns MockAIService()
Backend: query.py calls ai_service.analyze(image_path, query)
    ↓
AI Service: ai_service/mock_service.py::MockAIService.analyze()
    ↓ detects "water" in query → task = "Water Detection"
    ↓ returns deterministic dict (confidence: 0.87, hardcoded regions, Bengaluru map)
    ↓
Backend: saves Analysis record to database, returns JSON to frontend
    ↓
Frontend: adaptAnalysisResponse() normalizes the response
    ↓
Frontend: renders AnalysisResult with confidence badge, stats, regions, map
```

### What MockAIService returns

The mock service returns a fixed structure regardless of the input image:

```python
{
    "task": "Water Detection",        # Based on keywords in the query
    "status": "completed",
    "confidence": 0.87,
    "answer": "Mock analysis completed...",
    "stats": {"built_up": "42.8 ha", "vegetation": "31.2 ha", "water": "12.1 ha"},
    "regions": [
        {"id": 1, "label": "Region 01", "type": "vegetation"},
        {"id": 2, "label": "Region 02", "type": "built-up"},
        {"id": 3, "label": "Region 03", "type": "water"},
    ],
    "changes": [],
    "images": [],
    "metadata": {"source": "mock", "model": "placeholder", "image_path": "..."},
    "execution": {
        "task_detected": "Water Detection",
        "tools": ["MockAIService"],
        "input_type": "satellite_image",
        "status": "completed",
        "duration_ms": 42,
        "output_type": "analysis_report",
    },
    "map": {"center": [12.9716, 77.5946], "bounds": [[...], [...]]},
    "layers": {"optical": None, "sar": None, "changes": None},
}
```

### Task detection keywords

| Query contains | Detected task |
|----------------|---------------|
| "water" or "water body" | Water Detection |
| "built", "urban", or "built-up" | Built-up Detection |
| "change", "compare", or "two image" | Change Detection |
| anything else | Scene Understanding |

---

## 9. FUTURE REAL MODEL

### When you are ready to integrate a real trained model:

1. **Place your model files** in a local directory:
   ```bash
   mkdir -p model/
   # Copy your .safetensors, .bin, .pt, or .pth files into model/
   ```

2. **Update `backend/.env`:**
   ```env
   AI_MODE=real
   MODEL_PATH=./model/
   ```

3. **Implement inference in `ai_service/real_service.py`:**
   The `RealAIService` class already has the structure. You need to fill in the `analyze()` method:

   ```python
   class RealAIService(AIService):
       def __init__(self, model_path: str = ""):
           self.model_path = model_path
           self.model = None
           self._loaded = False

       def _load_model(self):
           if self._loaded:
               return
           if not os.path.exists(self.model_path):
               raise FileNotFoundError(f"Model not found at {self.model_path}")
           # TODO: Load your model here
           # self.model = YourModelClass.load(self.model_path)
           self._loaded = True

       def analyze(self, image_path: str, query: str, metadata=None) -> Dict[str, Any]:
           self._load_model()
           # TODO: Run inference here
           # return self.model.predict(image_path, query)
           raise NotImplementedError("Add your inference code here")
   ```

4. **Ensure the return format matches** what the backend expects. The result dict must include at minimum:
   - `task` (str) — detected analysis type
   - `status` (str) — "completed" or "failed"
   - `confidence` (float) — 0.0 to 1.0
   - `answer` (str) — natural language response
   - `stats` (dict) — key metrics
   - `regions` (list) — detected regions
   - `execution` (dict) — execution metadata

5. **Restart the backend.** The frontend, API endpoints, database schema, and response format remain unchanged.

### What stays the same

- All frontend components render the same way
- All API endpoints work identically
- The database schema does not change
- The response JSON format is the same
- Only the source of the analysis results changes (real model instead of mock)

### Adding new AI services

To add a new AI service (e.g., Qwen-based):

1. Create a new file in `ai_service/` (e.g., `qwen_service.py`)
2. Implement the `AIService` interface from `ai_service/base.py`
3. Add a new mode check in `ai_service/factory.py`:

   ```python
   def get_ai_service() -> AIService:
       mode = os.environ.get("AI_MODE", "mock").lower()
       if mode == "mock":
           return MockAIService()
       if mode == "real":
           # ... existing code
       if mode == "qwen":
           from ai_service.qwen_service import QwenAIService
           return QwenAIService(model_path=os.environ.get("MODEL_PATH", ""))
       raise ValueError(f"Unknown AI_MODE: {mode}")
   ```

4. Set `AI_MODE=qwen` in `backend/.env`
5. Restart the backend

---

## 10. DATABASE SCHEMA

Tables are auto-created at startup via `Base.metadata.create_all()`. No migration tool (Alembic) is configured.

### Tables

**users**
| Column | Type | Notes |
|--------|------|-------|
| id | Integer | Primary key |
| email | String(255) | Unique, indexed |
| password_hash | String(255) | bcrypt hash |
| created_at | DateTime | Default: utcnow |
| updated_at | DateTime | Auto-updated |

**chats**
| Column | Type | Notes |
|--------|------|-------|
| id | Integer | Primary key |
| user_id | Integer | FK → users.id, cascade delete |
| title | String(255) | Chat title |
| created_at | DateTime | Default: utcnow |
| updated_at | DateTime | Auto-updated |

**analyses**
| Column | Type | Notes |
|--------|------|-------|
| id | Integer | Primary key |
| chat_id | Integer | FK → chats.id, cascade delete |
| user_id | Integer | FK → users.id, cascade delete |
| query | Text | User's question |
| original_filename | String(255) | Original upload filename |
| stored_filename | String(255) | On-disk filename |
| task | String(255) | Detected task type |
| status | String(50) | "pending", "completed", "failed" |
| confidence | Float | 0.0 – 1.0 |
| answer | Text | Natural language answer |
| result_json | Text | Full AI result as JSON string |
| created_at | DateTime | Default: utcnow |
| completed_at | DateTime | When analysis finished |

**images**
| Column | Type | Notes |
|--------|------|-------|
| id | Integer | Primary key |
| user_id | Integer | FK → users.id, cascade delete |
| original_filename | String(255) | Original upload filename |
| stored_filename | String(255) | On-disk filename |
| content_type | String(100) | MIME type |
| file_size | Integer | Size in bytes |
| metadata_json | Text | Additional metadata as JSON |
| created_at | DateTime | Default: utcnow |

---

## 11. TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| Backend won't start: `ModuleNotFoundError: No module named 'ai_service'` | Make sure you're running uvicorn from the `backend/` directory and that `PYTHONPATH` includes the project root. In Docker, this is set automatically. |
| `psycopg2` install fails | Install PostgreSQL dev libraries: `sudo apt install libpq-dev` (Ubuntu) or use `pip install psycopg2-binary` (already in requirements.txt). |
| Frontend can't reach backend | Check that `VITE_API_BASE_URL` in `frontend/.env` matches the backend URL. In dev: `http://localhost:8000`. In Docker: nginx proxies automatically. |
| CORS errors | Ensure `FRONTEND_URL` in `backend/.env` matches the actual frontend origin (`http://localhost:5173`). |
| Database connection refused | Verify PostgreSQL is running and `DATABASE_URL` is correct. For Docker, the host is `db` (not `localhost`). |
| Port 5433 already in use | Change the host port in `docker-compose.yml` (e.g., `"5434:5432"`). |
| Upload fails with "File too large" | Check `MAX_UPLOAD_SIZE_MB` in `backend/.env` and `client_max_body_size` in `nginx.conf` (Docker). |
