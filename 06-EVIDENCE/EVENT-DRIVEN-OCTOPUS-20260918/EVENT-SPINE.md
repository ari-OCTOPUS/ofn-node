# EVENT SPINE — EVENT-DRIVEN-OCTOPUS-20260918

لین: `09-LANES/EVENT-DRIVEN-OCTOPUS-20260918` · GOV_VERSION=V8 · LADDER=L2 · نود اجرا: board138 (192.168.0.138)

## معماری در یک نگاه

```
ofn-heartbeat.service (daemon ۳۰s، موجود)                    [ساعت سیستم]
   └─ tools/octopus_beat.py ──► state/events/beat.json  (فایل مهر زمانی)
                             └─ PUB octopus.beat.138 ──► nats-leaf 127.0.0.1:4223
                                                          └─► هاب لپ‌تاپ JetStream OCTOPUS_EVENTS (octopus.>)
                                                              └─ vault-event-ledger (durable) ─► 06-EVIDENCE/.../jetstream-ledger/

runners موجود (بدون بازنویسی مغز) ── emit ──► state/events/inbox/<kind>/<utc>-<sha8>.json
   (reply_alert, imap_listener, send_queue, lead_enrich, money_executor,
    go_b3_owner_bind, store_watch, discovery_runner, revenue_drive)
                    │
                    ├─ فایل رویداد = تریگر (systemd .path روی همان دایرکتوری، inotify کرنل)
                    ▼
        octopus-evt-<name>.path  →  octopus-evt-<name>.service
                    ▼
        tools/octopus_event_gate.sh <name> <dirs|-> -- <cmd>
             ۱) اگر beat کهنه (>150s) ⇒ refuse (exit 75) + رسید EVENTS_GATED_STALE_BEAT   ← fail-closed
             ۲) flock per-unit ⇒ هرگز دو اجرای هم‌زمان روی یک مسیر پول
             ۳) mode=shadow ⇒ اجرا نمی‌کند، رسید SHADOW_WOULD_RUN + مصرف فایل
             ۴) mode=live   ⇒ اجرا؛ rc=0 ⇒ فایل‌ها به processed/ + رسید EVENTS_RAN
                                rc≠0 ⇒ فایل می‌ماند + رسید FAILED؛ sweeper دوباره trigger می‌کند

tools/beat_pulse.py (octopus-beat-pulse.service، daemon):
   • اگر ledger ≥۱۰ دقیقه ساکت و beat تازه ⇒ emit «idle»  (تریگر کشف پیوسته و مرور زنجیره)
   • sweeper: فایل‌های گیرکردهٔ inbox را دوباره touch می‌کند (retry با backoff ذاتی)
   • اگر beat کهنه ⇒ هیچ‌کدام (fail-closed)
```

## فایل‌ها و واحدهای جدید

| مسیر | نقش |
|---|---|
| `/home/ari/ofn/tools/octopus_events.py` | transport: emit → فایل اتمیک + ledger + PUB خام NATS (best-effort) |
| `/home/ari/ofn/tools/octopus_beat.py` | ناشر beat (از داخل ofn-heartbeat.sh صدا زده می‌شود؛ seq ماندگار) |
| `/home/ari/ofn/tools/octopus_event_gate.sh` | گیت fail-closed + سوئیچ shadow/live + flock + مصرف رویداد |
| `/home/ari/ofn/tools/beat_pulse.py` | مصرف‌کنندهٔ beat: idle + sweeper (بدون منطق کسب‌وکار) |
| `/home/ari/ofn/tools/imap_idle.py` | IMAP IDLE (push واقعی Gmail) → رویداد `mail_seen` |
| `/home/ari/ofn/tools/ziman_watch.py` | سنسور فروشگاه به‌جای تایمر: orders هر ۶۰s، stock هر ۳۰۰s، full هر ۶۰۰s |
| `octopus-imap-idle.service` | daemon بالا |
| `octopus-ziman-watch.service` | daemon بالا |
| `octopus-beat-pulse.service` | daemon بالا |
| `octopus-evt-{mail,inbound,leads,send,cards,owner,idle,orders,mesh}.{path,service}` | ۹ تریگر رویدادی |
| `state/events/mode.json` | سوئیچ per-kind: `shadow` (پیش‌فرض) / `live` |
| `state/events/{ledger.jsonl,inbox/,processed/,shadow-consumed/,gate-receipts.jsonl}` | خودِ اسپاین |
| `state/events/timer-sunset.jsonl` | رسید disable تایمرها + مسیر preimage |

