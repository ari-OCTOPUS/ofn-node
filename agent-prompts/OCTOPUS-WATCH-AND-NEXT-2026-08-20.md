---
type: prompt-pack
status: ready
tags: [octopus, prompts, watch, next-agents, directive-8-followup]
created: 2026-08-20
created_by: agent B (ZCode) — به رأی چت مالک 2026-08-20 (~15:00 +10) «پرامپت نویسی کن، بده ایجنتات اجرا کنن»
authority_boundary: R10 پابرجاست — رأی چت جانشین امضا نیست؛ هیچ پرامپتی مجوز فراخوان پولی/اجرای executable ندارد
---

# بستهٔ پرامپت ایجنت‌ها — پیگیری دستور #۸ و نگهبانی اختاپوس (2026-08-20)

> پنج پرامپت آمادهٔ اجرا. ترتیب پیشنهادی: W1 (زنده، هر ۵ دقیقه تا یک ساعت) →
> N1 پس از ۱۵:۴۹ → N2 → N3 → N4 فقط با امضای Ed25519.

---

## W1 — نگهبان اختاپوس (زنده؛ همان چیزی که الان زمان‌بندی شده)

```text
تو ایجنت نگهبان OCTOPUS در F:\backup هستی. این یک اسکن دوره‌ای ۵ دقیقه‌ای است —
مستقل و فقط-خواندنی به‌جز append به لاگ. مخزن: F:\backup (Git Bash).

۱) سلامت ارگانیسم:
   powershell -NoProfile -Command "(Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match 'organism.py' }).ProcessId"
   → باید PID بدهد (آخرین بار 19736). نبود PID = ANOMALY- organism-down.
   powershell -NoProfile -Command "if (Get-NetTCPConnection -LocalPort 8771 -State Listen -ErrorAction SilentlyContinue) {'LISTENING'} else {'dead'}"
۲) تپش و تلمتری T49:
   python -X utf8 -c "import json,os,time; d=json.load(open('_ops/state/ORGANISM-STATE.json',encoding='utf-8')); m=json.load(open('_ops/state/pulse/memory-read-latest.json',encoding='utf-8')); print('beat',d.get('beat'),'| memread',m.get('status'),m.get('memory_reads_per_cycle'),m.get('readback'),'| age_s',round(time.time()-os.path.getmtime('_ops/state/pulse/memory-read-latest.json'),0))"
   → beat باید نسبت به اسکن قبل جلو رفته باشد؛ memread باید status=OK و age<240s باشد؛ DEGRADED یا کهنه = ANOMALY.
۳) spine و producerهای T48:
   python -X utf8 -c "import sqlite3; con=sqlite3.connect(r'file:_ops/state/spine/spine.db?mode=ro',uri=True); print('rows',con.execute('SELECT COUNT(*) FROM events').fetchone()[0], '| v2', con.execute('SELECT COUNT(*) FROM events WHERE schema_version=2').fetchone()[0], '| t48', con.execute(\"SELECT COUNT(*) FROM events WHERE legacy_no_event_time=0\").fetchone()[0])"
۴) وضعیت lease: python -X utf8 _ops/writer_lease.py inspect → اگر held=true توسط session دیگری، طبیعی است (نویسنده فعال).
۵) ثبت: یک خط به انتهای «06-EVIDENCE/OCTOPUS-WATCH-2026-08-20.md» اضافه کن (فقط append):
   `HH:MM | pid=… port=… beat=… memread=… t48=… | OK` یا `HH:MM | ANOMALY: <شرح دقیق>`
۶) اگر ANOMALY:
   - سطحی و instrumentation (مثل memread DEGRADED پایدار >۲ اسکن): فقط rollback فلگ مربوط را «پیشنهاد» بده در همان خط لاگ؛ هیچ ریاستارتی؛ هیچ kill؛ هیچ فراخوان پولی.
   - organism-down یا beat ایستاده >۱۰ دقیقه: در لاگ بنویس CRITICAL + همان‌جا متوقف شو و گزارش بده (بازیابی دست مالک/ایجنت اصلی).
۷) گزارش چت: یک خط خلاصه بده (وضعیت + هر ایراد عیناً — «ایرادا تو چت ذخیره بشه»).
قواعد: read-only به‌جز append به لاگ · git commit نکن · lease نگیر · هیچ تغییری در کد/config.
```

