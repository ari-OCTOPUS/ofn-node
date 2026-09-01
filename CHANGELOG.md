# Changelog

## 2026-08-08 — OPERATOR SAFETY + FULL AUDIT

### کلید خاموشی (Kill Switch) — وصل شد
- **دکمهٔ «🛑 توقف اضطراری»** در هدر پنل. engage سریع (panic button)،
  release با تأیید دو مرحله‌ای.
- endpointها: `POST /api/v1/owner/kill` و `/release`. owner-only.
- state در حافظه (fail-safe: restart = disengage)، audit در
  `release_switch_events` + ledger همه tenantها.
- فیلد `session_id` به `Principal` اضافه شد (هش sha256 توکن).
- **۲۳ تست** در `tests/test_kill_switch.py`.
- فایل‌ها: `node.py`, `http_api.py`, `marketing_store.py`, `run.py`,
  `web/panel.html`, `tests/test_kill_switch.py`.

### داشبورد سلامت برد (Metrics) — زنده
- ماژول `ofn/adapters/sysmetrics.py`: دما (۵ زون)، RAM، load، uptime، دیسک.
- endpoint `GET /api/v1/owner/metrics` (owner-only).
- داشبورد در `web/panel.html`، هر ۳۰s به‌روز. بدون cache.
- ⚠️ هیچ تستی نداره (AUDIT MED-1).

### هشدار خرابی سرویس (Alert)
- `ofn-alert.service`: `OnFailure=` روی `ofn.service`.
- لایه ۱: لاگ محلی `service-alerts.log` (همیشه).
- لایه ۲: تلگرام فقط وقتی `OFN_ALERT_TELEGRAM=1` (default خاموش).
- `ofn/adapters/alert.py` — urllib، بدون وابستگی، never-raises.
- **۹ تست** در `tests/test_alert.py`.
- تست شلیک واقعی systemd انجام شد و سبز شد.

### Bluetooth روی برد
- `hciattach` روی UART9 با firmware BCM4345C5.
- `ap6256-bt.service` (systemd، در بوت خودکار). hci0 UP، BT 5.0.

### NPU Runtime
- `librknnrt.so v2.3.2` نصب شد (از GitHub رسمی Rockchip).
- `NPU-GUIDE.md` ساخته شد.

### ممیزی کامل پروژه
- سه agent موازی همه کد رو در برابر سندهای ابسیدین بررسی کردن.
- [[AUDIT-2026-08-08]] ساخته شد: ۲ CRITICAL + ۲ HIGH.
- همه ۶ audit doc در `docs/audit/` به‌روز شدند.
- هیچ فایلی حذف نشد — فقط کشف و مستندسازی.

- pytest: OFN **۱۵۵۳ تست سبز** + ۵ skip.

## 2026-08-۰۷ (سوم) — UNIFY FINALIZE: چهار نقطهٔ کور بسته شد
- **B-۲ `panel_note`:** brain call پنهان از write path‌های hypno حذف شد.
  `panel_note` حالا فقط یک ردیف log می‌نویسد (source=`panel_note`)، نه
  `brain.answer`. ۴ call site (memory/research/import/obsidian) به‌روز شد.
  تست جدید: `panel_note` دیگر مغز را صدا نمی‌زند.
- **B-۳ consent rename:** ستون `sessions.consent` در hypno به
  `safety_acknowledged` تغییر نام داد (ALTER TABLE RENAME COLUMN). **دادهٔ
  قدیمی migrate شد** (هر دو ردیف حفظ شدند). کد هر دو نام را می‌پذیرد
  (backward-compatible). UI هم به‌روز شد. consent OFN (`may_publish`)
  دست‌نخورده ماند.
- **B-۸ thread safety:** `fugu_core.memory` با `threading.RLock` thread-safe
  شد. تست جدید: ۸ thread × ۱۵ عملیات همزمان بدون خطا. Store قبلی hypno
  از قبل thread-safe بود (هر conn جدا + WAL).
- **فاز ۴ اتصال inline:** `StudioAssistantStore` حالا یک `shared_memory`
  اختیاری می‌گیرد. وقتی chunks محلی جوابی ندارند، از `memory_corpus`
  (shared knowledge) fallback می‌خواند. `ofn/config.py` مسیر `memory_path`
  اضافه شد. `ofn/run.py` memory را ایمن می‌سازد (اگه fugu_core نباشد، None).
- pytest: fugu_core **۲۶** · OFN **۱۵۱۶** · hypno **۶۳** = **۱۶۰۵ سبز**.

