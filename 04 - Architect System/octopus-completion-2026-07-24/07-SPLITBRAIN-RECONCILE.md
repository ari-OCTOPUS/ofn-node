---
type: reconciliation-plan
title: OCTOPUS Split-Brain Reconciliation (live ⇄ master)
date: 2026-07-24
owner: ari
status: proposed
risk: LOW (clean merge, zero content conflict) — but a DELIBERATE deploy (organism halted + tested)
---

# 🧠🔗 OCTOPUS — پلنِ آشتیِ split-brain (زنده ⇄ master)

## ۰) وضعیت (راست‌آزمایی‌شده 2026-07-24)
- **زنده** = `claude/octopus-event-bridge-aligned @ 9c49f17` (ارگانیسمِ در حالِ اجرا روی 8771/8772).
- **master** = `@ f363024`. نقطهٔ جدایی = `16d44e8a`. master **۱۰ کامیت جلو**، زنده **۲ کامیتِ خودش**.
- **کلیدِ ماجرا:** تنها ۲ فایلی که هر دو شاخه دست زده‌اند (`telegram_center/event_bridge.py`, `telegram_center/center.py`) **بایت‌به‌بایت یکسان‌اند** → event_bridge روی هر دو خط به محتوای یکسان رسیده.
- **نتیجه: `git merge master` روی زنده = صفر conflict.** کارِ منحصربه‌فردِ زنده در محتوا ≈ فقط یک سندِ handoff.

## ۱) زنده با این آشتی چه چیزی از master می‌گیرد (همه flag-off / propose-only)
| کامیت | چه می‌آورد |
|---|---|
| `6808c1a` + `3e6e2db` + `f87ebf0` | **کلِّ ماشینِ C6** (c6_trigger + research stack + c6_state_machine) — وابستگی‌هایی که الان زنده ندارد |
| `81c7380` | **۲ فیکسِ باگِ live-audit**: memory-checksum blind-spot + architect-STOP watchdog gap (تصحیحِ واقعی) |
| `ff33af0` | arm-gate (fresh-arm-token + two-key برای قابلیت‌های خطرناک) |
| `29228aa` | tick-decoupling brain_worker + fugu-everywhere TASK_TIERS (propose-only) |
| `c3ffff4` | یکپارچه‌سازیِ PF + P0 + AGI M2/M3 |
| `476a938`+`f363024` | پاک‌سازیِ تستِ run_all + handoff |

> بدونِ این آشتی، **هیچ‌چیزِ مدرن (C6، موج‌ها) نمی‌تواند زنده اجرا شود** — چون زنده ماشینِ زیرش را ندارد.

## ۲) چرا با اینکه clean است، باز هم یک عملیاتِ عمدی است
merge صدها خطِ زنده را عوض می‌کند و شاملِ **۲ تصحیحِ رفتاری** (باگ‌فیکس‌ها) است → پس: **ارگانیسم خاموش + سوئیتِ کامل سبز + restart**. هرگز روی ارگانیسمِ در حالِ اجرا. (ولی چون conflict صفر است، ریسکِ merge پایین است — ریسک فقط در «deployِ زنده» است، که با رول‌بکِ فوری پوشش داده می‌شود.)

## ۳) روال (native، ویندوز — از این‌طرف نمی‌زنم؛ لمسِ زندهٔ خودتغییردهنده)

```powershell
Set-Location F:\backup

# ── فاز ۰: نقاطِ رول‌بکِ فوری
git tag backup/live-pre-reconcile-2026-07-24  claude/octopus-event-bridge-aligned
git tag backup/master-pre-reconcile-2026-07-24 master

# ── فاز ۱: پیش‌آزمونِ merge در worktreeِ ایزوله (ارگانیسم هنوز روشن — این‌جا فقط تست)
git worktree add ../oct-reconcile claude/octopus-event-bridge-aligned
cd ..\oct-reconcile
git merge master        # انتظار: clean، بدونِ conflict (۲ فایلِ مشترک یکسان‌اند)
$env:REAL_VAULT = (Resolve-Path .).Path
python _ops\tests\run_all.py     # باید کامل سبز باشد (جز ۲ خطای نامرتبطِ شناخته‌شده اگر بود)
findstr /n /c:"=1" _ops\OCTOPUS-flags.cmd | findstr /i "C6 KILL_SEAM CORTEX_REVIVE"  # تأیید: هیچ فلگِ خطرناک arm نشده
```
اگر سوئیت سبز شد و فلگ‌ها خاموش بودند → deployِ زنده:
```powershell
# ── فاز ۲: HALT ارگانیسم (خودت): STOP-ORGANISM.flag یا /panic؛ فریزِ state/pulse را تأیید کن.
# ── فاز ۳: merge روی درختِ زنده (حالا که خاموش است و merge از قبل تست شده)
cd F:\backup
git merge master        # همان merge clean
# ── فاز ۴: restart
.\RESTART-ORGANISM.bat
# ── فاز ۵: تأیید: بوت سالم، پورت‌های 8771/8772 بالا، run_all سبز، هیچ فلگی armنشده، kill-switch کار می‌کند.
```
**رول‌بکِ فوری (اگر هرچیزی خراب شد):**
```powershell
# ارگانیسم را خاموش کن، بعد:
git reset --hard backup/live-pre-reconcile-2026-07-24
.\RESTART-ORGANISM.bat
```

## ۴) فاز ۲ (بعد از پایدارشدنِ زنده==master): سوارکردنِ موج‌ها
برنچِ `claude/megaprompts-octopus-review-d3f1a0 @ 59dcdc7` (موج ۱ + موج ۲: فیکسِ قلب، پکِ امنیتی، model_router، tick، lead-gen، **هوکِ C6**) روی master ساخته شده → بعد از آشتی، **تمیز** روی زنده merge می‌شود. **آن‌وقت هوکِ C6 وابستگی‌هایش را دارد و واقعاً قابلِ arm است.**

## ۵) همیشه owner-gated (حتی بعد از آشتی)
arm کردنِ C6 (فقط تو `ACTIVATION-C6-RESEARCH.flag` را می‌سازی) · مسیرهای پول/ارسال · GATE-0 (Project-F) · TCB (پول/کلید/genome/kill-switch).

## ۶) خلاصهٔ یک‌خطی
split-brain **تقریباً بی‌خطر حل می‌شود** (merge بدونِ conflict) — تنها احتیاطِ لازم: ارگانیسم خاموش، سوئیت سبز، رول‌بکِ آماده. این تنها دروازه بینِ «کدِ آماده روی master» و «همه‌چی زندهٔ قابلِ arm» است.
