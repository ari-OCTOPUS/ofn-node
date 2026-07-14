# راهنمای تست ۱۴ روزه با داده واقعی
# Live Testing Guide — 2 Bots, Real Data

**هدف:** در ۱۴ روز مطمئن شویم هر دو ربات با داده واقعی درست کار می‌کنند
**شروع:** همین امروز از روز ۱

---

## قبل از شروع — یک‌بار انجام می‌دهی (امروز)

### مرحله ۱ — ساخت دو ربات تلگرام

در تلگرام به `@BotFather` پیام بده:

```
/newbot
→ نام: Sentinel Monitor
→ username: SentinelMonitorBot (یا هر اسمی)
→ token دریافت می‌کنی — کپی کن
```

```
/newbot
→ نام: Quantum Alpha
→ username: QuantumAlphaSignalBot
→ token دریافت می‌کنی — کپی کن
```

برای گرفتن Chat ID، به `@userinfobot` پیام بده → عدد ID می‌گیری.

---

### مرحله ۲ — پر کردن .env فایل‌ها

**روی Raspberry Pi — فایل SENTINEL:**
```bash
cd ~/sentinel
cp .env.example .env
nano .env
```

این مقادیر رو پر کن:
```
SENTINEL_BOT_TOKEN=توکن_ربات_اول
SENTINEL_CHAT_ID=آیدی_چت_عددی_تو
ANTHROPIC_API_KEY=کلید_anthropic
LUNARCRUSH_API_KEY=کلید_lunarcrush
CRYPTOQUANT_API_KEY=کلید_cryptoquant
```

**فایل QuantumAlphaBot:**
```bash
cd ~/QuantumAlphaBot
cp .env.example .env
nano .env
```

```
QUANTUM_BOT_TOKEN=توکن_ربات_دوم
QUANTUM_CHAT_ID=همون_آیدی_چت
ANTHROPIC_API_KEY=همون_کلید_anthropic
CRYPTOQUANT_API=کلید_cryptoquant
COINALYZE_API=کلید_coinalyze
LUNARCRUSH_API=کلید_lunarcrush
```

---

### مرحله ۳ — تست اتصال اولیه

```bash
# SENTINEL
cd ~/sentinel
python3 -c "
from telegram_signaler import TelegramSignaler
import yaml
cfg = yaml.safe_load(open('config.yaml'))
t = TelegramSignaler(cfg)
t.send('✅ SENTINEL متصل شد — تست اتصال موفق')
"

# QuantumAlphaBot
cd ~/QuantumAlphaBot
python3 -c "
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
import requests
requests.post(f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage',
  json={'chat_id': TELEGRAM_CHAT_ID, 'text': '✅ QuantumAlpha متصل شد'})
"
```

اگه هر دو پیام در تلگرام دیدی، آماده‌ای.

---

## روز ۱ — راه‌اندازی و اولین اجرا

### صبح (۱ ساعت)

```bash
# ۱. نصب dependencies
cd ~/sentinel && pip3 install -r requirements.txt
cd ~/QuantumAlphaBot && pip3 install -r requirements.txt

# ۲. اولین اجرای SENTINEL در mock mode
cd ~/sentinel
SENTINEL_MOCK_MODE=true python3 run_daily.py

# ۳. بررسی لاگ
tail -50 logs/sentinel.log
```

باید پیام تلگرام دریافت کنی: گزارش روزانه با امتیاز کوین‌ها.

```bash
# ۴. اولین اجرای QuantumAlphaBot
cd ~/QuantumAlphaBot
python3 main.py
```

### بعدازظهر (بررسی)
- [ ] پیام SENTINEL در تلگرام دریافت شد؟
- [ ] پیام QuantumAlpha در تلگرام دریافت شد؟
- [ ] خطایی در لاگ نیست؟

---

## روز ۲ — سوییچ به داده واقعی

### صبح

```bash
# SENTINEL با داده واقعی (بدون MOCK)
cd ~/sentinel
python3 run_daily.py
```

اگه خطای rate limit دیدی:
```bash
# صبر کن ۶۰ ثانیه — LunarCrush فقط ۱۰ req/min
# یا mock را فعط برای LunarCrush نگه دار:
LUNARCRUSH_MOCK=true python3 run_daily.py
```

