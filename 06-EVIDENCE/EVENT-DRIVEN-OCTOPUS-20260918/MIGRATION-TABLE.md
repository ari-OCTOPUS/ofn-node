# MIGRATION TABLE — EVENT-DRIVEN-OCTOPUS-20260918 (Phase 0)

لین: `09-LANES/EVENT-DRIVEN-OCTOPUS-20260918` · GOV_VERSION=V8 · LADDER=L2
اندازه‌گیری: 2026-09-18 ~08:45Z روی board138 (192.168.0.138) — `systemctl cat` + خواندن سورس.

ستون‌ها: **unit** (تایمر فعلی) · **کدِ مصرف‌کننده** · **ورودی** (آن‌چه امروز تیک را معنا می‌کند) · **خروجی/رسید** · **گاردها** (هیچ‌کدام تغییر نمی‌کنند) · **تریگر رویدادی هدف** · **منبع رویداد** (چه کسی emit می‌کند).

| # | unit (تایمر) | کد | ورودی امروز | خروجی/رسید | گارد | تریگر هدف | منبع emit |
|---|---|---|---|---|---|---|---|
| 1 | `octopus-imap.timer` (*:6/15، 15m) | `ofn/agents/imap_listener.py` | صندوق Gmail via IMAP poll؛ cursor `last_uid.json` | رسید در `state/imap/legs/lead-inbox/events.jsonl` + `painting.sqlite` (status) + `owner_notify` | مالِ‌ما بودن فرستنده؛ نه seen/حذف ایمیل شخصی؛ dry-run | **IMAP IDLE** (push) → `mail_seen` | `imap_idle.py` (daemon جدید، نازک) |
| 2 | `octopus-reply-alert.timer` (*:0/2، 2m) | `state/revenue-drive/reply_alert.py` | همان IMAP؛ cursor `reply-alert-cursor.txt` | `REPLY_DETECTED` در `tg-inbox.jsonl` + کارت TG + رسید `REPLY_ALERT` | سلف‌میل ignore؛ idempotent به UID؛ هرگز raise | `mail_seen` → اجرا با گیت | `imap_idle.py` |
| 3 | `octopus-owner-reply.timer` (۱m) | `state/revenue-drive/owner_reply.py` | تغییرِ `tg-inbox.jsonl` (پیام مالک)؛ cursor `tg-inbox-cursor.txt` | پاسخ/کارت مالک + رسید | SEND-PAUSED/AUTH-REVOKED؛ authorize؛ یک‌پاسخ‌بر‌ورودی | **PathChanged(tg-inbox.jsonl)** | فایل spool (mesh→138) |
| 4 | `octopus-glass.timer` (*:2/5، 5m) | `ofn/agents/glass_runner.py` | `tg-inbox.jsonl` lane=MONEY + `go_b3` spool؛ seen-set `glass-seen.jsonl` | ACK روی برد + رسید | seen-set idempotency؛ chat_allowed | **PathChanged(tg-inbox.jsonl + go_b3 spool)** | همان دو فایل |
| 5 | `octopus-go-b3-bind.timer` (۲m) | `ofn/agents/go_b3_owner_bind.py poll` | `state/owner_dialogue/go_b3_tg_spool.jsonl` | `go_b3_inbox.jsonl` + `go_b3_pending_registry.json` + کارت‌های resolved | offset + دو-هش (text_sha256)؛ owner-only | **PathChanged(go_b3_tg_spool.jsonl)** | syncer (لپ‌تاپ→138) |
| 6 | `octopus-quote.timer` (*:18/30، 30m) | `ofn/agents/quote_pipeline.py` | لیدهای status=review/quote-requested | quote packet/پیشنهاد + رسید | rate card اجباری؛ بدون قیمت بی‌کارت | `quote_requested` | `imap_listener` (+`reply_alert`) |
| 7 | `octopus-revenue-drive.timer` (00/6:00، 6h) — زنجیرهٔ ExecStartPost | `revenue_drive.py` + `lead_enrich.py` + `money_executor.py` + `revenue_state.py` + `send_queue.py` + `owner_ask.py` + `owner_reply.py` + `reply_runner.py` + `event_notify.py` | کل فایل‌ها (کل قیف) در هر تیک | `REVENUE_REVIEW` + `SEND_CYCLE`/`PACKET_STAGED` + sent-log | standing-authorization (۶۰/روز، بچ ۲۵) · channel-authorization · i7 · STOP-AUTONOMY/HALT · یک‌پاسخ‌بر‌ورودی · رسید هر اثر | تفکیک: `draft_ready`+`lead_enriched`→`send_queue` · `lead_found`→`lead_enrich` · `inbound_reply`+`card_resolved`→`reply_runner` + زنجیرهٔ state · `idle`→`revenue_drive` (مرور) | emit‌های همین runners + `beat_pulse` |
| 8 | `octopus-scheduler.timer` (*:13/15، 15m) | `octopus-mesh/bin/octopus_scheduler.py --once` | inbound events در `octopus-mesh/state/events/` + internal autonomy | task files در `state/runs/` + audit | HOLD_EXTERNAL (فقط send/publish/pay)؛ بدون unit جدید | **PathChanged(octopus-mesh/state/events)** | mesh (wake/events) |
| 9 | `octopus-shopify-watch.timer` (*:24/30، 30m) | `octopus-mesh/bin/store_watch.py` | Shopify Admin API (orders+domain) — **دنیای بیرون، push ندارد مگر webhook** | `store-watch.jsonl` + `FIRST-ORDER-MARKER` | توکن فقط روی همین ماشین | daemonِ مصرف‌کنندهٔ ضربان (interval ~۶۰s) → `order_seen`/`payment_seen`/`stock_changed` | خودش |
| 10 | `octopus-discovery.timer` (daily 02:40Z) | `state/revenue-drive/discovery_runner.py` | ساعت | `DISCOVERY_*` در `receipts.jsonl` + `lead-emails.jsonl` | SEND-PAUSED؛ سقف/بودجهٔ امروز (۶۰ کاندید) | `idle` (beat بیکار) + گارد «صف کهنه/خالی» | `beat_pulse.py` |
| 11 | `octopus-phone-list-notify.timer` (30m) | `state/revenue-drive/phone_list_notify.py` | فایل phone-only queue | پیام TG مالک (change-only) | dedup تغییرمحور | `lead_found` (لید تلفنی جدید) + idle | emit discovery/harvest |

