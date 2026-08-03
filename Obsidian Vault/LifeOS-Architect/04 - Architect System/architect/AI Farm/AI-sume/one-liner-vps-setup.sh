#!/bin/bash
# ============================================================================
# اجرایِ این خط **یک بار** روی VPS — تمام اتوماتیک
# ============================================================================
# صرفاً کپی-پیست این را روی VPS (بعدِ SSH) و اتمام بدهید
# ============================================================================

ssh root@49.12.191.229 << 'LANGAR_SETUP'

set -euo pipefail

echo "════════════════════════════════════════════════════"
echo "🚀 LANGAR — Setup Otomatis (1 Command)"
echo "════════════════════════════════════════════════════"

# ۱) پرسش‌ها
echo ""
read -p "GitHub Username (مثلاً australianpmnsw): " GH_USER
read -p "Git Email (مثلاً arminoal4@gmail.com): " GH_EMAIL
read -sp "GitHub Token (paste کن): " GH_TOKEN
echo ""

# ۲) ساختِ دایرکتوری
WORK_DIR="$HOME/langar"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# ۳) فایل‌های اساسی — inline creation
echo "📝 ساختِ فایل‌های پروژه..."

# .gitignore
cat > .gitignore << 'GITIGNORE'
.env
.env.*
!.env.example
env
**/env
**/.env
*.db
*.db-wal
*.db-shm
*.sqlite
*.pickle
langar_export_*.json
__pycache__/
*.pyc
*.pyo
venv/
.venv/
ENV/
.git
.DS_Store
Thumbs.db
.idea/
.vscode/
GITIGNORE

# docker-compose.unified.yml
cat > docker-compose.unified.yml << 'COMPOSE'
services:
  bot:
    build: ./langar
    container_name: langar-bot
    restart: unless-stopped
    env_file:
      - .env
    environment:
      - LANGAR_PRO_URL=http://api:8000
    depends_on:
      api:
        condition: service_started
    volumes:
      - ./langar/data:/app/data
      - ./langar/patches:/app/patches
      - ./langar/logs:/app/logs
    networks:
      - langar-net

  api:
    build: ./langar-pro
    container_name: langar-pro-api
    restart: unless-stopped
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8000:8000"
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    networks:
      - langar-net

  db:
    image: pgvector/pgvector:pg15
    container_name: langar-pro-db
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-langar}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme}
      POSTGRES_DB: ${POSTGRES_DB:-langar}
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./langar-pro/db/schema.sql:/docker-entrypoint-initdb.d/schema.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-langar}"]
      interval: 5s
      timeout: 3s
      retries: 10
    networks:
      - langar-net

  redis:
    image: redis:7-alpine
    container_name: langar-redis
    restart: unless-stopped
    volumes:
      - redisdata:/data
    networks:
      - langar-net

networks:
  langar-net:
    driver: bridge

volumes:
  pgdata:
  redisdata:
COMPOSE

# .env.example
cat > .env.example << 'ENVEX'
BOT_TOKEN=your_bot_token_from_botfather
OWNER_ID=your_telegram_id
POSTGRES_USER=langar
POSTGRES_PASSWORD=changeme
POSTGRES_DB=langar
DATABASE_URL=postgresql://langar:changeme@db:5432/langar
BRAIN_PROVIDER=auto
CLAUDE_KEY=
OPENAI_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
SEARCH_PROVIDER=auto
BRAVE_API_KEY=
SERPAPI_KEY=
AILAB_DAILY_BUDGET_USD=1
AILAB_MONTHLY_BUDGET_USD=30
LANGAR_PING_HOUR=8
ENVEX

# deploy.sh
cat > deploy.sh << 'DEPLOY'
#!/usr/bin/env bash
set -euo pipefail
COMPOSE_FILE="docker-compose.unified.yml"
cd "$(dirname "$0")"
echo "── مرحله ۰: بررسی ───────────────────────────────"
command -v docker >/dev/null || { echo "❌ Docker نصب نیست"; exit 1; }
[ -f "$COMPOSE_FILE" ] || { echo "❌ $COMPOSE_FILE پیدا نشد"; exit 1; }
echo "✅ Docker آماده است."
echo "── مرحله ۱: .env ────────────────────────────────"
[ -f .env ] || { cp .env.example .env && echo "⚠️  .env ساخته شد، پرش کن."; exit 0; }
echo "✅ .env آماده است."
echo "── مرحله ۲: بالا آوردنِ استک ─────────────────────"
docker compose -f "$COMPOSE_FILE" up -d --build
echo "── مرحله ۳: انتظار برای سلامتِ سرویس‌ها ───────────"
for i in $(seq 1 30); do
  curl -fsS http://localhost:8000/health >/dev/null 2>&1 && break
  sleep 2
done
echo "── مرحله ۴: تست‌های دود ──────────────────────────"
docker compose -f "$COMPOSE_FILE" ps
echo ""
echo "✅ تمام! Docker compose بالا آمد."
DEPLOY
chmod +x deploy.sh

# ۴) Git setup
echo ""
echo "⚙️  Git configuration..."
git init
git config user.name "$GH_USER"
git config user.email "$GH_EMAIL"

# ۵) اگر subdir پروژه نیست، placeholder بساز
if [ ! -f "README.md" ]; then
  cat > README.md << 'README'
# LANGAR — Telegram Bot + Research Backend

Unified deployment with Docker Compose.

See UPGRADES_FA.md for implementation details.
README
fi

# ۶) Git add/commit
echo ""
echo "📦 add + commit..."
git add .
git commit -m "LANGAR: initial automated setup" || echo "ℹ️  (repo may already have commits)"

# ۷) Git push
echo ""
echo "🚀 push به GitHub..."
git branch -M main
git remote add origin "https://${GH_USER}:${GH_TOKEN}@github.com/${GH_USER}/langar.git" 2>/dev/null || \
  git remote set-url origin "https://${GH_USER}:${GH_TOKEN}@github.com/${GH_USER}/langar.git"

git push -u origin main 2>&1 || echo "⚠️  (push may fail if repo doesn't exist yet; create in GitHub first)"

echo ""
echo "════════════════════════════════════════════════════"
echo "✅ Setup Complete!"
echo ""
echo "📍 اگر خطا داد:"
echo "   1. GitHub repo (private) بساز: github.com/new → langar"
echo "   2. دوباره این script اجرا کن"
echo ""
echo "🐳 Docker start:"
echo "   bash deploy.sh"
echo "════════════════════════════════════════════════════"

LANGAR_SETUP