### بررسی داده واقعی
```bash
# قیمت‌ها واقعی هستند؟
python3 -c "
from data_fetcher import DataFetcher
import yaml
cfg = yaml.safe_load(open('config.yaml'))
df = DataFetcher(cfg)
prices = df.get_all_prices()
print(prices)
"
```

---

## روز ۳ — راه‌اندازی cron

```bash
# باز کن crontab
crontab -e
```

این خطوط را اضافه کن:
```cron
# SENTINEL — هر روز ساعت ۸ صبح
0 8 * * * cd /home/pi/sentinel && python3 run_daily.py >> logs/daily.log 2>&1

# SENTINEL — چک قیمت هر ۴ ساعت
0 */4 * * * cd /home/pi/sentinel && python3 -c "from main import SentinelBot; SentinelBot().check_price_alerts()" >> logs/alerts.log 2>&1

# QuantumAlphaBot — هر ۶ ساعت
0 */6 * * * cd /home/pi/QuantumAlphaBot && python3 main.py >> logs/quantum.log 2>&1
```

```bash
# تأیید cron
crontab -l
```

---

## روز ۴ — تست دستورات تلگرام

در تلگرام به ربات SENTINEL این دستورات را ارسال کن:

```
/start
→ باید خوش‌آمدگویی بدهد

/status
→ باید فاز فعلی (Phase 0) و تعداد روزها نشان دهد

/score CORE
→ امتیاز لحظه‌ای CORE با داده واقعی

/score XMR
→ امتیاز XMR

/ping
→ باید "pong" برگردد
```

---

## روز ۵ — بررسی کیفیت داده

```bash
cd ~/sentinel
python3 -c "
from data_store import DataStore
ds = DataStore()
stats = ds.get_stats()
for f, s in stats.items():
    print(f'{f}: {s.get(\"rows\",0)} rows, {s.get(\"size_kb\",0)} KB')
"
```

اگه Parquet فایل‌ها داده دارند → درست است.

---

## روز ۶ — تست harvest (کشیدن تاریخچه)

```bash
cd ~/sentinel
python3 harvest.py
```

این می‌کشد:
- تاریخچه ۱۸۰ روزه قیمت همه کوین‌ها از LunarCrush
- داده exchange flows و whale ratio از CryptoQuant

ممکن است ۳۰-۴۵ دقیقه طول بکشد (rate limit).

---

## روز ۷ — بررسی میانی

### چک‌لیست روز ۷

**SENTINEL:**
- [ ] گزارش روزانه هر روز در تلگرام دریافت شده؟
- [ ] قیمت‌های واقعی نمایش داده می‌شوند؟
- [ ] Phase 0 هنوز فعال است؟
- [ ] هیچ crash یا خطای crash-loop نیست؟

**QuantumAlphaBot:**
- [ ] هر ۶ ساعت سیکل جدید اجرا می‌شود؟
- [ ] paper_ledger.jsonl داده جدید اضافه می‌شود؟
- [ ] گزارش به تلگرام می‌رسد؟

**بررسی paper_ledger:**
```bash
cd ~/QuantumAlphaBot
python3 -c "
import json
lines = open('data/paper_ledger.jsonl').readlines()
print(f'کل سیکل‌ها: {len(lines)}')
last = json.loads(lines[-1])
print(f'آخرین سیکل: {last[\"cycle_ts\"]}')
print(f'Nulled: {last[\"cycle_nulled\"]}')
print(f'تعداد کوین: {last[\"n_coins\"]}')
"
```

---

## روز ۸ — تست signal_fusion

```bash
cd ~/sentinel
python3 -c "
from signal_fusion import SignalFusion, describe_matrix
from lc_client import LunarCrushClient
from cq_client import CryptoQuantClient
import yaml, os
from dotenv import load_dotenv
load_dotenv('.env')

lc = LunarCrushClient(api_key=os.getenv('LUNARCRUSH_API_KEY'))
cq = CryptoQuantClient(api_key=os.getenv('CRYPTOQUANT_API_KEY'))
fusion = SignalFusion(lc, cq)

for sym in ['CORE', 'XMR', 'TAO']:
    r = fusion.compute(sym)
    print(f'{sym}: {r.quadrant} | kelly={r.kelly_frac} | social={r.social_signal} | macro={r.macro_regime}')
"
```

---

## روز ۹ — تست portfolio_advisor

```bash
cd ~/sentinel
python3 portfolio_advisor.py --dry-run
```

باید گزارش دوهفتگی چاپ کند. اگه ANTHROPIC_API_KEY داری، thesis با Claude نوشته می‌شود.

