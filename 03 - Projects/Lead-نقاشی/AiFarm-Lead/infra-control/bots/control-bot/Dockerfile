FROM python:3.12-slim

WORKDIR /app

# System deps (pyyaml needs gcc on some platforms)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .

# Non-root user for security
RUN useradd -m -u 1001 botuser
USER botuser

CMD ["python", "-u", "bot.py"]
