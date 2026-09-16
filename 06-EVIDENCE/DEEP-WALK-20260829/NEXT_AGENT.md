---
type: handoff
schema: deep-walk-next-agent/1
experiment_id: deepwalk-20260829-discovery
created: 2026-08-29T06:35Z
gate_completed: DISCOVERY_ONLY (فاز ۱+۲)
next_gate: SAFE_TESTS (نیازمند تایید صریح مالک)
---

# NEXT AGENT — از اینجا ادامه بده

## ⚡ به‌روزرسانی 2026-08-29 عصر — SAFE_TESTS انجام شد؛ گیت بعدی: PATCH_PROPOSAL

- سه اجرای واقعی روی کپی fixture انجام شد (خروجی‌ها در `safe-tests/`): ‏memory.db لپ‌تاپ **HEALTHY** (exit 0)، ‏spine.db لپ‌تاپ و organism.db برد180 هر دو **BOTTLENECK:use** (exit 2).
- **ریشه‌ی مکانیکی write-only پیدا شد**: ‏`consume_tick` در `cycle_context.py:196-199` فقط ID می‌گیرد و ردیف stub با `text=needle` می‌سازد؛ محتوای واقعی هرگز وارد context تصمیم نمی‌شود. و incrementکننده‌ی `future_use_count` روی ۱۸۰ اصلاً وجود ندارد (obs-dw29-022).
- C-DW29-01 رایتیفاید شد (کد ملاک؛ نقش‌ها در CURRENT-TRUTH ثبت شد) · C-DW29-02 با شاهد حل شد (FTS سالم؛ علت = stub + needle-mismatch).
- `memtest_live.py` ارتقا یافت: کپی صفحه‌به‌صفحه (‏pages=64, sleep=0.2، قفل بین stepها آزاد) + `integrity_check` اجباری پس از کپی + `busy_timeout=5000`.
- **دو پچ پیشنهادی برای گیت PATCH_PROPOSAL (متمرکز و کوچک):**
  1. `consume_tick` → پاس‌دادن `SpineReadStore` واقعی به‌جای stubهای ID-only (+ هم‌خوانی needle با شکل متن `event_type+subject`).
  2. روی ۱۸۰: increment واقعی `future_use_count` هنگام استفاده‌ی receipt در تصمیم (یال نانوشته).
- پاک‌کاری معلق با تأیید مالک: فایل مرده `_ops/state/memory.db` (خالی) · بلاک debug هاردکد `debug-4ab476.log` در `memory_read_loop.py` (obs-dw29-020).

## چه شد (صبح — DISCOVERY)

فاز ۱ (کشف) و فاز ۲ (baseline) فقط-خواندنی کامل شد. صفر تغییر سیستمی.
خروجی‌ها: `D1-REALITY-MAP.md` (معماری واقعی) · `D2-EVIDENCE-INVENTORY.json` (snapshot ماشین‌خوان) ·
`observations.jsonl` (۱۸ FACT) · `contradictions.jsonl` (۶ تناقض، ۲ تای آن نیازمند تصمیم مالک).

## سه یافته‌ای که مسیر تست را تعیین می‌کنند

1. **حافظه «خوانده می‌شود» ولی «بی‌سیگنال» است**: حلقه خواندن زنده است (reads=3/cycle, readback=read_ok)
   اما متن experimentها فقط `"spine"` است و `search_vault` همیشه خالی.
   → تست M3-Retval و M4-Use باید **کیفیت محتوا** را بسنجند، نه فقط وجود رکورد.
2. **گلوگاه Use در قیف تصمیم است**: ۲۱ proposal-issued → ۳ decided (لپ‌تاپ)؛
   روی ۱۸۰: ۶۱۷۷ episode → ۹ lesson و future_use_count=0.
   → معیار نهایی `decisions_changed > 0` دقیقاً همین‌جا قابل اندازه‌گیری است (جدول decided / decision_evidence).
3. **API واقعی ۱۳۸ کارت مالک است نه decide()**: هر تستی که با فرض decide()/approve() نوشته شود
   مثل RED test قبلی ۴/۴ fail می‌شود (این بار به‌درستی فهمیدیم چرا).
   → یال واقعی برای بستن: `ساخت OwnerDecision card توسط نود → تایید مالک → Outbox.enqueue`.

