# 01-INTEGRATION-CHECKLIST — وصل‌کردنِ رویدادهای ارگانیسم به تلگرام

> اسکنِ فنیِ مبتنی بر شواهد · 2026-07-24 · شاخهٔ live `claude/c7-continuity` @ `67f1a71`.
> همهٔ مسیرها و شمارهٔ خطوط با کدِ همین روز راستی‌آزمایی شده‌اند. فقط‌خواندنی.

## حقیقتِ مرکزی (اصلاح‌شده)

**تلگرام pull-based است، نه push.** `center.py` سه کار می‌کند:
1. `run_once()` (`center.py:1486`): `poll_updates` (getUpdates) → `handle_update` واکنشی به پیام/دکمهٔ مالک.
2. `beat()` (`center.py:394`) هر ۳۰۰s: فقط **(الف)** edit پیامِ پین‌شدهٔ وضعیت، **(ب)** send دایجستِ هر پا (cadence). هر دو از `collect_feeds()` کشیده می‌شوند (pull).
3. هیچ push-per-eventی وجود ندارد.

پس **هر رویدادی که owner باید فوراً بداند، فعلاً یا در فایل می‌خوابد، یا فقط وقتی owner `/start` می‌زند دیده می‌شود.**

---

## جدولِ ۱۶ نقطهٔ گسست (gap) — منبع → مقصد → وضعیت

| # | سیگنال | تولیدکننده (file:line) | مقصدِ فعلی | push تلگرام؟ | Tier |
|---|---|---|---|---|---|
| 1 | `events.emit()` همه‌نوع | `events.py:122-177` | `state/events.jsonl` | نه (فقط dashboard خواندنی) | 1 |
| 2 | `UnifiedBus.publish()` | `unified_bus.py:68-97` | ledger + chrono.db + audit-note | نه (`_subscribers` خالی، `unified_bus.py:48`) | 0 |
| 3 | `incident.opened` | `events.py:356-368` | `events.jsonl` | **هرگز** (صفر caller تولیدی) | 1 |
| 4 | `incident.contained` | `events.py:371-376` | `events.jsonl` | **هرگز** (صفر caller تولیدی) | 1 |
| 5 | `protective_halt` (pain>0.7) | `wiring.py:977-980`، اجرا `organism.py:494-495` | `ORGANISM-STATE.json` + `governor-alerts.md` + `HEARTBEAT.md` | نه | 0 |
| 6 | `protective_throttle` (reflex critical) | `wiring.py:983-987` | `ORGANISM-STATE.json` (فقط state) | نه (حتی alert هم نه) | 1 |
| 7 | selfheal leg-restart | `chrono.py:1227-1234` | `selfheal-events.jsonl` + `events.jsonl` | نه (فقط شمارش در /start) | 1 |
| 8 | selfheal circuit-breaker throttle (≥3/300s) | `chrono.py:1252-1254` | `governor-alerts.md` | نه | 0 |
| 9 | `circuit_breaker OPEN` (outbound) | `budget/circuit_breaker.py:136-144` | `circuit-state.json` + `governor-alerts.md` | نه | 1 |
| 10 | `stress`/`fear` entry | `cortex/stress.py:140-149` | `cortex/stress-latest.json` + `events.jsonl` | نه | 2 |
| 11 | `opslib.alert()` (~۱۷۰ call-site) | `budget/opslib.py:341-344` | `governor/governor-alerts.md` | **هرگز** (فقط append فایل) | 0 |
| 12 | `opslib.heartbeat()` | `budget/opslib.py` | `_memory/HEARTBEAT.md` | نه | 2 |
| 13 | proposal جدید (leg.proposals) | `live_loop.py:398-485` route_leg_proposals | کارت به مالک (این وصل است) | **بله** | — |
| 14 | verdict مالک (approve/reject) | `telegram_center/center.py` callback | outcome + learning | **بله** | — |
| 15 | `lead-naghshi` fail-storm | `selfheal-events.jsonl` (۶۰ رویداد امروز) | فایل | نه | 0 |
| 16 | `DEEPSEEK_API_KEY` غیرفعال | `.env` (کامنت‌شده) | — | نه | 2 (تصحیح: Fugu/GLM فعال‌اند، پس مغز کر نیست) |