## رویدادهای دامنه (kind → منبع emit → مصرف‌کننده)

| kind | emit در | مصرف‌کننده (unit) |
|---|---|---|
| `mail_seen` | `imap_idle.py` | mail → reply_alert + imap_listener |
| `inbound_reply` | `reply_alert.py`، `imap_listener._receipt` | inbound → reply_runner + quote_pipeline + owner_ask + state |
| `quote_requested` / `quote_accepted` / `opted_out` / `bounce` / `autoreply` | `imap_listener._receipt` | inbound |
| `lead_found` | `discovery_runner.py` (diff روی leads_master) | leads → lead_enrich + phone_list_notify + money_executor |
| `lead_enriched` | `lead_enrich.py` | send |
| `draft_ready` | `money_executor.py` (فقط پکت تازه) | send → money_executor + send_queue + revenue_state |
| `packet_staged` | `send_queue.py` (staging) | فقط سابقه — عمداً تریگر نیست (ضد کاسکید) |
| `packet_sent` / `packet_failed` | `send_queue.py` | سابقه + زنجیرهٔ state |
| `card_resolved` | `go_b3_owner_bind.emit_decision` | cards → state + money_executor + owner_ask + reply_runner |
| `order_seen` / `payment_seen` / `stock_changed` | `store_watch.py` v2 | orders → revenue_state |
| `revenue_review` | `revenue_drive.py` | سابقه |
| `idle` | `beat_pulse.py` | idle → money_executor + send_queue + revenue_state + revenue_drive + discovery_runner |
| `owner_message` (فایل‌محور) | — | owner → owner_reply + event_notify + glass_runner + go_b3 binder |

## چرا fail-closed واقعی است

- تنها منبع ضربان، همان daemon موجود `ofn-heartbeat` است (نه پروسهٔ جدید).
- گیت پیش از هر اجرا مهر زمانی `beat.json` را می‌سنجد؛ کهنه ⇒ هیچ runnerی اجرا نمی‌شود و رسید `EVENTS_GATED_STALE_BEAT` ثبت می‌شود.
- اگر NATS/هاب بخوابد، خودِ beat همچنان روی ۱۳۸ نوشته می‌شود (منبع محلی)، ولی مسیر بین‌نودی (JetStream ledger) می‌ایستد — این تفکیک عمدی است تا خوابِ لپ‌تاپ، موتور پول را نکشد.
- اثبات تجربی: `06-EVIDENCE/.../FAILCLOSED-PROOF.md`

## نکات طراحی (تصمیم‌های ثبت‌شده)

1. **تریگر = فایل روی inotify** (`.path`) نه daemon رابط: هیچ orchestrator جدیدی ساخته نشد؛ systemd نقش dispatcher را دارد.
2. **مغز runners دست‌نخورده**: هر تغییر فقط emit/گارد افزودنی بود (پری‌ایمیج برای همه).
3. **کاسکید ممنوع**: staging عمداً `packet_staged` (بی‌تریگر) emit می‌کند؛ فقط پکتِ *تازه از تهیه‌کننده* `draft_ready` است.
4. **flock**: هرگز دو اجرای هم‌زمان روی یک مسیر پول.
5. **shadow پیش‌فرض**: `mode.json` پیش‌فرض shadow است؛ فلیپ فقط per-kind و پس از شاهد شادو.
