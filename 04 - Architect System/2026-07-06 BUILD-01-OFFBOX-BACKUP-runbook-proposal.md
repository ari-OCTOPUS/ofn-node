---
type: runbook-proposal
status: proposal            # propose-only — runbookِ آماده‌ی اجرا. من چیزی نصب/اجرا نکردم.
role: Researcher-Designer
created: 2026-07-06
verdict_recorded: "آری «برو» 2026-07-06 → قدمِ ۱ نقشه (بک‌اپ اول)"
verdict_open: "مقصدِ بک‌اپ (§۲) — تنها تصمیمِ لازم"
depends_on: "[[2026-07-06 PENTA-SYSTEM-REPORT+REVIEW]] §۴ قدم ۱ · [[2026-07-06 PHASE5-BACKUP-DR-INTERLOCKS-proposal]]"
grounds: [LAPTOP-RUNTIME.md §۶/§۸ BACKLOG-10, ARCHITECT_CHARTER §۶ Privacy]
tags: [build-01, backup, rclone, disaster-recovery, runbook, propose-only]
---

# BUILD-01 — بک‌اپِ off-box (runbookِ آماده‌ی اجرا، propose-only)

> **قدمِ اولِ نقشه — پیش از هر «همیشه‌روشن».** این‌جا هیچ‌چیز نصب/اجرا نشد؛ فقط مراحل + اسکریپت برای اجرای **خودت سمتِ Windows** (طبق الگوی موجودت «اجرا Windows-side توسط مالک»). با یک دستور بگو، همین اسکریپت را به‌صورت فایلِ آمادهٔ `scripts/` هم می‌گذارم.

---

## ۱. هدف و دامنه
هدف: نسخهٔ دومِ **رمزنگاری‌شدهٔ** دادهٔ حیاتیِ بقا، بیرونِ لپ‌تاپ، + تمرینِ restore. این حفرهٔ BACKLOG-10 را می‌بندد.

| بک‌اپ شود ✅ | چرا | مستثنا ⛔ |
|---|---|---|
| کلِ vault (`04 - Architect System/**` شاملِ ledgerها، `learning-engine/`, `architect/`) | وراثت + حاکمیت | `.env` |
| `langar.db` + `langar_state.pickle` | حافظهٔ بدنه | `*.key`, `*.pem` |
| `audit.jsonl` / `logs/igk_state` | حسابرسیِ امضاشده | `secrets*`, password stores |
| `MUSE-QUARANTINE-LEDGER` (بعد از فاز ۳) | ایده‌ها | هر مقدارِ secret |

> **چرا secret مستثناست:** طبق منشور §۶، مقادیرِ کلید هرگز از لپ‌تاپ کپی نمی‌شوند؛ آن‌ها از قبل off-box/در password manager‌اند.

## ۲. مقصدِ بک‌اپ (تنها verdict لازم)
| گزینه | هزینه | lock-in | حریم (§۶) | توصیه |
|---|---|---|---|---|
| **Backblaze B2 + rclone crypt** | ~$6/TB/ماه | پایین (S3-سازگار) | **zero-knowledge** (رمز سمتِ کلاینت) | ✅ **توصیه** — off-site واقعی + رمزِ خودت |
| دیسکِ خارجیِ رمز‌شده | یک‌بار خرید | صفر | عالی اگر جای دیگری نگه‌داری | خوب به‌عنوانِ نسخهٔ دوم، ولی off-site نیست مگر ببری بیرون |
| کلودِ موجود + crypt | بسته به سرویس | متوسط | zero-knowledge با crypt | قابل‌قبول؛ Obsidian Sync فقط `.md` را می‌گیرد، نه db/ledger/audit |

> با **rclone crypt** حتی روی کلود، دادهٔ شخصی (HRV/langar.db/هیپنوتیزم) به‌صورتِ **رمزشده** می‌رود؛ plaintext هرگز خارج نمی‌شود → §۶ و O-04 (default لپ‌تاپ) حفظ. فقط مقصد را بگو تا دستورها را نهایی کنم.

## ۳. راه‌اندازی (یک‌بار — سمتِ Windows، خودت)
```powershell
# 1) نصب rclone (choco یا zip رسمی)
winget install Rclone.Rclone

# 2) ساختِ remoteِ رمز (رمز فقط در password manager؛ هرگز در vault/چت)
rclone config      # → n) new  → نامِ "b2raw"  → Backblaze B2 → key/secret را وارد کن
rclone config      # → n) new  → نامِ "vaultcrypt" → crypt → remote = b2raw:architect-backup
#           → رمزِ crypt را از password manager بگذار (obscure می‌شود، در چت ننویس)
```