**نکتهٔ مهم (تصحیح):** `DEEPSEEK_API_KEY` غیرفعال است ولی `model_router` از **Fugu/GLM** استفاده می‌کند (`model_router.py:95-97`) و هر دو کلید حاضرند. پس «مغزِ LLM کر است» دقیق نیست؛ فقط مسیرِ DeepSeek (که router به آن ارجاع نمی‌دهد) غیرفعال است.

**نکتهٔ مهم (تصحیح):** lead-naghshi **۶۰ رویداد** در `selfheal-events.jsonl` امروز دارد، نه ۴. این fail-storm واقعی و زنده است.

---

## Tier تعریف
- **Tier 0** = owner باید فوراً بداند (incident، protective-halt، circuit-breaker throttle، fail-storm، alert). این‌ها سکوت خطرناک‌اند.
- **Tier 1** = رویدادهای ساختاریافته که داشتن pushشان ارزشمند است.
- **Tier 2** = polish / context (stress، heartbeat).

---

## چهار فاز اجرایی (مرتب بر اساس ارزش/تلاش)

### فاز A — Event Bridge (Quick Win، بزرگ‌ترین ارزش)
یک ماژول `_ops/telegram_center/event_bridge.py` که **دو منبع را به center.beat() وصل می‌کند**:
- منبع ۱: خواندنِ `governor-alerts.md` از آخرین offset (Tier 0: alert→push).
- منبع ۲: خواندنِ `events.jsonl` فیلترِ `incident.*` + `task.failed` + protective-halt از `ORGANISM-STATE.json`.
- مقصد: `center.py` یک متد `push_alert(text, topic)` جدید بگیرد (send به topic=system یا DM مالک).
- dedup با offset/cursor؛ rate-limit (مثلاً نهایتاً ۱۰ push/ساعت).

**چرا اول:** همهٔ ۶ نقطهٔ Tier 0 را با یک ماژول حل می‌کند. lead-naghshi، protective-halt، circuit-breaker.

### فاز B — مغز-حافظه (گفتگوی حافظه‌دار)
- conversation buffer (آخرین N پیام مالک + پاسخ) → `MemoryStore` یا یک store سبک.
- `llm_intent.py` (موجود) را به `model_router.ask` وصل کن (الان صفر حافظهٔ مکالمه).
- recall: قبل از پاسخ، `memory_store.search()` بزن برای زمینه.

### فاز C — UI زنده (dynamic pinned status + adaptive keyboard)
- `render_status()` (موجود، `render module`) را با فیلدهای protective/incident/alert غنی کن.
- adaptive keyboard: وقتی incident.open وجود دارد، دکمهٔ «containing» نشان بده.

### فاز D — تولید incident واقعی
- نقاط ۳ و ۴: `incident.opened/contained` **هیچ caller تولیدی ندارند**. باید producer بسازی
  (مثلاً وقتی protective-halt فعال می‌شود → `events.open_incident(...)`، و وقتی برمی‌گردد → `contain_incident`).

---

## شبه‌کد: event_bridge.py (QW1 — فاز A)

