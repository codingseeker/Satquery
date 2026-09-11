# SatQuery AI - ISRO Remote Sensing Bot

SatQuery AI is a comprehensive full-stack solution built for the Smart India Hackathon (SIH 2026) for ISRO problem statement **SIH26167**. 

It allows users to interactively query satellite imagery via a modern React interface, powered by a custom-trained Vision-Language AI model (\Qwen2.5-VL\ with a locally fine-tuned LoRA adapter).

## System Architecture

- **Frontend:** React + Vite (runs on port 2000)
- **Backend:** FastAPI + SQLite (runs on port 4000)
- **AI Service:** Integrated directly into the backend, utilizing \	ransformers\, \peft\, and \itsandbytes\ to serve the \satquery-best-lora\ weights directly in 4-bit precision.

## Running the Application Locally

Since this setup utilizes large model caches and local weights, the application runs via Python scripts (Docker is not required).

### 1. Requirements

- Python 3.11+
- Node.js & npm
- A CUDA-capable GPU (Nvidia RTX 3050+ recommended for local inference)

### 2. Start the Backend API (Port 4000)

Open a terminal and run the FastAPI server:

\\powershell
cd backend
python -m venv .venv
.\.venv\Scriptsctivate
pip install -r requirements.txt
python -m uvicorn app.main:app --port 4000
\*Note: The backend uses a local SQLite file (\satquery.db\). No PostgreSQL server is required.*

### 3. Start the Frontend UI (Port 2000)

Open a second terminal and run the React application:

\\powershell
cd frontend
npm install
npm run dev
\
Visit **http://localhost:2000** in your browser.

## Custom Trained AI Pipeline

The system uses the \Qwen2.5-VL-3B-Instruct\ base model fine-tuned on the BigEarthNet dataset using QLoRA.
- The training scripts and data preparation routines are located in \	raining/scripts/\.
- The locally trained adapter (\satquery-best-lora\) successfully handles complex spatial distributions, identifies coastlines, vegetation, water bodies, and handles conversational multi-turn AI interactions cleanly.
- The \AI_MODE\ in \ackend/ai_service/real_service.py\ has been fully wired up. The AI automatically detects markdown, structures plain text for the frontend UI, and parses Qwen \<box>\ tags into visual bounding boxes!

## Evaluation Metrics (SatQuery LoRA vs Base)

Based on our validation dataset (	raining/outputs/satquery_evaluation.json), the SatQuery LoRA adapter achieves the following accuracy scores against the remote sensing benchmark:

| Task Type | Total Examples | Exact Match Rate |
| --- | --- | --- |
| **Binary Classification** | 10 | 60.0% |
| **VQA / Captioning** | 3 | 33.3% |
| **Multiple Choice** | 3 | 33.3% |
| **Overall Accuracy** | 20 | **40.0%** |

*Note: The model runs locally in 4-bit precision via BitsAndBytes, ensuring fast inference while preserving remote sensing intelligence.*