## ۴. اسکریپتِ بک‌اپ (نسخه‌دار + لاگ + هشدارِ شکست)
```powershell
# backup-offbox.ps1  — نسخه‌دار (sync + archive تاریخ‌دار = بدونِ ازدست‌رفتنِ نسخهٔ قبلی)
$ErrorActionPreference = "Stop"
$stamp   = Get-Date -Format "yyyy-MM-dd_HHmm"
$src     = "F:\backup\04 - Architect System"
$dst     = "vaultcrypt:current"
$archive = "vaultcrypt:archive/$stamp"      # نسخهٔ جابه‌جاشده = تاریخچه (append-only-ish)
$log     = "F:\backup\_ops\backup\log_$stamp.txt"
$exclude = @("--exclude",".env","--exclude","*.key","--exclude","*.pem","--exclude","secrets/**","--exclude","*_secret*")

$flagDir = "F:\backup\_ops\backup"
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
New-Item -ItemType Directory -Force -Path $flagDir | Out-Null
try {
    # اگر rclone نصب نباشد، اینجا throw می‌شود → catch مارکر را می‌نویسد (نه سکوت)
    & rclone sync "$src" "$dst" --backup-dir "$archive" @exclude `
          --transfers 4 --log-file "$log" --log-level INFO
    if ($LASTEXITCODE -ne 0) { throw "rclone exit=$LASTEXITCODE" }
    Remove-Item "$flagDir\FAILED.flag" -ErrorAction SilentlyContinue
    "OK $stamp" | Out-File "$flagDir\LAST-OK.flag"
} catch {
    # خطای خاموش = شدیدترین باگ (منشور §۴) → مارکرِ آشکار در هر حالتِ شکست
    "BACKUP-FAILED $stamp : $_" | Out-File "$flagDir\FAILED.flag"
    exit 1
}
```

## ۵. زمان‌بندی (Task Scheduler — بدونِ لاگین‌وابستگی)
```powershell
schtasks /Create /TN "OffboxBackup" /TR "powershell -NoProfile -File C:\ops\backup-offbox.ps1" `
         /SC HOURLY /RU SYSTEM /RL HIGHEST /F
```
> ساعتی برای داده‌ای که کم تغییر می‌کند کافی است؛ rclone فقط دلتا می‌فرستد (کم‌هزینه).

## ۶. تمرینِ restore (اجباری — «بک‌اپِ تست‌نشده = نداشته»)
```powershell
# restore-drill.ps1 — ماهانه: بازیابیِ نمونه به temp و diff
$tmp = "C:\ops\restore-test"
rclone copy "vaultcrypt:current/learning-engine" "$tmp\learning-engine" --log-level INFO
# سپس دستی diff بگیر با نسخهٔ زنده؛ اگر فرقِ غیرمنتظره بود → alert
Get-ChildItem "$tmp\learning-engine" | Format-Table Name,Length,LastWriteTime
```
- ماهانه اجرا کن؛ نتیجه را در ledger ثبت کن (kind=drill).
- سالی یک‌بار: **restoreِ کامل** روی یک پوشهٔ خالی و بوتِ آزمایشیِ langar از آن.

## ۷. مانیتورینگ و ضدِ خطای خاموش (منشور §۴)
- `LAST-OK.flag` / `FAILED.flag` = وضعیتِ آخرین اجرا؛ GOVERNOR (فاز ۲) این‌ها را می‌خواند و اگر `FAILED` یا `LAST-OK` کهنه بود → تشدیدِ تلگرام.
- retention: `archive/<date>` را با یک prune ساده نگه‌دار (مثلاً ۳۰ نسخهٔ روزانه + ۱۲ ماهانه).

## ۸. هزینه/جایگزین/lock-in (خلاصه)
- **B2:** ~$6/TB/ماه؛ vaultِ متنی احتمالاً « MB»‌هاست → عملاً سنت‌ها. زیرِ سقفِ §۵.
- **جایگزین‌ها:** rsync.net، Wasabi، دیسکِ خارجی. rclone هر کدام را می‌گیرد → lock-in پایین.

## ۹. چه چیزی این فاز تغییر می‌دهد
**صفرِ عملیاتی از سمتِ من.** اسکریپت‌ها این‌جا فقط برای مرورند؛ نصب/زمان‌بندی را **تو** اجرا می‌کنی (یا بگو فایلِ `scripts/backup-offbox.ps1` را propose کنم).

## ۱۰. QA checklist (قبل از اعتماد)
- [ ] `.env`/`*.key` واقعاً در بک‌اپ نیستند (یک‌بار `rclone ls vaultcrypt:current | findstr .env` = خالی).
- [ ] crypt فعال است (فایل‌های مقصد نامِ رمزشده دارند).
- [ ] یک restore-drill موفق ثبت شد.
- [ ] `FAILED.flag` مسیرِ تشدید دارد.

## ۱۱. باز مانده و گامِ بعد
- **verdict:** فقط مقصد (§۲) — B2 تأیید است؟
- **بعدِ بک‌اپ (قدم ۲ نقشه):** read-only فنیِ ژنوم + چکِ genome-diff دکتر.

## ۱۲. ردیفِ ledger پیشنهادی
| تاریخ | kind | مبنا | تغییر | وضعیت |
|---|---|---|---|---|
| 2026-07-06 | propose | REPORT §۴ قدم۱ + «برو» | runbookِ بک‌اپِ off-box (rclone crypt + drill + مانیتور) | آماده‌ی اجرای مالک |

---

*propose-only. هیچ ژنوم/کد تغییر نکرد و چیزی نصب/اجرا نشد.*
