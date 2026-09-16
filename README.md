# SatQuery AI

SatQuery AI is a multimodal AI platform built for ISRO's Smart India Hackathon 2024. It lets you upload satellite imagery and ask questions about it in plain English. The system analyzes the image using a fine-tuned Vision Language Model, draws bounding boxes around detected features, and shows the result in a side-by-side annotated viewer alongside a structured textual response.

The model runs entirely on-device without any external API calls to OpenAI, Gemini, or any other cloud AI service.


## Tech Stack

The project is split into two parts: a Python backend that handles AI inference and a React frontend that handles the user interface.

Backend is built with Python. Frontend is built with React using Vite as the build tool.


## Libraries Used

### Backend Libraries

| Library | Version | How it is used in SatQuery AI |
| --- | --- | --- |
| FastAPI | 0.115+ | Serves all the REST API endpoints. Handles image uploads, query processing, authentication, and conversation history. |
| Uvicorn | 0.34+ | Runs the FastAPI application as an ASGI server on port 4000. |
| SQLAlchemy | 2.0+ | Manages the database schema and all queries for users, conversations, and analysis results stored in SQLite. |
| PyJWT | 2.10+ | Creates and validates JSON Web Tokens used to authenticate users between the frontend and the backend. |
| bcrypt | 4.2+ | Hashes user passwords before storing them so plain-text passwords are never saved to the database. |
| python-multipart | 0.0.20+ | Parses the multipart form data when a user uploads a satellite image file through the browser. |
| python-dotenv | 1.0+ | Loads environment variables from the .env file so secrets like the JWT key are not hardcoded in source files. |
| pydantic | 2.11+ | Validates the shape and types of all incoming API request bodies and outgoing response objects. |
| Rasterio | 1.3+ | Opens GeoTIFF files to extract geospatial metadata including CRS, lat/lon bounds, resolution, and band count. This context is injected directly into the AI prompt. |
| PyTorch | 2.2+ | The core tensor computation framework that runs the entire neural network for the Vision Language Model inference. |
| Transformers (HuggingFace) | 4.40+ | Loads the Qwen2.5-VL-3B-Instruct model architecture and the multimodal processor that tokenizes both text and image inputs together. |
| PEFT | 0.10+ | Applies the trained LoRA adapter weights on top of the base Qwen2.5-VL model so the model specializes in satellite imagery without retraining all 3 billion parameters. |
| BitsAndBytes | 0.43+ | Loads the model in 4-bit NF4 quantization so it fits and runs on consumer GPUs that do not have enough VRAM for full precision. |
| Accelerate | 0.29+ | Handles device placement and memory management when loading the quantized model across available hardware. |
| qwen-vl-utils | 0.0.14 | Provides the process_vision_info utility that correctly prepares image tensors for the Qwen2.5-VL model's visual encoder. |
| NumPy | 2.4+ | Used inside the Rasterio pipeline to read band arrays and compute the NDVI index for vegetation analysis. |
| email-validator | 2.2+ | Validates that email addresses provided during user registration are properly formatted before saving to the database. |

### Frontend Libraries

| Library | Version | How it is used in SatQuery AI |
| --- | --- | --- |
| React | 18+ | Builds the entire user interface as reusable components including the chat window, image viewer, sidebar, and settings panel. |
| Vite | 6.4+ | Bundles and serves the React application with hot module replacement during development and optimized output for production. |
| Lucide React | Latest | Provides all the icons used throughout the interface such as the satellite icon, layer controls, zoom buttons, and action toolbar icons. |
| Tailwind CSS | 3+ | Used for base utility classes in the layout. The application also maintains a custom CSS file for the dark geospatial theme. |


## Project Structure

`
Satquery-Final-Production/
  backend/
    ai_service/         AI inference service, bounding box parser, and lat/lon extractor
    app/
      routers/          API route handlers for auth, images, queries, and users
      models/           SQLAlchemy database models
      schemas/          Pydantic request and response schemas
      services/         Business logic for analysis and file handling
  frontend/
    src/
      components/       React components for chat, image viewer, settings, and results
      services/         API client functions that call the backend
      utils/            File format helpers and timestamp formatters
  training/
    scripts/            Model training, evaluation, and inference scripts
    models/             Trained LoRA adapter weights stored here
`


## Getting Started

You need Python 3.10 or higher and Node.js 18 or higher installed. A CUDA-compatible GPU is strongly recommended because the model is large and will be very slow on CPU.

Clone the repository first.

`
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd Satquery-Final-Production
`

Start the backend.

`
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --port 4000
`

Start the frontend in a new terminal.

`
cd frontend
npm install
npm run dev
`

Open http://localhost:2000 in your browser. Create an account, upload a satellite image, and start querying.


## Model

The AI model is Qwen2.5-VL-3B-Instruct fine-tuned with LoRA on ISRO remote sensing datasets. The base model weights are downloaded from HuggingFace and the LoRA adapter is stored in training/models/satquery-best-lora. The adapter file is tracked with Git LFS because it is approximately 148 MB.

When you run a query, the backend extracts geospatial context from the image using Rasterio, appends it to your query, runs inference through the fine-tuned model, parses the bounding box coordinates from the output, converts them to real-world latitude and longitude using the image CRS, and returns the structured result to the frontend.


Built for ISRO and the SIH Hackathon.
