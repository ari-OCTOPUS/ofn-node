# ژنوم (Genome) — هستهٔ تغییرناپذیر

این پوشه «DNA» سیستم است: ارزش‌ها، گیت‌ها، متریک‌ها، سیاست بک‌اپ و پروتکل تغییر.
همهٔ ایجنت‌ها آن را **می‌خوانند** ولی **نمی‌نویسند**.

| فایل | نقش |
|---|---|
| `values.yaml` | ارزش‌ها و اصول تغییرناپذیر + آزمونِ مرزِ invariant↔mutable |
| `gates.yaml` | گیت بودجه، approve-first، مسیریابی مدل‌ها، run-guards |
| `metrics.yaml` | تعریفِ «سلامت» (فریزشده تا reward hacking نشود) |
| `backup.yaml` | سیاست ۳-۲-۱ و DR |
| `genome_change_protocol.md` | مسیر کندِ ۷۲ساعته + دو-کلیدی برای هر تغییر ژنوم |

## کدام ایجنت‌ها «تحت حاکمیت» ژنوم‌اند؟

هر سه ایجنت (`agents/`) توسط ژنوم **حکمرانی** می‌شوند و روی آن read-only‌اند:

- **Guardian-Architect** — «داخل ژنوم» به معنای *governed-by*، نه *able-to-edit*.
  کنترل، آنلاین‌بودن (۲۴ساعته)، اجرای گیت‌ها، و در صورت لزوم halt. ولی حقِ
  بازنویسی ژنوم را ندارد؛ تغییر ژنوم فقط از مسیر انسانیِ دو-کلیدی می‌گذرد.
- **Creativity Black-Box** — read-only روی کل پروژه، فقط `PROPOSAL` می‌سازد.
- **Evolutionary Doctor** — ارزیاب/تصمیم‌گیرِ هفتگی، فقط propose-only.

## قفل کردن (ضمانت فنی، نه صرفاً قراردادی)

```bash
# POSIX
chmod -R a-w genome/
# Windows (PowerShell, به‌جای chmod)
icacls "genome" /deny "$($env:USERNAME):(W)" /T
```
گاردین موظف است اگر این قفل برداشته شد یا فایلی از ژنوم تغییر کرد، رویداد
`METRIC(distance_from_genome>0)` ثبت و سیستم را halt کند.
