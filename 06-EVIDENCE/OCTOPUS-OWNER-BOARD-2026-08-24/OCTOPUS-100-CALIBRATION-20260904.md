# OCTOPUS-100 — چک‌لیست ۱۰۰ موردی برای عملگراتر شدن و اثر واقعی

شناسه: `OCTOPUS-100-CALIBRATION-20260904`
هدف: هر آیتم یک تست/سنجه/اقدام اجرایی است که اثر واقعی را اندازه بگیرد — نه ادعا.
قاعده: هر مورد باید `verify` + `expect` داشته باشد؛ بدون آن، بسته‌شدنش ادعاست.
مبنای گردآوری: MISSING-WIRING-50 · FINDINGS-LEDGER · SCAN A/B/C · HARMONY-MERGER · GATES-31 · پنج دور اعتبارسنجی

---

## چگونگی استفاده
هر آیتم: `id · target · verify → expect · owner-gate?` —
بعد از اجرا: نتیجه در SEASON-LOG با شماره‌ی آیتم ثبت شود.
موارد دارای گیت مالک با ⚡ نشانه‌گذاری شده‌اند.

---

## A) اثر واقعی پول (۲۰)

```
A01 · اولین پرداخت وریفایِ سیزن-۵ در لجر
     verify: sqlite lead_store → payment.verified=1 در 30 روز
A02 · Manly $306.90 مابه‌التفاوت پاسخ/بسته شود                        ⚡
A03 · فاکتور Painter licence file موجود در والت
A04 · Workers-comp cert موجود در والت
A05 · DET reply با [NAME] پر شده (دستی مالک)                          ⚡
A06 · اولین مناقصه buy.nsw برداشت شده (۰ کلیک)
A07 · اولین quote سمت مشتری با OwnerRelease dual-confirm              ⚡
A08 · اولین order-ingest واقعی شاپیفای → lead_store
A09 · VAUCLUSE $78,500 یا DEE WHY $25,500 پاسخ/بسته
A10 · revenue_runway_days از لجر محاسبه شود (نه پیش‌بینی)
A11 · ATO reserve 30% جدا شود (tools/treasury)
A12 · cashflow 7-day از لجر خوانده شود
A13 · quote_pipeline سرعت: از رویداد تا card < 1h
A14 · idempotency: دو اجرای quote → یک QT
A15 · rollback: خطای DB → state نیمه‌کاره نماند
A16 · imap پارس ۵ نمونه: reply/quote/bounce/spam/none
A17 · fingerprint پایدار بین دو اجرا
A18 · H1 harvest بدون N-execution برای یک verdict
A19 · paid_call ledger: هر API پولی ثبت شود
A20 · ماهانه: revenue-vs-cost گزارش مالک
```

## B) خودمختاری امن (۱۵)

```
B01 · M5 فعال روی بورد + verify دو-مرحله‌ای                            ⚡
B02 · cognitive_wake واقعی: 138→180→reply→138
B03 · reply-outbox 15min: 0 pending پس از هر run
B04 · brain_wake فایلی: state ماندگار بین تیک‌ها
B05 · patch_proposer: یک PR خودنوشت روی CLASS_A
B06 · loop budget: >3/24h بلوکه شود (تست بقا)
B07 · GAP-LEDGER: هر verify_status پر شود یا OWNER_DECISION
B08 · GAP-065 fix روی بورد verify شود (نه فقط تست)
B09 · GAP-018 fix روی بورد verify شود (quiet ≠ dead)
B10 · conservation: تست واقعی (مالک ۲۴h غایب → صفر send)
B11 · doctor silent 3-tick → conservation (dead-man معکوس)
B12 · glass_runner: پاسخ واقعی به /status از تلگرام مالک
B13 · learning_feeder: run تازه در runs/auto-*
B14 · release_pipeline: سه reach به receipt
B15 · repair_api: یک اقدام واقعی روی CLASS_A با dry=false
```

## C) حافظه و مغز (۱۵)

```
C01 · cognitive worker reply به ۱۳۸ برگردد (pending→0)
C02 · wake-dedup: دو تیک متوالی → یک wake
C03 · semantic_memory از cortex consolidate فایل بنویسد
C04 · chrono.db هر beat جدید بنویسد
C05 · memory.db صفربایت‌ها حذف/ادغام شوند
C06 · brain_probe روی ۱۸۰ پاسخ بدهد (نه unverifiable)
C07 · llama محلی به یک prompt جواب بدهد (زنده)
C08 · mesh reply از 180→138 با sha (نه evidence خالی)
C09 · self_model روی بورد تازه شود (سن < ۲ ساعت)
C10 · cockpit کارت self_model را بخواند (نه stale)
C11 · memory consolidation 4d دوباره فعال شود
C12 · observatory روی مسیر bومی بازگردانده شود
C13 · cortex-vs-mesh حافظه مرجع واحد تعیین شود (F2)
C14 · Event Spine طراحی شود با trace_id
C15 · board_packs 3/3 در هر round دوباره تأیید شود
```

