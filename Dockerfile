# persona-bot — pinned slim base (multi-arch: amd64/arm64 via official python images)
# syntax=docker/dockerfile:1.7
FROM python:3.11.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_LINK_MODE=copy \
    # Persist fastembed/HF caches on a volume (see docker-compose).
    HF_HOME=/cache/huggingface \
    FASTEMBED_CACHE_PATH=/cache/fastembed \
    XDG_CACHE_HOME=/cache \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501

WORKDIR /app

# System deps for chromadb / onnxruntime wheels on slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv (pinned installer channel; resolves platform wheels)
COPY --from=ghcr.io/astral-sh/uv:0.6.14 /uv /usr/local/bin/uv

# Non-root user
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin appuser \
    && mkdir -p /app /data /cache/huggingface /cache/fastembed \
    && chown -R appuser:appuser /app /data /cache

# Project metadata first for better layer caching
COPY --chown=appuser:appuser pyproject.toml uv.lock README.md LICENSE ./
COPY --chown=appuser:appuser persona_bot ./persona_bot
COPY --chown=appuser:appuser personas ./personas
COPY --chown=appuser:appuser .streamlit ./.streamlit
COPY --chown=appuser:appuser persona_bot/static ./persona_bot/static

USER appuser

# Install package (no dev extras in image)
RUN uv sync --frozen --no-dev \
    && uv pip install -e .

EXPOSE 8501

# Examples stay in the image (read-only). Runtime data + caches are volumes.
VOLUME ["/data", "/cache"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8501/_stcore/health || exit 1

CMD ["uv", "run", "streamlit", "run", "persona_bot/main.py", \
     "--browser.gatherUsageStats=false", \
     "--server.address=0.0.0.0", \
     "--server.port=8501"]
