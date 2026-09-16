#!/bin/bash
# ============================================================
# SENTINEL — setup.sh
# راهنمای نصب گام‌به‌گام روی Raspberry Pi 3B (DietPi/Raspberry Pi OS Lite)
# ============================================================

set -e
echo "======================================================"
echo "  SENTINEL — نصب روی Raspberry Pi 3B"
echo "======================================================"

# ─── ۱. به‌روزرسانی سیستم ───
echo ""
echo "[۱/۸] به‌روزرسانی پکیج‌ها..."
sudo apt-get update -qq
sudo apt-get upgrade -y -qq

# ─── ۲. نصب Python و ابزارها ───
echo ""
echo "[۲/۸] نصب Python 3 و ابزارهای لازم..."
sudo apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    git \
    sqlite3 \
    libsqlite3-dev \
    curl

python3 --version

# ─── ۳. ساخت محیط مجازی ───
echo ""
echo "[۳/۸] ساخت virtual environment..."
cd ~/sentinel 2>/dev/null || { mkdir ~/sentinel && cd ~/sentinel; }

python3 -m venv venv
source venv/bin/activate

# ─── ۴. نصب پکیج‌های Python ───
echo ""
echo "[۴/۸] نصب پکیج‌های Python..."
pip install --upgrade pip -q
pip install \
    requests==2.31.0 \
    pyyaml==6.0.1 \
    python-dotenv==1.0.0 \
    -q

echo "پکیج‌های نصب‌شده:"
pip list --format=columns | grep -E "requests|PyYAML|python-dotenv"

# ─── ۵. ساخت .env از نمونه ───
echo ""
echo "[۵/۸] تنظیم فایل .env..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  فایل .env ساخته شد. لطفاً ویرایش کن:"
    echo "    nano ~/sentinel/.env"
    echo ""
    echo "   مقادیر لازم:"
    echo "   • TELEGRAM_BOT_TOKEN"
    echo "   • TELEGRAM_CHAT_ID"
    echo "   • LUNARCRUSH_API_KEY"
    echo "   • CRYPTOQUANT_API_KEY"
    echo "   • COLD_WALLET_BTC (آدرس عمومی)"
    echo "   • COLD_WALLET_ETH"
    echo "   • COLD_WALLET_XMR"
    echo "   • COLD_WALLET_ZEC"
else
    echo "  .env از قبل وجود دارد — رد شد"
fi

# ─── ۶. آزمایش اتصال ───
echo ""
echo "[۶/۸] آزمایش اتصال به اینترنت..."
if curl -s --max-time 5 https://api.coingecko.com/api/v3/ping > /dev/null; then
    echo "  ✅ CoinGecko: متصل"
else
    echo "  ❌ CoinGecko: قطع — اینترنت را بررسی کن"
fi

if curl -s --max-time 5 https://api.alternative.me/fng/?limit=1 > /dev/null; then
    echo "  ✅ Fear & Greed: متصل"
else
    echo "  ❌ Fear & Greed: قطع"
fi

# ─── ۷. تنظیم cron ───
echo ""
echo "[۷/۸] تنظیم cron job (هر ۱۵ دقیقه)..."
CRON_CMD="*/15 * * * * cd ~/sentinel && source venv/bin/activate && python3 main.py --once >> sentinel.log 2>&1"
DAILY_REPORT="0 21 * * * cd ~/sentinel && source venv/bin/activate && python3 main.py --once >> sentinel.log 2>&1"

# اضافه کردن به crontab اگر وجود ندارد
(crontab -l 2>/dev/null | grep -q "sentinel") && \
    echo "  cron از قبل تنظیم شده" || \
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo "  ✅ cron job تنظیم شد"
echo ""
echo "  برای بررسی: crontab -l"

# ─── ۸. اجرای اول ───
echo ""
echo "[۸/۸] اجرای اولیه برای بررسی..."
echo ""
python3 main.py --once && echo "✅ اجرای اولیه موفق" || echo "❌ خطا در اجرا — لاگ را بررسی کن"

echo ""
echo "======================================================"
echo "  نصب کامل شد!"
echo "======================================================"
echo ""
echo "دستورات مفید:"
echo "  مشاهده لاگ:       tail -f ~/sentinel/sentinel.log"
echo "  اجرای دستی:       cd ~/sentinel && source venv/bin/activate && python3 main.py"
echo "  حالت cron:        python3 main.py --once"
echo "  بررسی پایگاه داده: sqlite3 ~/sentinel/state.db '.tables'"
echo "  وضعیت cron:       crontab -l"
echo ""
echo "⚠️  فراموش نکن .env را پر کنی!"
