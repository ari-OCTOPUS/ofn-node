---
type: runbook
status: ready
created: 2026-07-06
verdict_recorded: "آری «همه‌چیو درست کن، آماده باشه» 2026-07-06"
tags: [setup, scripts, activation, owner-steps]
---

# SETUP — راه‌اندازیِ سیستمِ GOVERNOR + MUSE (اسکریپت‌های آماده)

> ⚠️ **هیچ‌چیز این‌جا خودکار اجرا نمی‌شود.** اسکریپت‌ها ساخته و تست‌شده‌اند ولی **تا وقتی خودت زمان‌بندی/اجرا نکنی، غیرفعال‌اند.** مراحلِ «فقط-مالک» را فقط تو می‌توانی انجام دهی (منشور: charter/secret/پول/git = انسان).
>
> 🗄️ **بازنشسته 2026-07-17 (تری‌اسکن):** `genome_guard.py` به `_Archive/scripts/` منتقل شد
> (همیشه exit(2) می‌داد چون `GENOME-LOCK.json` هرگز init نشد، و صفر callerِ زنده داشت).
> مراحلِ زیر که به `genome_guard.py --init` یا اجرای آن اشاره می‌کنند **دیگر معتبر نیستند** —
> رد کن. اگر بعداً بررسیِ یکپارچگیِ genome خواستی، باید از نو (جای دیگری) ساخته شود.

---

## ۱. چه چیزی آماده است (تست‌شده در سندباکس)
| فایل | کار | تست |
|---|---|---|
| `scripts/budget_gate.py` | شمارندهٔ بودجهٔ مشترک (reserve/settle/release) | ✅ race ۲۰-موازی، fail-closed، rollover |
| `scripts/genome_guard.py` | گاردِ یکپارچگیِ ژنوم (Windows-side) | ✅ init/tamper(exit1)/restore |
| `scripts/governor_shadow.py` | سرپرستِ shadow (قطعی، $0) | ✅ healthy/tampered/doctor-crash/low-health/STOP |
| `scripts/backup-offbox.ps1` | بک‌اپِ off-boxِ رمزنگاری‌شده | بازبینی چشمی (rclone سمتِ Windows) |
| `scripts/restore-drill.ps1` | تمرینِ restore | بازبینی چشمی |
| `learning-engine/MUSE-QUARANTINE-LEDGER.md` | قرنطینهٔ ایده‌ها (خالی) | — |

پرامپت‌های MUSE و دکترِ تکاملی در `BUILD-03/BUILD-04` حاضرند (متن، آماده‌ی اجرای تعاملی).

## ۲. کارهای «فقط-مالک» (من نمی‌توانم — تو باید)
1. **حلِ دریفت‌های ژنوم** D1/D2/D3 (ویرایشِ `LEARNING-CONTRACT.yaml` mode، `LEARNING-STATE.json` گیت، تثبیتِ تک‌whitelist).
2. **پیستِ بلوکِ منشورِ فاز ۱** در `ARCHITECT_CHARTER.md` (charter برای ایجنت immutable است).
3. **انتخابِ مقصدِ بک‌اپ** + `rclone config` (کلید فقط در password manager، هرگز در چت/vault).
4. **`python genome_guard.py --init "verdict: قفلِ اولیه"`** — تأییدِ ژنومِ فعلی (این عملِ approval است).
5. **`attrib +R`** روی ۴ فایلِ ژنوم (قفلِ سبک).

## ۳. ترتیبِ فعال‌سازی (طبق BUILD-06 §۳ — امن‌ترین → آخر)
```
① بک‌اپ:   schtasks /Create /TN OffboxBackup  /TR "powershell -File C:\ops\backup-offbox.ps1"  /SC HOURLY /RU SYSTEM /F
② گارد:    python genome_guard.py --init "..."   ➜   attrib +R <۴ فایلِ ژنوم>
③ بودجه:   (خودکار فعال می‌شود وقتی اولین مصرف‌کننده reserve() صدا بزند)
④ GOVERNOR: schtasks /Create /TN GovernorShadow /TR "powershell -Command python C:\ops\governor_shadow.py" /SC MINUTE /MO 15 /RU SYSTEM /F
⑤ MUSE/دکتر: تعاملی dry-run (BUILD-04) — قرنطینه پر شود، هیچ forward نشود، rubric کالیبره شود
⑥ live:    فقط بعد از ۳۰ روز پاک + verdictِ صریح (BUILD-06 §۳)
```
> مسیرها را با محلِ واقعیِ فایل‌ها هماهنگ کن (اسکریپت‌ها را از `scripts/` به `C:\ops\` کپی کن یا مسیرِ schtasks را به همین‌جا بده). همه env-override دارند: `VAULT_ROOT`, `SCRIPTS_DIR`, `OPS_DIR`, `BUDGET_STATE`.

## ۴. QA قبل از اتکا (سمتِ Windows)
- [ ] `rclone ls vaultcrypt:current | findstr .env` → خالی (secret نرفته).
- [ ] تغییرِ آزمایشیِ یک بایت در whitelist → `genome_guard.py` مقدارِ `genome-unapproved-change` می‌دهد.
- [ ] یک `restore-drill.ps1` موفق.
- [ ] `governor_shadow.py` یک‌بار دستی → یک سطر در `HEARTBEAT.md`.

## ۵. ثابت‌های ایمنی (همیشه)
فایلِ `STOP` در ریشهٔ vault = halt همه · سقفِ بودجه $2/روز · AU$30/ماه · خطِ فاجعهٔ $500 · هر تغییرِ ژنوم با workflowِ سه‌مرحله‌ایِ قفل (`attrib -R` → ویرایش → `--init` → `attrib +R`).

## ۶. اگر ایراد دیدی
همه اسکریپت‌ها propose‌اند و در `scripts/`‌اند؛ تغییرشان بی‌خطر است. changelogِ کاملِ باگ‌های رفع‌شده: `2026-07-06 REVIEW-FIXES-changelog.md`.
