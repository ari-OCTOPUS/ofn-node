#!/bin/bash
# ============================================================================
# setup-github-vps.sh — اتوماتیکِ GitHub + push از روی VPS (Hetzner)
# اجرا:  bash setup-github-vps.sh
# ============================================================================
set -euo pipefail

echo "════════════════════════════════════════════════════"
echo "🚀 LANGAR — اتوماتیکِ GitHub و Push"
echo "════════════════════════════════════════════════════"

# ۱) اطلاعاتِ GitHub
echo ""
read -p "📝 GitHub username (مثلاً australianpmnsw): " GH_USER
read -p "📧 Email برای commits (مثلاً arminoal4@gmail.com): " GH_EMAIL
read -sp "🔑 GitHub Personal Access Token (paste کن بعد Enter): " GH_TOKEN
echo ""

if [ -z "$GH_USER" ] || [ -z "$GH_EMAIL" ] || [ -z "$GH_TOKEN" ]; then
  echo "❌ تمام فیلد‌ها اجباری‌اند."
  exit 1
fi

# ۲) پروژه را clone یا setup
LANGAR_DIR="$HOME/langar"
if [ ! -d "$LANGAR_DIR" ]; then
  echo ""
  echo "⬇️  کلونِ پروژه از GitHub..."
  git clone "https://${GH_USER}:${GH_TOKEN}@github.com/${GH_USER}/langar.git" "$LANGAR_DIR" 2>/dev/null || {
    echo "❌ خطا در clone (ریپو شاید هنوز در GitHub ساخته نشده). دستی بساز یا skip کن."
    mkdir -p "$LANGAR_DIR"
  }
fi

cd "$LANGAR_DIR"

# ۳) اگر git init نشده، init کن
if [ ! -d .git ]; then
  echo ""
  echo "🔧 git init..."
  git init
  git remote add origin "https://${GH_USER}:${GH_TOKEN}@github.com/${GH_USER}/langar.git" 2>/dev/null || true
fi

# ۴) git config
echo ""
echo "⚙️  git config..."
git config user.name "$GH_USER"
git config user.email "$GH_EMAIL"

# ۵) Add + commit
echo ""
echo "📦 add + commit..."
git add .
git status

echo ""
echo "⚠️  مطمئن شو هیچ .env / env / *.db در لیست نیست!"
read -p "✅ ادامه بدهم (y/n)? " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "❌ لغو شد."
  exit 1
fi

git commit -m "LANGAR unified: core + langar-pro + upgrades (retrieval/BrainRouter/ACE) — automated deploy" || {
  echo "⚠️  (شاید commit قبلاً ساخته شده)"
}

# ۶) git push
echo ""
echo "🚀 push به GitHub..."
git push -u origin main 2>&1 || {
  echo "ℹ️  اگر branch اولاً main نیست، git می‌تواند بگوید. ادامه دهم..."
  git branch -M main
  git push -u origin main
}

echo ""
echo "════════════════════════════════════════════════════"
echo "✅ تمام! پروژه به GitHub push شد."
echo ""
echo "📍 بعدِ اصلاحات:"
echo "   git add . && git commit -m '...' && git push"
echo ""
echo "🐳 اجرایِ Docker:"
echo "   bash deploy.sh"
echo "════════════════════════════════════════════════════"