```python
# _ops/telegram_center/event_bridge.py
# Push regulator alerts + critical events to Telegram. Behind OCTOPUS_WIRE_EVENT_BRIDGE.
import os, time
from pathlib import Path
import opslib

FLAG = "OCTOPUS_WIRE_EVENT_BRIDGE"
ALERTS_MD = opslib.OPS / "governor" / "governor-alerts.md"
EVENTS = opslib.STATE_DIR / "events.jsonl"
STATE = opslib.STATE_DIR / "ORGANISM-STATE.json"
CURSOR = opslib.STATE_DIR / "telegram" / "event-bridge-cursor.json"
MAX_PUSH_PER_HOUR = 10

def flag_on():
    return str(os.environ.get(FLAG, "")).strip().lower() in ("1","true","yes")

def beat(center) -> dict:
    """از center.beat() صدا زده شود. pushهای زبانِ انسان به مالک. dedup + rate-limit."""
    if not flag_on():
        return {"pushed": 0, "reason": "flag-off"}
    pushed = 0
    cur = _load_cursor()
    # 1) governor-alerts.md: read lines past last offset
    new_alerts, cur["alerts_pos"] = _read_past(ALERTS_MD, cur.get("alerts_pos", 0))
    for line in new_alerts:
        if _rate_ok(cur) and _is_critical(line):
            if center.push_alert(_human(line), topic="system"):
                pushed += 1; cur["push_count"] += 1
    # 2) events.jsonl: incident.opened / task.failed past last line offset
    new_evts, cur["events_pos"] = _read_past(EVENTS, cur.get("events_pos", 0))
    for ln in new_evts:
        import json
        try: e = json.loads(ln)
        except: continue
        if e.get("event_name") in ("incident.opened","incident.contained","task.failed") and _rate_ok(cur):
            if center.push_alert(_human_event(e), topic="system"):
                pushed += 1; cur["push_count"] += 1
    # 3) protective-halt state change (edge-triggered)
    prot = _protective_state(STATE)
    if prot and prot != cur.get("last_prot"):
        if _rate_ok(cur) and center.push_alert(f"🛑 protective-halt: {prot}", topic="system"):
            pushed += 1; cur["push_count"] += 1
        cur["last_prot"] = prot
    _save_cursor(cur)
    return {"pushed": pushed}

# helpers: _read_past(path, pos) → (new_lines, new_pos);
#          _rate_ok(cur) →每小时 reset، < MAX;
#          _is_critical(line) →keywords: CRIT/protective/throttle/circuit/fail;
#          _human / _human_event →فارسی readable;
#          _protective_state →خواندن ORGANISM-STATE.json protective_mode.
```

**نقطهٔ اتصال در center.py:** در `beat()` (line 394)، پس از بخشِ دایجست، صدا بزن:
```python
try:
    import event_bridge as _eb
    _eb.beat(self)
except Exception: pass  # §۴ fail-soft
```
و یک متد `push_alert(self, text, topic)` به Center اضافه کن که `self._client.send(...)` بزند
(مثل `beat()` خودش برای دایجست می‌زند، line 432).

---

## سناریوی هدف (lead-naghshi، واقعی)

**امروز:** lead-naghshi ۶۰ بار fail→restart می‌خورد (`selfheal-events.jsonl`)، circuit-breaker آن را throttle می‌کند (`chrono.py:1252`، alert به `governor-alerts.md`)، **owner هیچ خبری ندارد** تا وقتی `/start` نزند.

**با event_bridge (فاز A):**
1. circuit-breaker throttle → `opslib.alert()` → `governor-alerts.md`.
2. event_bridge در beat بعدی، خطِ جدیدِ alert را می‌خواند، `push_alert("lead-naghshi throttled: ۶۰ restart")` به topic=system می‌زند.
3. owner در تلگرام push را می‌بیند، به /status می‌زند، پا را diagnose می‌کند.

---

## آمادگی زیرساخت (تصحیح‌شده)
- **مغز** (cortex روی ۸۷۷۲، journal): ساخته‌شده.
- **حافظه** (MemoryStore SQLite+FTS5، ۵ namespace): ساخته‌شده، یادگیری از ۲۳ جولای روشن.
- **event bus** (UnifiedBus): ساخته‌شده ولی `_subscribers` خالی — یک نقطهٔ اتصالِ تمیز.
- **self-model** (۲۶۶ ماژول): ساخته‌شده.
- **تنها کارِ واقعی:** وصل‌کردن. event_bridge (فاز A) مهم‌ترین گام است چون ۶ نقطهٔ Tier 0 را حل می‌کند.

---

## ریسک‌ها و قواعد
- event_bridge **fail-soft**: هرگز center.beat را نکشد (try/except، §۴).
- **rate-limit سخت**: نهایتاً N push/ساعت تا spam نشوی.
- **dedup با cursor**: هر فایل یک offset/pos جدا، restart-safe.
- **صفر secret** در push text (scrub مثل `_scrub` موجود در center.py:426).
- پشتِ flag `OCTOPUS_WIRE_EVENT_BRIDGE` (پیش‌فرض خاموش).
