FROM python:3.11-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir torch==2.4.1 torchaudio==2.4.1 --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir demucs==4.0.1 fastapi==0.115.6 uvicorn==0.34.0
ENV TORCH_HOME=/models/torch
RUN python -c "from demucs.pretrained import get_model; get_model('htdemucs')"
WORKDIR /app
COPY server.py /app/server.py
ENV PORT=5000 PYTHONUNBUFFERED=1
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT:-5000}/healthz" || exit 1
CMD ["python", "server.py"]
