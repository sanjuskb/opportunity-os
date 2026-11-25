# NexteRaS ML Inference Container (Proposed for Google Cloud Run / Isolated CPU Worker)
# Does NOT embed model weights into Git or Docker build context unless pre-cached at deploy time.
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    HF_HOME=/var/cache/huggingface \
    TOKENIZERS_PARALLELISM=false \
    TORCH_NUM_THREADS=4 \
    ML_MAX_LOADED_MODELS=1

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.15.0+cpu

COPY ml/requirements.txt ./ml/requirements.txt
RUN pip install --no-cache-dir -r ml/requirements.txt

COPY ml ./ml
COPY apps/api/app/ml ./apps/api/app/ml

# Lightweight offline sanity readiness probe (zero HF weight download during build)
RUN python -c "from ml.src.integration.fastapi_adapter import NexteRaSMLService; svc = NexteRaSMLService(); assert svc.health_and_readiness().status == 'healthy'"

# Default verification / worker command; Cloud Run API sidecar mounts NexteRaSMLService cleanly
CMD ["python", "-m", "pytest", "ml/tests", "-q"]