## 2026-08-07 (دوم) — UNIFY فاز ۰ تا ۴: مغز و حافظهٔ مشترک
- **`fugu_core` ساخته شد** در `~/shared/fugu_core/` (خالص stdlib، بدون
  وابستگی). شامل `auth` (verify_init_data, ReplayGuard)، `scrub` (redaction)،
  `brain` (RemoteBrain به Sakana)، `memory` (سه‌لایه با FTS5). نصب با `.pth`
  file (pip روی DietPi نیست). **۲۵ تست سبز.**
- **`memory.sqlite` سه‌لایه** ساخته شد: `memory_turns` (اپیزودی)،
  `memory_facts` (معنایی)، `memory_corpus` + `memory_fts` (پیکره). قانون
  جداسازی: لایهٔ ۱/۲ هرگز بین tenantها نشت نمی‌کند؛ فقط لایهٔ ۳ می‌تواند
  `shared` باشد. ۱۳ تست جداسازی سبز.
- **`packs/hypno.yaml`** اضافه شد (tenant چهارم). quota تنظیم شد:
  ziman=۰.۳۵ · lead=۰.۳۵ · studio=۰.۲۰ · hypno=۰.۱۰ = ۱.۰۰.
- **مغز ریموت Sakana برای hypno فعال شد.** `HFM_REMOTE_API_KEY` از OFN
  کپی شد؛ حالا hypno هم از همان مغز `fugu` استفاده می‌کند. تأیید زنده:
  `source: remote:fugu`.
- **۱۳۲ chunk از hypno research_docs** به‌عنوان knowledge مشترک در
  `memory.sqlite` کپی شد (tenant=shared).
- **آنچه دست‌نخورده ماند:** کد OFN و hypno تغییر نکرد (فقط pack‌ها و env).
  assistant.sqlite و hypno.sqlite بازنویسی نشدند — فقط کپی.
- pytest: **OFN ۱۵۱۲ + hypno ۶۲ + fugu_core ۲۵ = ۱۵۹۹ تست سبز**.

## 2026-08-07 — جریان خروجی لید نقاشی (reply/quote + پارتنر CRM)
- **شکاف خروجی پر شد.** تا دیروز لید نقاشی فقط ورودی داشت (ثبت/امتیاز/
  داشبورد) و هیچ راه خروجی. حالا پارتنر می‌تواند **جواب بنویسد**
  (یادداشت/SMS/ایمیل) و **قیمت بدهد** — مثل استودیو، همه چیز از یک درب
  fail-closed می‌گذرد: پیام وارد outbox می‌شود و آری در پنل مالک تأیید/
  رد می‌کند. هیچ‌چیز خودکار از دستگاه خارج نمی‌شود.
- **پارتنر CRM کامل شد.** `lead.html` حالا **جستجو + فیلتر وضعیت + تغییر
  وضعیت** (new→contacted→quoted→won/lost) دارد. تا دیروز فقط ثبت می‌کرد.
- **سه endpoint partner جدید:** `GET /api/v1/painting/leads` (با q/status)،
  `POST /api/v1/painting/leads/<id>/reply`، `POST /api/v1/painting/leads/
  <id>/quote`. الگو از `publish_draft` استودیو کپی شد.
- **سه متد node جدید:** `send_lead_reply`، `send_lead_quote`. یادداشت سبز
  است (interaction + ledger، بدون outbox)؛ SMS/ایمیل/قیمت RED (PII + پول +
  irreversible → double-confirm).
- **وضعیت خودکار:** وقتی reply می‌رود، لید `new` خودکار `contacted` می‌شود؛
  وقتی quote می‌رود، `quoted` می‌شود.
- **query string در handle:** `ApiApp.handle` حالا `query` اختیاری می‌گیرد
  (backward-compatible) تا GET leads بتواند `?q=…&status=…` بخواند.
- **۱۲ تست جدید** در `tests/test_painting_outbox.py` با Node و Outbox و
  Ledger واقعی (نه lambda): note بدون outbox، SMS در RED، quote در RED،
  idempotency، تغییر وضعیت خودکار، owner_queue. **۱۵۱۲ سبز + ۵ skip.**
- زبان UI گرم/غیرفنی: «جواب بنویس»، «قیمت بده»، «آماده برای آری» (D-22).
  هیچ کلمهٔ فنی (outbox/reply/quote/queue) در UI نیست.

