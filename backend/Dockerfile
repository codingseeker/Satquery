FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN mkdir -p /app/uploads

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY backend/ai_service ./ai_service

ENV DATABASE_URL=postgresql://satquery:satquery@db:5432/satquery \
    UPLOAD_DIR=/app/uploads \
    FRONTEND_URL=http://localhost:2000 \
    AI_MODE=real \
    MODEL_PATH=training/models/satquery-best-lora

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
