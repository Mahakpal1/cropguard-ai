# Build from the repository root:  docker build -f backend/Dockerfile -t cropguard .
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend backend
COPY cv cv
COPY contracts contracts
COPY knowledge_base knowledge_base
COPY frontend frontend
ENV MODEL_DIR=/models DB_PATH=/data/cropguard.db
RUN mkdir -p /models /data
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
