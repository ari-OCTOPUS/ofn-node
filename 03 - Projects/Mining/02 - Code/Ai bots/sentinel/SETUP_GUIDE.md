# SENTINEL — Setup Guide / راهنمای نصب

**Version 1.0 · Bilingual: English + Persian**

---

## Stage A — Laptop (Build & Debug) / لپ‌تاپ (ساخت و باگ‌گیری)

### Prerequisites / پیش‌نیازها
- Python 3.9 or higher / پایتون ۳.۹ یا بالاتر
- Git
- Internet connection / اتصال اینترنت
- API keys (see `.env.example`) / کلیدهای API

### Step 1 — Clone & virtual environment / کلون و محیط مجازی
```bash
git clone <your-repo-url>
cd sentinel
python3 -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

### Step 2 — Configure / پیکربندی
```bash
cp .env.example .env
nano .env   # یا هر ویرایشگر دیگری
```

Fill in your API keys / مقادیر را پر کنید:
```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
LUNARCRUSH_API_KEY=...
CRYPTOQUANT_API_KEY=...
COLD_WALLET_BTC=bc1q...   # public address only / فقط آدرس عمومی
COLD_WALLET_ETH=0x...
COLD_WALLET_XMR=4...
COLD_WALLET_ZEC=t1...
```

> ⚠️  **Never commit .env** — it is in `.gitignore`
> ⚠️  **هرگز .env را کامیت نکن**

### Step 3 — Test in mock mode / تست در حالت آفلاین
```bash
# Run all unit tests (no API keys needed)
# اجرای تمام تست‌ها بدون کلید API
python3 -m pytest tests/ -v

# Single cycle in mock mode / یک چرخه در حالت mock
SENTINEL_MOCK_MODE=1 python3 main.py --once
```

### Step 4 — Backtest / بک‌تست
```bash
# Validate scoring logic on 1 year of historical price data
# اعتبارسنجی منطق امتیازدهی روی ۱ سال داده‌ی تاریخی
python3 backtest.py --days 365

# Use cached data (no network) after first run
python3 backtest.py --days 365 --no-fetch
```

Read the flags section of the backtest output carefully.  
بخش «هشدارها» در خروجی backtest را با دقت بخوان.

### Step 5 — Live test (requires real API keys) / تست زنده
```bash
# Dry-run: prints signals instead of sending to Telegram
# اجرای آزمایشی: سیگنال‌ها چاپ می‌شوند نه ارسال
python3 main.py --once
```

Check the `sentinel.log` file for details. / فایل `sentinel.log` را بررسی کن.

### Step 6 — Continuous mode (laptop) / حالت دائم
```bash
python3 main.py   # runs every 15 minutes / هر ۱۵ دقیقه اجرا می‌کند
```

---

## Stage B — Orange Pi 5 / Raspberry Pi 3B Fleet

### Hardware notes / نکات سخت‌افزاری

| Feature | Orange Pi 5 | Raspberry Pi 3B |
|---|---|---|
| RAM | 4–16 GB | 1 GB |
| CPU | RK3588S (8-core) | BCM2837 (4-core) |
| Code changes needed | Minimal | None — SENTINEL is already Pi 3B-safe |
| Recommended OS | Ubuntu 22 / Armbian | Raspberry Pi OS Lite |

> **SENTINEL is written to be Pi 3B-safe** (SQLite, no heavy frameworks,
> cron-style loop). On Orange Pi 5 it will run with extra headroom.
>
> **SENTINEL برای Pi 3B نوشته شده** (SQLite، بدون فریمورک سنگین، حلقه‌ی cron-style).
> روی Orange Pi 5 با منابع اضافه اجرا می‌شود.

### Step 1 — Prepare the Pi / آماده‌سازی Pi

```bash
# SSH into the Pi / وارد Pi شو
ssh pi@<pi-ip-address>

# Update system / به‌روزرسانی سیستم
sudo apt-get update && sudo apt-get upgrade -y

# Install Python & deps
sudo apt-get install -y python3 python3-pip python3-venv git sqlite3
```

### Step 2 — Run deploy.sh / اجرای deploy.sh

```bash
# On the Pi: copy the project first
scp -r ./sentinel pi@<pi-ip>:~/sentinel

# Then run the deployment script
ssh pi@<pi-ip> "bash ~/sentinel/deploy.sh"
```

`deploy.sh` will:
- Create a virtual environment
- Install dependencies
- Set up a `systemd` timer (runs every 15 minutes)
- Run a self-test (mock mode)
- Print resource usage

### Step 3 — Canary test (ONE Pi first) / تست کانری (ابتدا روی یک Pi)

```bash
# Verify it runs and sends a real Telegram signal
SENTINEL_MOCK_MODE=0 python3 main.py --once

