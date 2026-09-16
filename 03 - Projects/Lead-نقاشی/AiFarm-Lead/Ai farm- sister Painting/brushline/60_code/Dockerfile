FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY src/ ./src/
COPY Makefile .

# Data directory (audit logs, kill switch, etc.)
RUN mkdir -p /app/data && chmod 777 /app/data

# Non-root user
RUN useradd -m -u 1001 brushline && chown -R brushline:brushline /app
USER brushline

# Health check: verify main Python process is importable and config is loadable
# (Telegram bot — no HTTP port, process-based health)
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "from src.config import config; v = config.validate(); exit(0 if not v else 1)" \
    || exit 1

# Environment (secrets injected at runtime via .env or env vars)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["python", "-u", "main.py"]
