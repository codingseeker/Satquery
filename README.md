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
# SatQuery

SatQuery is an experimental vision-language model for remote sensing. We fine-tuned `Qwen2.5-VL-3B-Instruct` to answer questions about satellite imagery, specifically focusing on identifying land cover, answering binary questions, and doing basic bounding box localization.

The model was trained entirely on a local RTX 3050 (6GB VRAM) laptop using 4-bit QLoRA.

## Dataset

We use a subset of the **BigEarthNet v2.0** dataset (specifically the Lithuania Summer split). 

The raw data consists of Sentinel-1 (SAR) and Sentinel-2 (Multispectral) patches stored in LMDB format. We extract the optical RGB bands and map them to text-based question-and-answer pairs across four tasks:
- `binary`: Yes/no questions about terrain features.
- `mcq`: Multiple-choice land cover classification.
- `captioning`: Detailed summarization of the landscape.
- `bounding box`: Localizing specific features.

## Project Layout

```
satquery-ai-service/
└── satai/
    ├── README.md
    └── training/
        ├── data/
        │   ├── images/       # LMDB files and extracted S1/S2 PNG/NPY patches
        │   ├── metadata/     # Raw BigEarthNet annotations
        │   └── processed/    # HuggingFace DatasetDict and JSONL files
        ├── models/
        │   ├── qwen25vl/           # Base model weights
        │   └── satquery-best-lora/ # The trained LoRA adapter
        ├── outputs/          # Logs and evaluation results
        └── scripts/          
            ├── extract_matching_pixels.py  # Unpacks LMDB to images
            ├── build_qwen_dataset.py       # Builds the conversational format
            ├── train.py                    # The QLoRA training loop
            ├── improve_satquery.py         # Modified training loop for better loss
            └── evaluate_satquery.py        # Runs inference on the dev set
```

## Results

On our held-out development set, the best checkpoint (`satquery-best-lora`, Epoch 5) achieved:
- **Dev Loss:** 0.4379
- **Exact Match:** 40.0%

*Note on the metric:* Exact match is a very strict string-matching metric. If the model outputs "The image shows a forest." and the ground truth is "This image shows a forest.", it counts as a failure. Qualitatively, the model has learned to identify land features quite well.

## Setup & Usage

### 1. Requirements
You'll need Python 3.11+ and a CUDA-capable GPU. Install the standard HuggingFace stack:
`pip install torch transformers peft bitsandbytes datasets qwen_vl_utils`

### 2. Running Evaluation
To test the trained adapter against the dev set:
```bash
python training/scripts/evaluate_satquery.py --dev
```

### 3. Inference (Loading the model)
If you want to plug the adapter into your own inference script, load the base model in 4-bit and apply the PEFT adapter:

```python
import torch
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration, BitsAndBytesConfig
from peft import PeftModel

# Load processor and base model
processor = AutoProcessor.from_pretrained("Qwen/Qwen2.5-VL-3B-Instruct")
base_model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2.5-VL-3B-Instruct", 
    quantization_config=BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16), 
    device_map="auto"
)

# Apply our trained LoRA
model = PeftModel.from_pretrained(base_model, "training/models/satquery-best-lora")

print("Ready for inference!")
```