---

## روز ۱۰ — بررسی Phase 0

```bash
cd ~/sentinel
python3 -c "
from phase_manager import PhaseManager
import yaml
cfg = yaml.safe_load(open('config.yaml'))
pm = PhaseManager(cfg)
pm.initialize()
print(pm.get_status_summary())
print('پیشرفت به Phase 1:', pm.should_advance_from_phase0())
"
```

Phase 0 حداقل ۱۰ روز طول می‌کشد و به ۱۰ نمونه نوسان نیاز دارد.

---

## روز ۱۱ — تنظیم هشدار قیمت

در SENTINEL تست کن:
```
/scenario fiat_erosion active
→ باید تأیید کند که سناریو فعال شد
→ CORE باید امتیاز بیشتری بگیرد
```

بررسی در لاگ:
```bash
grep "fiat_erosion" logs/daily.log | tail -5
```

---

## روز ۱۲ — بررسی کیفیت QuantumAlpha

```bash
cd ~/QuantumAlphaBot
python3 -c "
import json
from collections import Counter

lines = open('data/paper_ledger.jsonl').readlines()
all_decisions = []
for line in lines:
    cycle = json.loads(line)
    for coin in cycle.get('coins', []):
        all_decisions.append((coin['symbol'], coin.get('llm_decision', 'UNKNOWN')))

# بیشترین ACCUMULATE
acc = [s for s, d in all_decisions if d == 'ACCUMULATE']
print('پرتکرارترین ACCUMULATE:', Counter(acc).most_common(10))
"
```

---

## روز ۱۳ — stress test

```bash
# اجرای دستی همه چیز پشت سر هم
cd ~/sentinel && python3 run_daily.py
sleep 10
cd ~/QuantumAlphaBot && python3 main.py
sleep 10
cd ~/sentinel && python3 portfolio_advisor.py --force

# بررسی لاگ‌ها
tail -20 ~/sentinel/logs/daily.log
tail -20 ~/QuantumAlphaBot/logs/quantum.log
```

---

## روز ۱۴ — گزارش نهایی تست

### چک‌لیست تأیید کامل

**SENTINEL ✅:**
- [ ] ۱۴ گزارش روزانه در تلگرام
- [ ] Phase 0 در حال کالیبراسیون (یا به Phase 1 رفته)
- [ ] دستورات /score /status /ping کار می‌کنند
- [ ] هیچ crash در طول ۱۴ روز نبوده
- [ ] Parquet فایل‌ها داده جمع کرده‌اند

**QuantumAlphaBot ✅:**
- [ ] ~۵۶ سیکل در paper_ledger (6 ساعت × 14 روز)
- [ ] گزارش هر سیکل در تلگرام
- [ ] کوین‌های ACCUMULATE شناسایی شده‌اند

**Portfolio Advisor ✅:**
- [ ] --dry-run بدون خطا اجرا می‌شود
- [ ] گزارش دوهفتگی scheduled (1 و 15 ماه)

---

## بعد از ۱۴ روز — تصمیم‌گیری

### اگه همه چیز خوب بود:
1. **Phase 0 SENTINEL** → وقتی `should_advance_from_phase0()` برگشت True، تأیید کن
2. **QuantumAlphaBot** → اگه BTC trend به ACCUMULATING برگشت، سیکل‌ها null نمی‌شوند
3. **خرید اول** → بعد از Phase 1 با امتیاز ≥ 70 و Kelly coefficient

### اگه مشکل داشت:
- هر خطایی را عکس بگیر و بفرست — در همین session بهت کمک می‌کنم

---

## دستورات مفید روزانه

```bash
# وضعیت سریع
cd ~/sentinel && python3 -c "
from phase_manager import PhaseManager
import yaml
pm = PhaseManager(yaml.safe_load(open('config.yaml')))
print(pm.get_status_summary())
"

# آخرین سیکل Quantum
cd ~/QuantumAlphaBot && python3 -c "
import json
last = json.loads(open('data/paper_ledger.jsonl').readlines()[-1])
print(f\"سیکل: {last['cycle_ts']}\")
print(f\"Null: {last['cycle_nulled']}\")
coins = [c['symbol'] for c in last['coins'] if c.get('llm_decision')=='ACCUMULATE']
print(f\"ACCUMULATE: {coins}\")
"

# لاگ امروز
tail -50 ~/sentinel/logs/daily.log
```
