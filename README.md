# SatQuery AI 🛰️

SatQuery AI is a cutting-edge multimodal AI platform designed for advanced geospatial analysis and remote sensing. Built specifically for ISRO's SIH 2024 problem statement, SatQuery acts as an intelligent assistant capable of understanding, analyzing, and annotating satellite imagery in real-time through natural language queries.

## 📸 Working Model Screenshots

*(Add your screenshots here before pushing to GitHub!)*

![Chat Interface](dummy_sat.png)  
*Example: Conversational AI interface analyzing satellite imagery.*

![Side-by-side Viewer](dummy_sat.png)  
*Example: Intelligent visual grounding and bounding box annotations.*

## 🌟 Key Features

* **Conversational AI Analysis:** Ask complex questions about satellite imagery (e.g., "Identify water bodies and built-up areas") and receive highly structured, ChatGPT-style detailed textual responses.
* **Intelligent Visual Grounding:** The AI doesn't just describe what it sees—it draws bounding boxes to precisely locate features in the image, rendering them in a beautiful side-by-side interactive viewer.
* **Geospatial Awareness:** Natively parses GeoTIFF metadata (CRS, bounds, resolution, and bands) and injects this context directly into the AI's prompt for spatially-aware reasoning.
* **Dynamic Accuracy Metrics:** Real-time generation of model confidence scores to reflect the AI's certainty based on image complexity and prompt instructions.
* **Multi-Turn Context:** The platform remembers active images across a chat session, allowing you to ask follow-up questions without re-uploading the data.

## 🛠️ Tech Stack & Libraries Used

Here is a detailed breakdown of every major library powering the SatQuery AI engine:

| Component | Library / Tech | Why it is used in SatQuery AI |
| :--- | :--- | :--- |
| **Frontend Core** | React & Vite | Powers the extremely fast, dynamic user interface and manages conversational state without page reloads. |
| **Styling** | Tailwind CSS | Provides the sleek, modern dark-mode UI specifically themed for geospatial analysis environments. |
| **Icons & UI** | Lucide React | Supplies the clean, professional iconography used throughout the chat and image viewer. |
| **Mapping** | Leaflet | Handles the interactive geospatial map viewer for plotting coordinates and evaluating broad terrain context. |
| **Backend Core** | FastAPI | The high-performance Python framework that handles asynchronous AI generation and API endpoints. |
| **Server** | Uvicorn | Runs the FastAPI application seamlessly to handle multiple concurrent hackathon queries. |
| **Geospatial Processing** | Rasterio | Extracts deep metadata (CRS, bounds, bands) directly from uploaded GeoTIFFs to inject spatial context into the AI prompt. |
| **Database** | SQLite & SQLAlchemy | Persistently stores user conversational history and analysis results locally. |
| **Machine Learning Core** | PyTorch | The foundational tensor framework running the entire neural network and Vision-Language Model. |
| **Model Architectures** | HuggingFace Transformers | Loads and runs the Qwen2.5-VL model architectures and the specialized multimodal tokenizers. |
| **Base AI Model** | Qwen2.5-VL-3B | A powerful 3-Billion parameter Vision-Language Model that natively understands complex spatial prompts and imagery. |
| **Fine-Tuning** | PEFT (LoRA) | Applies Low-Rank Adaptation to allow our model to specialize in ISRO satellite data without requiring massive VRAM. |
| **Hardware Acceleration**| Accelerate & BitsAndBytes | Enables 4-bit quantization, allowing the massive AI model to run incredibly fast on standard consumer GPUs. |

## 🚀 Getting Started

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

## 🧠 Model Training & Architecture

Our architecture utilizes a heavily fine-tuned Qwen2.5-VL model adapted using LoRA specifically for ISRO's remote sensing datasets. By injecting dynamic Rasterio headers into the context window, the model bridges the gap between raw pixel data (RGB/SAR) and geospatial reality (Coordinates, CRS).

---
*Built with ❤️ for ISRO and the SIH Hackathon.*
