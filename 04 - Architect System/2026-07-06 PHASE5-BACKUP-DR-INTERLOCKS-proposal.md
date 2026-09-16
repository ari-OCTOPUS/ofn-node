---
type: proposal
status: proposal            # propose-only — طراحیِ بقا/DR. چیزی نصب/اجرا نشد.
role: Researcher-Designer
created: 2026-07-06
verdict_recorded: "آری «کاملش کن» 2026-07-06 → پیش‌بردِ فاز ۵ (آخر)"
depends_on: "[[2026-07-06 PHASE4-MEMORY-INTEL-DOCTOR-proposal]] · [[2026-07-06 PENTA-PROMPT-Governor-Muse-proposal]] فاز ۵"
grounds: [LAPTOP-RUNTIME.md §۶/§۸ (BACKLOG-10), ARCHITECT_CHARTER §۴/§۵, LEARNING-STATE.json pilot]
tags: [phase5, backup, disaster-recovery, interlocks, always-on, propose-only]
---

# فاز ۵ — بک‌اپ + بازیابیِ فاجعه + قفل‌های ضدِ runaway + همیشه‌روشن

> **propose-only.** طراحیِ بقاست؛ چیزی نصب/اجرا نشد. هدف: «تمامِ حافظه و هوشمندی و بک‌اپ» لحاظ شود و حلقهٔ همیشه‌روشن + خلاقیت هرگز خودتقویت نشود.

---

## ۱. OFF-BOX BACKUP (پرکردنِ بزرگ‌ترین حفره — BACKLOG-10)
- **ابزار:** `rclone` به off-box (کلود/دیسکِ دوم)، **رمزنگاری‌شده**، زمان‌بندی‌شده.
- **دامنه:** ledgerها (`EXPERIENCE`, `MUTATION`, `MUSE-QUARANTINE`) + `LEARNING-STATE.json` + vault(`.md`) + `langar.db`/pickle + `audit.jsonl`. **بدونِ secret** (آن‌ها از قبل off-box؛ منشور §۶).
- **قاعدهٔ طلایی:** «بک‌اپِ تست‌نشده = بک‌اپِ نداشته» → **تمرینِ restore** دوره‌ای اجباری.
- **حریم:** بک‌اپ laptop-origin؛ دادهٔ شخصی/Project-F طبق O-04 فقط لپ‌تاپ/off-boxِ خصوصی، هرگز VPS.

## ۲. STATE-DURABILITY + recovery
- durable روی دیسک: SQLite **WAL** + pickle + ledgerهای append-only + git.
- **recovery:** بعد از کرش/خواب → NSSM بالا می‌آورد → state بازخوانده → **چکِ fail-closedِ kill-switch پیش از سرویس** (LAPTOP-RUNTIME §۴). کارِ خطرناکِ نیمه‌تمام ادامه نمی‌یابد.

## ۳. ALWAYS-ON — با «سایه‌اول» (مهم‌ترین قاعدهٔ ایمنی)
- GOVERNOR: NSSM `Restart=always`. MUSE: زمان‌بندیِ نادر. learning-loop: ساعتی (`@ 35`).
- **shadow-first (اجباری):** رفتن از «فقط‌جلسات‌تعاملی» (STATE.runtime فعلی) به «پروسهٔ مستقلِ همیشه‌روشن» بزرگ‌ترین جهشِ ریسک است. پس اول در **پایلوتِ ۳۰روزه** (LAPTOP-PILOT-30D، day_zero امروز) به‌صورت **shadow/dry-run**: propose-only، بدونِ call خارجی، لاین‌های پرفرکانس `*/3,*/5` **dark** (همان scope_dark موجود). روشن‌کردنِ live فقط با verdictِ صریحِ آری بعد از پایلوت.

## ۴. RUNAWAY-INTERLOCKS — هر مسیرِ خودتقویت را نام ببر و ببند
| مسیرِ بالقوهٔ خودتقویت | چطور بسته می‌شود |
|---|---|
| MUSE → دکترِ تکاملی → اجرا | گیتِ آری وسط؛ **هیچ auto-apply**. دکتر فقط forward. |
| learning-loop خودجهش | whitelist + ۱ جهش/روز + evidence-based + rollbackِ ۲-خطا |
| GOVERNOR | propose-only؛ خودجهش ندارد |
| **rubric/آستانهٔ دکترِ تکاملی** | **genome (immutable)** — هیچ حلقه‌ای نمی‌تواند سخت‌گیری‌اش را شل کند (ضدِ evaluator-tampering) |
| هزینه | **شمارندهٔ بودجهٔ روزانهٔ مشترک (تک‌منبع)** — نه سقفِ per-agentِ جدا؛ در سقف، **همهٔ** callها halt |
| خطِ فاجعه | $500 (D-22) = «حلقهٔ recursive از کنترل خارج شده» → halt کامل |
| STOP | فایلِ STOP/halted = kill-switchِ همه (D-06) |

## ۵. DR-RUNBOOK (خلاصه)
1. **کرش/ری‌استارت:** خودکار (NSSM + fail-closed boot).
2. **از‌دست‌رفتنِ دیسک:** از off-box، restore → تمرینِ صحت → ادامه.
3. **کلیدِ لو‌رفته:** revoke/rotate سمتِ سرویس + ثبت در ROTATION؛ §Security Gate دوباره OPEN تا چرخش (منشور §۲).

## ۶. چه چیزی این فاز تغییر می‌دهد
**صفرِ عملیاتی.** طراحی؛ هیچ نصب/اجرا/ویرایشِ ژنوم.

## ۷. ردیفِ ledger پیشنهادی (kind=propose)
| تاریخ | kind | مبنا | تغییر | وضعیت |
|---|---|---|---|---|
| 2026-07-06 | propose | PENTA فاز ۵ + «کاملش کن» | backup off-box + DR + interlockها + shadow-first | pending-اجرا |

---

*propose-only. هیچ ژنوم/کد تغییر نکرد.*
