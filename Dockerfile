FROM python:3.11-slim

WORKDIR /app

# システム依存関係
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    libportaudio2 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 依存関係
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーション
COPY backend/ ./backend/
COPY frontend/dist/ ./frontend/dist/
COPY config/ ./config/

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
