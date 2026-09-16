# TCB-HALT-ROOT-CAUSE — چرا دیمون ۴d در 2026-08-16 15:39:45 ایستاد

run: CL01-191-20260818-2233 · طبق فرمان مالک (RESTART گیتِ این سند است). هیچ restart اجرا نشد.

## ۱. invariant دقیقِ شعلۀگرفته

```text
کد:      4d_system/brain/automation.py :: _job_guard()  (خطوط ~647–675)
شرط:     elif tcb.get("enforcement") and tcb.get("tampered"):
             halt_reason = "نقضِ مرزِ اعتماد (TCB)"
منبع:    guardrails.check_invariants() — مقایسهٔ هشِ فایل‌های TCB با
         «manifest مرزِ اعتماد» (R13/C-013؛ معرفی: commit 6fc0f4b، 2026-08-15 22:48)
شاهد لاگ: daemon-launch3.err.log:
         15:39:45,923  task.failed   ⚠️ نقضِ مرزِ اعتماد (TCB) — توقفِ حفاظتی
         15:39:45,926  decision packet [approve] → queued (not-configured)
         15:39:45,927  ERROR daemon: protective HALT (invariant violation) → stopping
         15:39:45,947  daemon stop · ticks=448 · proposals=0 · errors=0
```

## ۲. رویداد محرک، بازهٔ git و آشتی‌سازی

```text
پنجرهٔ رخداد:  صبحِ 2026-08-16 «self-run» — ده‌ها کامیت بین 13:00–15:38
              (seams/SELFRUN/AUTOFLOW) فایل‌های محدودهٔ manifest را تغییر دادند
              بدون اینکه manifest قبلاً بازسازی شود.
آشتی‌سازی:     commit 8bdd9c7 در 15:43:16 — «both TCB cards applied with owner
              authorization … manifest rebuilt (14 digests + NO-GO packet)» —
              یعنی ۳ دقیقه و ۳۱ ثانیه پس از HALT، تغییراتِ مجاز اعمال و manifest
              بازسازی شد و ناهمخوانی رفع شد.
دقت:          daemon.py/automation.py از 6fc0f4b (Aug-15 22:48) تا امروز
              دست‌نخورده مانده‌اند — drift از فایل‌های دیگرِ محدودهٔ manifest آمده،
              نه از خودِ این دو.
```

## ۳. پاکت approve معلق

آن پاکت، خودِ «درخواست تأییدِ HALT» بود با مسیر تحویلِ not-configured — موضوعش
منقضی‌شده است (رویدادش مصرف شد). restart تازه اگر invariant دوباره بجنبد،
پاکت تازه می‌سازد؛ پاکت قدیمی نه معتبر است و نه خطرناک — فقط سابقه.

## ۴. چرا restart دوبارهٔ فوری همان HALT را نمی‌گیرد (با یک شرط)

```text
امروز (OBSERVED، فقط‌خواندن):
  git status 4d_system/brain           → تمیز (صفر dirty)
  guardrails.check_invariants()        → anchors_ok=true · tampered=false ·
                                         mismatches=[] · signature=valid
شرط cwd:  اجرای من از ریشهٔ 4d_system پیام داد «REFERENCE_DIR='./' مرزِ نامعتبر
          (C-013)؛ fallback» و enforcement=false — یعنی چکِ manifest به cwd حساس است.
پس pre-check الزامی restart: اجرای daemon از working directory رسمی خودش
          (F:\backup\4d_system) تا enforcement روشن و چکِ manifest فعال باشد؛
          و در ۱۰ دقیقهٔ اول، لاگ نباید «protective HALT» تازه داشته باشد.
```

## ۵. فرمان restart (bounded — عیناً از DAEMON-RESTART-PROPOSAL §2)

یک تلاش · timeout ۱۰ دقیقه · بدون scheduler/شبکه · kill = `touch outputs/daemon.stop`
(مسیر رسمی خود دیمون) و در صورت بی‌پاسخی فقط `taskkill /PID <pid> /F` همان PID ·
لاگ: `outputs/daemon-launch4.err.log` · cwd: `F:\backup\4d_system` · env: بدون تغییر
(`OCTOPUS_WIRE_MEMORY_GATE` همچنان خاموش).

## ۶. حکم

HALT **خرابی نبود؛ محافظ درست کار کرد**: drift غیرمجاز TCB → توقف → آشتی‌سازی مالک‌مجاز
۳٫۵ دقیقه بعد. امروز drift صفر است و امضا معتبر؛ با رعایت cwd، restart امن است —
اما طبق فرمان مالک، تا مرور این سند و دستور صریح «restart approved» اجرا نمی‌شود.

## شواهد

p2a-halt-forensics.txt (کامیت‌های پنجره + کد گار) · p2b (کد گار + manifest + تمیزی brain)
· p2c-invariant-now.txt (چک زندهٔ امروز + هشدار REFERENCE_DIR) · daemon-launch3.err.log (tail در F1/R01).