**واحدهای جدید (نازک، بدون منطق کسب‌وکار):**
- `tools/octopus_events.py` — emit/spool/NATS (transport).
- `tools/octopus_beat.py` — ناشر beat (از داخل `ofn-heartbeat.sh` موجود؛ daemon ⇒ نه تایمر).
- `tools/octopus_event_gate.sh` — گیت fail-closed (beat کهنه ⇒ refuse) + سوئیچ shadow/live + مصرف فایل رویداد با رسید.
- `tools/beat_pulse.py` (+`octopus-beat-pulse.service`) — مصرف‌کنندهٔ beat: emit `idle` + sweeper تلاش مجدد. بدون منطق کسب‌وکار.
- `tools/imap_idle.py` — IMAP IDLE (push) → emit `mail_seen`.
- `.path` units: `octopus-evt-<name>.path` + `.service` (هر کدام با گیت).

**نگه‌داشته‌شده‌ها:** تایمرهای غیرپولی (pulse/watchdog/soak/doctor/...) دست نمی‌خورند.

**غیرقابلِ‌رویدادسازی امروز (صادقانه):** Shopify push (webhook) نیازمند endpoint عمومی + HMAC secret (در دست نیست؛ فقط admin token) → فاز ۳ با daemon-ضربان‌محور و ثبت صریح. traffic_seen نیازمند شمارندهٔ کلیک/بازدید (منبع امروز: صفر).
