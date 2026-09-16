# SatQuery AI ???

SatQuery AI is a cutting-edge multimodal AI platform designed for advanced geospatial analysis and remote sensing. Built specifically for ISRO's SIH 2024 problem statement, SatQuery acts as an intelligent assistant capable of understanding, analyzing, and annotating satellite imagery in real-time through natural language queries.

## ?? Key Features

* **Conversational AI Analysis:** Ask complex questions about satellite imagery (e.g., "Identify water bodies and built-up areas") and receive highly structured, ChatGPT-style detailed textual responses.
* **Intelligent Visual Grounding:** The AI doesn't just describe what it sees—it draws bounding boxes to precisely locate features in the image, rendering them in a beautiful side-by-side interactive viewer.
* **Geospatial Awareness:** Natively parses GeoTIFF metadata (CRS, bounds, resolution, and bands) and injects this context directly into the AI's prompt for spatially-aware reasoning.
* **Dynamic Accuracy Metrics:** Real-time generation of model confidence scores to reflect the AI's certainty based on image complexity and prompt instructions.
* **Multi-Turn Context:** The platform remembers active images across a chat session, allowing you to ask follow-up questions without re-uploading the data.

## ??? Tech Stack

**Frontend:**
* React (Vite)
* Tailwind CSS (Custom thematic styling for geospatial dark mode)
* Lucide React (Icons)
* Leaflet (Geospatial mapping)

**Backend:**
* FastAPI (High-performance Python web framework)
* Uvicorn (ASGI server)
* Rasterio (Geospatial metadata extraction)
* PyTorch & HuggingFace Transformers (AI Inference)
* Qwen2.5-VL-3B-Instruct (Fine-tuned Base Vision-Language Model)
* PEFT / LoRA (Low-Rank Adaptation for domain-specific satellite training)

## ?? Getting Started

### Prerequisites
* Python 3.10+
* Node.js 18+
* CUDA-compatible GPU (Recommended for fast inference)

### 1. Start the Backend Server
`ash
cd backend
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python -m uvicorn app.main:app --port 4000
`

### 2. Start the Frontend Server
`ash
cd frontend
npm install
npm run dev
`

### 3. Access the Application
Open your browser and navigate to http://localhost:2000. You can log in using any dummy credentials, upload a satellite image, and start asking queries!

## ?? Model Training & Architecture

Our architecture utilizes a heavily fine-tuned Qwen2.5-VL model adapted using LoRA specifically for ISRO's remote sensing datasets. By injecting dynamic Rasterio headers into the context window, the model bridges the gap between raw pixel data (RGB/SAR) and geospatial reality (Coordinates, CRS).

---
*Built with ?? for ISRO and the SIH Hackathon.*
