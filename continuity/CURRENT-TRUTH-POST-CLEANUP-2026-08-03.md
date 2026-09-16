---
type: status
project: Octopus
date: 2026-08-03
status: post-cleanup-baseline
baseline_tag: post-cleanup-baseline-2026-08-03
baseline_commit: ea69126
tags: [octopus, baseline, canonical-truth, post-cleanup]
---

# Octopus Current Truth — Post-Cleanup Baseline (2026-08-03)

> **این نقطهٔ canonical truth پس از نشستِ پاک‌سازی ۲۰۲۶-۰۸-۰۳ است.**
> Tag: `post-cleanup-baseline-2026-08-03` · Commit: `ea69126`
> خلاصهٔ کامل نشست: `03 - Projects/_OCTOPUS-PMO/SESSION-SUMMARY-2026-08-03.md`

## وضعیتِ کلی

اختاپوس از یک وضعیتِ پراکنده (۴۵ branch، ۱۰۹ فایلِ ریشه، ~۱۵GB) به یک ساختارِ تمیز و قابلِ مدیریت رسید. این نقطه قفل شد.

## آمارِ baseline

| متریک | مقدار |
|---|---|
| branches | ۷ |
| worktrees | ۲ (master + hybrid-control-plane) |
| فایل‌های مستقیمِ ریشه | ۲ (CLAUDE.md, README.md) |
| فضا (بدون .git) | ~۶.۴ GB |
| approvals pending | ۲ (HOLD) |
| expired (بسته‌شده) | ۱۰۳ |
| commitهای merge‌نشده | ۰ |

## ۶ branch باقی‌مانده

| branch | وضعیت | دلیل |
|---|---|---|
| `master` | canonical | مسیرِ اصلی |
| `backup/pre-deploy-2026-07-21` | restore point | نقطهٔ بازگشت |
| `claude/c6-self-improvement` | نگه‌داری | ۳ commitِ C6 |
| `claude/project-f-agent-build` | نگه‌داری | ۵ commitِ Project-F (langar files) |
| `claude/vigilant-grothendieck` | نگه‌داری | test_master_halt fix |
| `fix/neural-loop-close-310-214` | **بحرانی — Phase B** | #۳۱۰ neural→decision گمشده |
| `claude/hybrid-control-plane-bd4b21` | فعال | امروز |

## مواردِ باز (به ترتیبِ اولویت)

### Phase B — بحرانی
`fix/neural-loop-close-310-214`: #۳۱۰ (neural→decision) روی master نیست. باید به‌صورتِ shadow-first، پشتِ flag، با تست و rollback اعمال شود. **نه live wiring.**

### Phase C — HOLD
۲ approval زنده (`sgc-mission-mis-*`): هر دو `medium`/`sgc_action`. به `attribution.claim` نزدیک‌اند. تصمیم بعد از Phase B.

### Phase D — triage
۵۶۵ نقطهٔ کورِ BLINDSPOTS در `03 - Projects/_OCTOPUS-PMO/`. باید triage شوند (P0/P1/P2/P3/Research).

## ساختارِ ریشه

```
F:\backup\
├── CLAUDE.md, README.md
├── 📚 11 پوشهٔ ابسیدین (00-10)
├── 🐙 4d_system, _ops, _octopus, OCTOPUS, OCTOPUS-DOCTOR, OCTOPUS-PRIME, nervous-system, PRE-0
├── 📁 agent-prompts, continuity, _Templates, _archive-binaries, _Archive, _Duplicates
```

## ERRATA — neural-loop #310 (2026-08-03, post-verification)

در نسخهٔ اولیهٔ SESSION-SUMMARY نوشته شد که #۳۱۰ neural→decision روی master نیست.
این **اشتباه بود**. راستی‌آزمایی بعدی (فاز B) نشان داد:

- ✅ #۲۱۴ BCM self-wipe guard روی master جذب شده (`bcm.py:150 if known:`)
- ✅ #۳۱۰ neural→decision shadow-first روی master جذب شده (`neural_driver.py:79-88`)
- ✅ flagها default-off هستند:
  - `OCTOPUS_NEURAL_EFFECT_SHADOW` (shadow logging، default-off)
  - `OCTOPUS_NEURAL_LEARNED_APPLY` (apply path، default-off)
- 🗑️ branch `fix/neural-loop-close-310-214` حذف شد (کاملاً dead)
- **اقدام لازم**: هیچ merge لازم نیست؛ فقط review و فعال‌سازیِ کنترل‌شدهٔ flagها در آینده (پس از ۲۴–۴۸h shadow review طبق طراحی).

## NOTE — nbb-cp-kre app (verified 2026-08-03)

`4d_system/nbb-cp-kre/` در baseline `ea69126` موجود بود **قبل از قفلِ نشستِ پاک‌سازی**. این یک پکیجِ پایتونِ از-قبل‌موجود است (تحتِ `src/nbb_cp_kre/`)، نه featureِ ساخته‌شده در نشستِ no-feature.

وقایعِ راستی‌آزمایی‌شده:
- ✅ `watcher.py` از watchdog observer و file_hash reads استفاده می‌کند؛ هیچ write یافت نشد
- ✅ `ReadOnlyGuard` choke-pointِ filesystem-write است و fail-closed است
- ✅ `read_note_body` روی خطا/escape fail-closed می‌شود (`return None`)
- ✅ `start.bat` و `run_dashboard.bat` موجودند
- ⛔ اپ در این نشست **اجرا نشد**

وضعیتِ اجرا:
- **NOT RUN** در این نشست
- نیاز به Decision Recordِ جداگانه قبل از اجرا دارد، چون `run_dashboard.bat` ممکن است وابستگی نصب کند (`pip install -e ".[ui,live]"`) و کلِ `F:\backup` را scan کند

### طبقه‌بندیِ manifest
```
kind: app/tool
status: BASELINE_PREEXISTING
decision: KEEP_STAGED_READONLY_TOOL
execution: NOT_RUN_THIS_SESSION
risk: medium
reason: dependency install + vault-wide scan + watcher/live mode concerns
```

### پیش‌نیازهای اجرای امن (نشستِ بعدی)
۱. Decision Record (D3): environment_change=yes, vault_scan=yes, owner_required=yes
۲. نصب داخل `.venv`، نه global pip
۳. اول روی snapshot/test vault کوچک، نه کلِ `F:\backup`
۴. ترتیب: package-check → dashboard-only → scan read-only sample → بعداً watcher

## rollback

اگه نیاز به بازگشت به این baseline بود:

```bash
git reset --hard post-cleanup-baseline-2026-08-03
```
