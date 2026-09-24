# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HTTP_PROXY= \
    HTTPS_PROXY= \
    ALL_PROXY= \
    http_proxy= \
    https_proxy= \
    all_proxy= \
    NO_PROXY=* \
    no_proxy=* \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# Install dependencies separately so this layer is reused when only application
# source changes. The OCI sandbox preview SDK is deliberately not installed here:
# it must be supplied from Oracle's private distribution when that feature is used.
COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY app.py run.py ./
COPY services ./services

RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8501

CMD ["python", "run.py", "--server.headless=true"]