## نقشه‌ی تست به مسیرهای واقعی (برای نویسنده memtest.py / chaintest.py)

### memtest.py — لپ‌تاپ
| سطح | هدف دقیق | ابزار |
|---|---|---|
| M1 Write | insert در `_ops/state/spine/spine.db` با idempotency_key یکتا (روی **کپی** fixture) | sqlite copy + event_spine |
| M2 Read | همان evt_id را با فیلتر bitemporal برگردانید؛ FUTURE_DATA باید drop شود نه اصلاح | cycle_context._eligible |
| M3 Retrieval | FTS5 روی `memory.db.memory_fts` با مفهوم/زمان؛ سنجه: رتبه مورد درست | memory_store query |
| M4 Use | پس از write، `decided` جدید در spine.db با reference به memory_id؟ سنجه: decisions_changed>0 | event_type=decided |
| M5 Transfer | ایجنت تازه با خواندن `memory-context-latest.json` بدون توضیح شفاهی ادامه دهد | consume projection |

قرارداد مرجع (از خود کد): `_ops/memory_read_loop.py` سطر ۸–۱۶ (bitemporal + شمارنده + read-back).

### memtest.py — برد ۱۸۰
مسیر واقعی: `/opt/octopus/lab/lab-data/organism.db` (روی کپی fixture):
- Write: `events` + hash/node_seq → `episodes`
- Read: `memory_read_receipts` (باید receipt با purpose/register شود؛ ok=1)
- Use: `decision_evidence.receipt_id → receipt_id` و سنجه `future_use_count>0`
- Learning: `episodes → lessons` (الان ۶۱۷۷→۹؛ حداقل باید مسیر کد پیدا شود یا نبودش FACT ثبت شود)

### chaintest.py — زنجیره بین‌بردی
- 180 producer: `/root/octopus-mesh/outbox/*.payload.json` (نمونه‌های زنده امروز موجود)
- 138 consumer: `/home/ari/octopus-mesh/inbox` + receipts (۴۳۳۵ موجود برای idempotency-check)
- 182 شاهد: `/root/octopus-mesh/state/witness/{events,verdicts}.jsonl`
- invariantها برای X1: payload_hash یکسان در مسیر · بدون witness هیچ receipt · idempotency (تکرار enqueue فقط یک receipt) · dead-letter با SUPERSEDED_TYPE_MISMATCH قابل بازتولید نیست بدون نوع‌تغییر
- ⚠️ قبل از هر تست زنده: گیت `CROSS_NODE_TESTS` از مالک؛ همه fixtureها کپی، هیچ صف production لمس نشود.

## کارهای مانده به ترتیب

1. **مالک دو تصمیم**: (الف) نقش‌های ۱۳۸/۱۸۲ در مستندات ratify شود (C-DW29-01)؛ (ب) سرنوشت فلگ vault_bridge (C-DW29-02: عمدی یا باگ؟).
2. گیت `SAFE_TESTS` از مالک بگیرید → memtest.py روی fixture لپ‌تاپ (M1–M5).
3. گیت `FAULT_INJECTION_LOCAL` → سناریوهای duplicate/corrupt/restart/clock-skew فقط روی کپی‌ها.
4. گیت `CROSS_NODE_TESTS` → chaintest.py روی fixtureهای سه نود.
5. بدهی‌های کشف‌شده برای بررسی بعدی: انبار ۱۱۹۸تایی outbox ۱۸۲ (C-DW29-05) · معنای verdict=disputed با delivered_acked (C-DW29-06) · فایل مرده state/memory.db (C-DW29-04).

## قواعد ایمنی که همین نشست رعایت کرد (ادامه بده)

- `.env` هرگز خوانده/چاپ/کامیت نشود؛ رازی ثبت نشد (D2 sanitize شده).
- پورت‌های 8791–8796، panel.html، Telegram auth، tunnel config لمس نشدند.
- هیچ restart/install/migration/push/merge انجام نشد؛ همه‌ی SQLiteها با `mode=ro` باز شدند.
- 180 و 182 git نیستند — هر «کامیت» روی آن‌ها بی‌معناست؛ فقط 138 و لپ‌تاپ lineage دارند (هرگز push متقاطع نکن).