## 2026-08-06 (چهارم) — پرورش عمیق مدل لبهٔ سیستم در hypno
- **مغز وصل شد:** `brain.py` حالا `_extract_scores` (نمره از متن فارسی) و
  `EDGE_SYSTEM_PROMPT` دارد. وقتی کاربر در chat نمره می‌دهد، مغز
  `decision_source`/`daily_verdict` را محاسبه و به فارسی ساده جواب می‌دهد.
- **سه endpoint:** `POST /api/edge/decision`، `POST /api/edge/daily`،
  `GET /api/edge/history`.
- **حافظهٔ روزانه:** جدول `edge_daily` (upsert یک‌ردیف‌درروز) در
  `store.py`؛ قانون سه‌روزه روی آن کار می‌کند.
- ۱۹ تست جدید (نمره‌گیری، تجزیه، endpointها، upsert، chat wiring،
  بحران-قبل-از-مغز، idempotency). **hypno ۶۲ تست سبز.**
- هیچ دیتای قدیمی دست‌نخورد؛ `hypno-fugu-mini.service` active.

## 2026-08-06 (سوم) — کد مدل لبهٔ سیستم + RAG در hypno
- `hypno/kernel/edge.py` — ۱۹ تابع خالص stdlib (LES، Agency/Super/Body
  Index، γ_S/γ_R، q شعاعی، daily_verdict، three_red_days، decision_source).
- `hypno/adapters/edge_seed.py` — ۸ chunk متن کامل مدل در RAG.
- `run.py` — `is_edge_topic` + `edge_chunks` (مسیر مستقیم).
- ۳۸ تست مدل. مدل در citations پیدا می‌شود.

## 2026-08-06 (دوم) — جراحی پنل سبا، مرحلهٔ ۲
- **آپلود چندتایی مقاوم‌تر:** یک عکس بد batch را متوقف نمی‌کند (حذف `break`)،
  شمارش واقعی خطاها، آزادسازی بهتر حافظه (`bmp.close()` در `finally`،
  renditions+original موازی). کیفیت حفظ شد.
- **ضربدر حذف روی هر عکس:** «×» بالای هر عکس با تأیید «مطمئنی؟» → فقط همان
  عکس حذف؛ `stopPropagation` روی pointer/touch/click.
- ۶ تست جدید (ضربدر روی عکس، آپلود بدون break، حذف یک عکس).
- **۱۴۹۶ سبز + ۵ skip.**

## 2026-08-06 (اول) — جراحی پنل سبا، مرحلهٔ ۱
- چت‌باکس وسط و بالاتر؛ پنل خالی تیرهٔ بالای چت‌باکس حذف؛ دکمه‌ها مرتب.
- حذف نشت کلمهٔ فنی «RAG» از کپشن پیشنهاد.
- متن‌ها گرم/دخترانه/غیرفنی بازنویسی (chatbox، suggestionها در
  `studio_assistant.py`، placeholder، subtitle).
- گالری: بنر «خوش اومدی سبا جان…» و empty-state گرم.
- ۲۱ تست جدید برای قراردادهای جراحی.
- Added non-destructive audit documentation.
- Added painting CRM foundation and safe owner panel extensions.
- Added B2B/tender/vendor/source-registry plan for next phase.
- Outbound/publish remains off.

## 2026-09-01 — v0.9.0: خودمختاری کامل (afeatures)
- **گوش:** imap_listener (systemd/15min) — reply/bounce/optout/autoreply؛ autoreply هیچ‌وقت engaged نمی‌کند (درس Transport IAU)
- **فالوآپ:** followup_worker — ۲ یادآوری/۷روز/سپس آرشیو (رأی Q4)
- **کوت:** quote_engine + rate_card_builder (OCP واقعی، قفل تأیید مالک Q6) + book_wins
- **زیرساخت:** ۶ تایمر systemd، UTC (ADR-A)، بکاپ شبانه+manifest، اولین restore-drill موفق، heartbeat ساعتی + digest ۷صبح (تلگرام مالک، تست‌شده)
- **حکمرانی:** G-51 بسته، انقضای دامنه‌ها ۱۰-۰۱، identity.json، ADR-B، کمپین رسمی PAINT-L5-001
- ۵ ایمیل واقعی ارسال‌شده (WAL: sent×5، attempts=1) — campaign PAINT-L5-001
- reconcile.py: ۶ invariant بین outbox↔WAL↔leads↔counter — همه سبز
- تست‌ها: tests/test_lane_e_q.py ۱۳/۱۳
