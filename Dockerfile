FROM python:3.11-slim

# System deps (ffmpeg for local rendering)
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install backend deps
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend code
COPY backend backend

# FastAPI app
ENV PYTHONPATH=/app/backend
EXPOSE 8000
# Render sets $PORT in the container; default to 8000 for local runs
CMD ["sh","-c","uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]