# Check RAM/CPU usage
free -m
top -bn1 | head -5
```

Acceptable resource usage / مصرف منابع قابل قبول:
- RAM: < 80 MB
- CPU average: < 5% (idle between cycles)

### Step 4 — Simulate API outage / شبیه‌سازی قطعی API

```bash
# Block CryptoQuant temporarily and verify graceful degradation message
# CryptoQuant را موقتاً قطع کن و پیام graceful degradation را بررسی کن
sudo iptables -A OUTPUT -d api.cryptoquant.com -j DROP
python3 main.py --once
sudo iptables -D OUTPUT -d api.cryptoquant.com -j DROP
```

Expected: Telegram signal arrives with a note:
`⚠️ On-chain data unavailable — scored on 2 signals`

### Step 5 — Fleet rollout / استقرار ناوگان

Only after Armin confirms the canary Pi works:
```bash
# Loop over your Pi IPs
for ip in 192.168.x.x 192.168.x.y ...; do
  scp -r sentinel pi@$ip:~/sentinel
  ssh pi@$ip "bash ~/sentinel/deploy.sh"
done
```

### Step 6 — Systemd status / وضعیت systemd

```bash
systemctl status sentinel.timer
systemctl status sentinel.service
journalctl -u sentinel.service -f   # live log / لاگ زنده
```

---

## Isolation from mining / جداسازی از مایننگ

SENTINEL runs as a **separate user** (`sentinel`), in a **separate directory**
(`/home/sentinel/`), under a **separate `systemd` unit**. Mining and signaling
must NEVER share a process.

```bash
# Create dedicated user / ساخت کاربر اختصاصی
sudo useradd -m -s /bin/bash sentinel
sudo cp -r ~/sentinel /home/sentinel/
sudo chown -R sentinel:sentinel /home/sentinel/sentinel
```

The `deploy.sh` handles this automatically.

---

## Telegram commands / دستورات تلگرام

| Command | Description |
|---|---|
| `/status` | Current phase + summary / وضعیت فعلی |
| `/portfolio` | Investment progress / پیشرفت سرمایه‌گذاری |
| `/score BTC` | Instant score / امتیاز فوری |
| `/confirm_BTC 500 86400` | Record a buy: A$500 at $86,400 |
| `/scenario fiat_erosion active` | Update scenario status |

---

## XMR / ZEC purchase path — OPEN QUESTION / سؤال باز

> ⚠️  XMR is delisted from most major CEXs (Binance, Coinbase, Kraken).
> **This question is still open for Armin to decide.** Until confirmed,
> every XMR/ZEC signal includes a reminder.
>
> Options / گزینه‌ها:
> - Atomic swap (decentralized, no CEX needed)
> - Remaining CEXs that still list XMR (e.g. TradeOgre, Haveno)
> - P2P platforms
>
> Once you decide, update `PRIVACY_PURCHASE_NOTE` in `telegram_signaler.py`
> and set `purchase_path` in `config.yaml`.

---

## Security checklist / چک‌لیست امنیتی

- [ ] `.env` permissions: `chmod 600 .env`
- [ ] `.env` not in git: verify with `git status`
- [ ] No private keys anywhere in the codebase
- [ ] Cold wallet addresses are public addresses only
- [ ] `state.db` backed up regularly
- [ ] Telegram bot accessible only to your chat ID
- [ ] Pi is behind your home router (not port-forwarded to internet)

---

## File structure / ساختار فایل‌ها

```
sentinel/
├── config.yaml              # Main config — operator edits this
├── .env                     # Secrets — never commit
├── .env.example             # Template
├── requirements.txt
├── main.py                  # Main loop
├── data_fetcher.py          # API layer + mock mode
├── scorer.py                # Entry Favorability scoring + Big Scenarios
├── phase_manager.py         # Phase 0/1/2 + SQLite history
├── telegram_signaler.py     # Bilingual signal formatting
├── wallet_tracker.py        # Manual buy tracking
├── backtest.py              # Historical validation
├── state.db                 # SQLite (auto-created)
├── sentinel.log             # Log file (auto-created)
├── setup.sh                 # Pi 3B setup script
├── deploy.sh                # Orange Pi 5 / Pi 3B deploy script
├── SETUP_GUIDE.md           # This file
├── tests/
│   ├── test_scorer.py
│   ├── test_data_fetcher.py
│   └── test_phase_manager.py
└── backtest_cache/          # Cached historical data
```
