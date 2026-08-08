# Owner-Cockpit Stack — راهنمای راه‌اندازی

> Owner-Cockpit = پنلِ مدیریتیِ مالک برای کنترلِ اختاپوس از تلگرام.
> WP1-WP7 کامل (۲۰۲۶-۰۸-۰۸). منبع: Kimi K3 blueprint + Sakana official docs.

## معماری

```
Telegram Mini App (web.telegram.org)
  ↓ HTTPS (cloudflared tunnel)
Owner API (:8788) — HMAC auth + session + approval
  ├─ SQLite (owner_cockpit.db) — audit ledger + sessions + usage
  ├─ live_snapshot.snapshot() — state زنده
  ├─ OTel spans (traces.jsonl) — ردگیری
  └─ Fugu Proxy (:8787) → api.sakana.ai — usage normalizer + cost
```

## فایل‌ها

| فایل | نقش | فلگ |
|---|---|---|
| `fugu_proxy.py` | پراکسیِ محلیِ Fugu + usage normalizer | `OCTOPUS_WIRE_FUGU_PROXY` |
| `otel_setup.py` | OTel spans (JSON-lines) | `OCTOPUS_WIRE_OTEL` |
| `db.py` | SQLite schema + audit chain | `OCTOPUS_WIRE_OWNER_DB` |
| `owner_api.py` | HTTP API + HMAC auth + approval | `OCTOPUS_WIRE_OWNER_API` |
| `miniapp/index.html` | Mini App (۵ تب، RTL، تم تیره) | — |

## راه‌اندازی

### ۱. Environment variables (در OCTOPUS-flags.cmd یا env)
```bat
set FUGU_API_KEY=your-key-here
set TELEGRAM_BOT_TOKEN=your-bot-token
set OWNER_TELEGRAM_IDS=123456789
set OCTOPUS_WIRE_OWNER_DB=1
set OCTOPUS_WIRE_OWNER_API=1
```

### ۲. Owner API را اجرا کن
```bash
python -X utf8 _ops/owner_cockpit/owner_api.py
# listening on 127.0.0.1:8788
```

### ۳. Tunnel (Telegram HTTPS لازم است)
```bash
cloudflared tunnel --url http://127.0.0.1:8788
# URL را در BotFather به‌عنوان Web App URL ثبت کن + /miniapp
```

### ۴. Mini App را سرو کن
`miniapp/index.html` را از طریقِ Owner API یا یک static server سرو کن.

## Smoke Checklist

- [ ] `python -c "from owner_cockpit.db import get_db; get_db()"` — DB ساخته شد
- [ ] `curl http://127.0.0.1:8788/health` → `{"status":"ok"}`
- [ ] با initData نامعتبر → `/auth/session` → 401
- [ ] با initData معتبر → session token
- [ ] `/state` با session → 200 + organism/budget/flags
- [ ] `/fugu/usage` با session → 200 + today aggregation
- [ ] `/freeze` با session → STOP-ORGANISM ساخته شد
- [ ] audit chain: `verify_chain()` → (True, 0)
- [ ] tamper test: رکورد audit را تغییر بده → `verify_chain()` → (False, id)
- [ ] rate limit: ۳۱+ request → 429

## قیمت‌گذاریِ Fugu (verified 2026-08-08)

| مدل | input/1M | output/1M | cached/1M |
|---|---|---|---|
| fugu-ultra (standard) | $5 | $30 | $0.50 |
| fugu-ultra (context >272K) | $10 | $45 | $1.00 |

منبع: [console.sakana.ai/pricing](https://console.sakana.ai/pricing)

## امنیت (۷ لایه)

1. HMAC initData — الگوریتم رسمی Telegram
2. Session جدا — initData فقط برای صدور session؛ بقیه با توکن ۳۰ دقیقه‌ای
3. Owner allowlist — هم در initData هم در verify session
4. Consume-once در confirm — `WHERE status='preview_sent'`
5. CORS محدود به `web.telegram.org`
6. Rate limit — ۳۰/دقیقه per owner
7. Freeze بدون approval ولی همیشه در hash-chained audit ledger