## D) زیرساخت و برد‌ها (۱۵)

```
D01 · مش سه‌برد: هر outbox هر ساعت صفر شود
D02 · reply-outbox 180: pending صفر بماند
D03 · NATS: تصمیم رمز core یا گزینه ب تثبیت
D04 · ۱۸۰ wake consumer: worker واقعاً wake بخواند
D05 · ساعت ۱۳۸ NTP sync مانده باشد
D06 · ساعت ۱۸۲: sync واقعی تأیید شود
D07 · mesh سه برد git-versioned بماند (commit جدید = تغییر ثبت)
D08 · inter-board key: ssh 138→180/182 بدون password
D09 · sensorium 182: بدون D-state یا restart
D10 · stability_monitor 9101: مالک مشخص و در رجیستر
D11 · events.jsonl 182: پرون داشته باشد (۲۹MB رشد نکند)
D12 · brainwake timer: هر ساعت fire شود
D13 · reply timer: هر ۱۵ دقیقه fire شود
D14 · glass timer: هر ۵ دقیقه fire شود
D15 · digest/followup: حذف یا rebuild با رأی
```

## E) امنیت و حاکمیت (۱۵)

```
E01 · GOV-V6: هر merge فقط با رأی معتبر (canary رد شود)
E02 · require-fresh-base: هر PR قدیمی قرمز شود
E03 · CODEOWNERS * @Elahe-z @aram-ui بماند
E04 · هیچ PR self-authored به CLASS_Z دست نزند
E05 · ALLOWLIST VALID_REVIEWERS فقط این دو
E06 · نقدی: bot approval صفر اثر
E07 · shopify webhook: secret بدون env = connector صفر
E08 · kill-switch فعال = همه‌چیز بسته
E09 · repair_api بدون dry=false = هیچ اجرا
E10 · repair_api CLASS_Z = رد
E11 · three counters: EXTERNAL_ACTIONS/LAN/MAY_AUTH صفر
E12 · surface های ۴گانه evidence[] جدابمانند
E13 · GAP-MESH-TRUST-001: git versioned روی هر ۳ برد
E14 · runtime_sha_verified: از unknown به واقعی
E15 · locks doc: هر عدد measured_at داشته باشد
```

## F) خودآگاهی و گلاس (۱۵)

```
F01 · self_model.json: سن <۲ ساعت در هر سیکل
F02 · cockpit ۴ حالت صحیح: سبز/زرد/قرمز/خاکستری
F03 · glass /doctor: verdict دکتر را نمایش دهد
F04 · glass /money: لجر یادگیری را نمایش دهد
F05 · glass /queue: OWNER-QUEUE.md را نمایش دهد
F06 · glass /receipts: رسیدهای اخیر را نمایش دهد
F07 · pulse heartbeat خط «دکتر:…» داشته باشد
F08 · pulse نبض صندوق‌خالی = healthy·quiet (نه dead)
F09 · probe oneshot: تازگی آخرین اجرا (نه inactive)
F10 · activating units = skip (نه قضاوت کاذب)
F11 · probe_pulse نویسنده‌های تازه را چک کند
F12 · brain_probe روی ۱۸۰: status واقعی (نه unverifiable)
F13 · هیچ verdict پنجمی (فقط چهار حالت)
F14 · disabled = UNKNOWN عمدی (نه پنهان)
F15 · journal permission: یک UNPROBED صادق بماند (یا رأی رفع)
```

---

## ثبت نتیجه

پس از اجرای هر آیتم: در SEASON-LOG با شماره (مثلاً OCT-100/A01) ثبت شود.
هر هفته: count PASS/FAIL/⚡ — گزارش کالیبراسیون مالک.

```text
TOTAL = 100
owner-gate (⚡) = 5
auto-testable = 95
currently PASS (تخمین بر اساس Round 5-33) = ~31
currently FAIL/PENDING = ~69
```

این ۱۰۰ مورد، مرزِ بین «اختاپوس نمایشی» و «اختاپوس واقعاً عملگرا» را تعریف می‌کند. هر مورد که سبز شود، ارگانیسم یک قدم از ادعا به واقعیت نزدیک‌تر می‌شود.