---

## N1 — پس از گزارش ۱۵:۴۹: بستن LIVE-B و suite روی داده واقعی

```text
تو ایجنت پیگیری OCTOPUS در F:\backup. فایل «06-EVIDENCE/T48-EVENT-TIME-MEASUREMENT-2026-08-20.md»
را بخوان (اگر نبود، خودت سنجش بخش ۱ پرامپت زمان‌بندی‌شدهٔ قبلی را اجرا کن).
سپس: اگر هر دو producer رویداد دارند و stdev>10ms، گیت LIVE-B را ارزیابی کن
(independent_sources>=2 · stdev>10ms هر دو · late-arriving واقعی>=1).
اگر LIVE-B=PASS: نسخهٔ فقط-خواندنیِ suite پانزده‌تایی (_ops/tests/test_bitemporal_spine_spec.py)
را روی دادهٔ واقعی spine اجرا کن — یک wrapper بنویس که ردیف‌های واقعی را به
MemoryRecord نگاشت کند (occurred_at/recorded_at از ستون‌ها؛ رکوردهای legacy فقط در
بازوی naive). گیت‌های strict باید روی دادهٔ واقعی هم صفر future-use بدهند.
حکم نهایی را در 06-EVIDENCE/BITEMPORAL-REAL-DATA-2026-08-20.md بنویس.
زیر lease بنویس (python -X utf8 _ops/writer_lease.py acquire …) و در پایان release.
هیچ فراخوان پولی؛ هیچ executable=true.
```

---

## N2 — ریاستارت امن brain.daemon برای فعال شدن کامل producer_1

```text
تو ایجنت زیرساخت OCTOPUS در F:\backup. brain.daemon (PID آخرین بار 25680، از
19/08) هنوز کد قدیم model_router دارد → رویدادهای T48 فقط از organism می‌آیند.
مأموریت propose-only:
۱) سرپرست فعلی daemon را شناسایی کن (parent=cmd /c outputs\launch5.cmd — فایل را
   در 4d_system/outputs پیدا و بخوان؛ ببین بعد از خروج daemon دوباره بالا می‌آورد یا نه).
۲) اگر بازیافت‌پذیر است: baseline بنویس (PID/beat/تعداد رسید امروز) + پروتکل
   ریاستارت گام‌به‌گام + شرط rollback را در 06-EVIDENCE/DAEMON-RESTART-PLAN-2026-08-20.md.
۳) اگر بازیافت‌پذیر نیست یا مبهم است: فقط گزینه‌ها را بنویس، اجرا نکن.
هیچ ریاستارتی همین جلسه اجرا نکن مگر با تأیید صریح مالک در پاسخ به همین سند.
```

---

## N3 — روال بازتولید ابسیدین (labels → NOW → CURRENT-TRUTH)

```text
تو ایجنت مستندات OCTOPUS در F:\backup. با هر تغییر وضعیت مهم:
۱) _ops/state/labels.json را با لیبل‌های تازه (value/status/evidence_path/hash/updated_at)
   به‌روز کن — فقط چیزهایی که شاهد داری.
۲) python -X utf8 _ops/scripts/render_now.py  (بعد --check برای اطمینان از nodrift)
۳) python -X utf8 -c "…sync_truth_note…" با مقادیر مشاهده‌شده (beat/PID/گیت‌ها)
۴) زیر lease؛ commit فقط فایل‌های خودت؛ سپس release.
الگوی کامل: commit 43d2860 امروز.
```

---

## N4 — اجرای LIVE-D (فقط پس از امضای Ed25519 مالک)

```text
این پرامپت تا زمانی که مالک امضای Ed25519 خودش را روی
«02-DECISIONS/PRE-REG-FULL-LOOP-FLASH-2026-08-20.md» ثبت نکرده، اجرا نشود
(رأی چت کافی نیست — R10). پس از امضا و LIVE-B=PASS: طبق همان کارت منجمد —
۱۲ task واقعی، هر ۵ دقیقه، سقف AU$0.50، concurrency=1، هر task ابتدا از
memory_read_loop با decision_time بخواند، همهٔ خروجی‌ها proposal_only،
رسید کامل با task_id/run_id، HARD_STOP خودکار، گزارش انحراف در صورت نقض.
```
