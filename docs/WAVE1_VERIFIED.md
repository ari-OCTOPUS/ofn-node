# Wave 1 — Verified Independent Audit

> **تاریخ:** 2026-08-02 · **آزمایشگر:** ZCode (audit مستقل روی دیسک)
> **هدف:** تأیید صادقانهٔ green/red بودن Wave 1 Ops Runtime — بدون fake-green.

---

## نتیجهٔ کلی: ✅ GREEN

Wave 1 واقعاً shipped و functional است. همهٔ ادعا‌های برنامهٔ پیوست روی دیسک تأیید شدند.

---

## فایل‌های canonical (همگی وجود دارند و functional)

| فایل | مسیر | وضعیت |
|---|---|---|
| Action engine | `_ops/agi2027_control/ops_actions.py` | ✅ واقعی |
| MiniApp gateway | `_ops/telegram_center/miniapp_gateway.py` | ✅ واقعی |
| MiniApp state | `_ops/telegram_center/miniapp_state.py` | ✅ واقعی |
| Frontend | `_ops/telegram_center/miniapp/app.js` | ✅ واقعی |

---

## تأیید قابلیت‌ها (با شمارهٔ خط)

### 1. Telegram initData HMAC verify ✅
- `miniapp_gateway.py` — HMAC validation واقعی با `TELEGRAM_BOT_TOKEN`
- `auth_date <= 300s` freshness check پیاده‌سازی شده

### 2. Owner gate ✅
- `owner_chat_id` check — فقط owner می‌تواند action بزند
- بدون initData → `403 owner_auth_required`

### 3. POST /api/actions owner-gated ✅
- POST handler با owner auth gate کامل

### 4. SQLite CRM schema ✅ (`ops_actions.py`)
```sql
CREATE TABLE leads          (id, handle, display_name, source, platform, stage, ...)
CREATE TABLE lead_notes     (id, lead_id, note, created_at)
CREATE TABLE tasks          (id, title, kind, target_type, target_id, due_at, status, ...)
CREATE TABLE value_events   (id, leg, event, value_type, output_score, cost_score, risk_score, ...)
```

### 5. Audit log + Idempotency ✅
- `AuditLog` → `ops-action-audit.jsonl`
- `IdempotencyStore` → `ops-actions-idempotency.sqlite3`

### 6. Blocked prefixes ✅
`onlyfans`, `fansly`, `scrape`, `login`, `auto_dm`, `mass_message` همگی در safety layer.

### 7. MiniApp button = `web_app` ✅ (CRITICAL)
```python
# _ops/telegram_center/center.py:1329
rows.append([{"text": "📊 داشبورد", "web_app": {"url": _mu}}])
```
**صحیح** — نه `url`. Telegram با `web_app` initData ارسال می‌کند.

### 8. Frontend sends X-Tg-Init-Data ✅
```js
// _ops/telegram_center/miniapp/app.js:23
function tgHeaders(extra){ var h=extra||{}; if(tg && tg.initData){ h["X-Tg-Init-Data"] = tg.initData; } return h; }
```

---

## نتیجه: Wave 1 سبز است — به Wave 2 برو

هیچ rebuild لازم نیست. فقط روی همین engine (`ops_actions.py`) Wave 2 را اضافه کن:
- جداول: `campaigns`, `content_items`, `manual_send_queue`, `money_events`
- اکشن‌های local-only، owner-gated، audited، idempotent
- OF/Fansly direct automation برای همیشه ممنوع باقی می‌ماند
