# CLEANUP — چه چیزهایی را حذف کنی تا پروژه بهینه شود

تاریخ: ۲۰۲۶-۰۶-۲۵. (sandbox اجازه‌ی حذف روی درایوت را ندارد؛ پس خودت با اسکریپتِ پایین یا دستی پاک کن.)

## ۱) حتماً حذف — تکراری یا منسوخ
| مورد | چرا | حجم |
|---|---|---|
| `fusion-mvp/.git/` | گیتِ **ناقصِ** ساخته‌شده در sandbox (خراب). بعد از حذف، روی ویندوز `git init` تازه بزن. | — |
| `fusion-safety/igk/` | **کپیِ تکراری**. نسخه‌ی اصلی و runnable حالا `fusion-mvp/igk/` است (کنارِ کدی که از آن استفاده می‌کند). | ~16K |
| ۱۱ فایلِ `*.pdf` در root | بعد از split، همه در `fusion-creative/` (۱۰) و `fusion-safety/docs/` (checklist) **کپی شده‌اند**. | ~2.0MB |

> ⚠️ قبل از حذفِ PDFهای root، یک‌بار `fusion-creative/` و `fusion-safety/docs/` را باز کن و سالم‌بودنشان را تأیید کن.

## ۲) حذفِ بی‌خطر — کش / تولیدشونده (هر وقت خواستی)
| مورد | چرا |
|---|---|
| همه‌ی `__pycache__/` (۴ پوشه) | کشِ پایتون؛ خودکار بازساخته می‌شود. |
| `fusion-mvp/dashboard.html` | خروجیِ `python dashboard.py`؛ هر وقت لازم شد دوباره ساخته می‌شود. |
| `fusion-mvp/logs/igk_state/` | وضعیتِ اجرای کرنل (شاملِ `.kernel_key`). runtime؛ بازساخته می‌شود. **هرگز commit نکن.** |
| `fusion-mvp/logs/audit.jsonl` | لاگِ اجرا؛ اختیاری. `logs/.gitkeep` را نگه‌دار. |

## ۳) هرگز commit نکن (الان در `.gitignore` هست)
`.env` · `*.pyc` · `__pycache__/` · `logs/*.jsonl` · `dashboard.html` · `prompts.json` · `**/.kernel_key` · `logs/igk_state/`

## ۴) نگه‌دار (حذف نکن)
- `fusion-mvp/igk/` (کرنلِ اصلی) · `fusion-mvp/igk/held_out.sample.json` (نمونه‌ی held-out)
- `fusion-safety/{GAP-AUDIT,RECONCILIATION}.md` و `fusion-safety/docs/`
- `fusion-creative/` · `INDEX.md`

## اسکریپتِ آماده — `cleanup.ps1`
در PowerShell اجرا کن (یا فایلِ `cleanup.ps1` کنارِ همین سند را Right-click → Run with PowerShell):

```powershell
$root = "C:\Users\Armin\Documents\Claude\Projects\AI Farm"

# ۱) تکراری/منسوخ
Remove-Item -Recurse -Force "$root\fusion-mvp\.git"     -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$root\fusion-safety\igk"   -ErrorAction SilentlyContinue
Get-ChildItem "$root\*.pdf" | Remove-Item -Force        # PDFهای root (در دو پوشه کپی شده‌اند)

# ۲) کش/تولیدشونده
Get-ChildItem -Path $root -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Remove-Item -Force          "$root\fusion-mvp\dashboard.html"  -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$root\fusion-mvp\logs\igk_state"  -ErrorAction SilentlyContinue
# اختیاری: Remove-Item -Force "$root\fusion-mvp\logs\audit.jsonl" -ErrorAction SilentlyContinue

Write-Host "✅ پاکسازی تمام شد."
```

## نتیجه‌ی پاکسازی
حذفِ موارد ۱ ≈ **۲MB و دو تکرارِ سردرگم‌کننده** کم می‌کند و یک منبعِ واحد برای هر چیز می‌گذارد (همان «پراکندگیِ منبع = تناقضِ پنهان» که `data-map` هشدارش را داد).
