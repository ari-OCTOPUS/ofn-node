---
title: تله‌های محیط ویندوز مالک
type: note
tags: [octopus, powershell, windows, operations]
up: "[[00-INDEX]]"
---

# درس‌های عملیاتی PowerShell

> [!info] این‌ها با شکست واقعی یاد گرفته شدند، نه با حدس.
> مالک فقط کپی‌پیست می‌کند. هر دستوری که بفرستی باید بار اول کار کند.

| چیز | نتیجه |
|---|---|
| heredoc `<<` | پشتیبانی نمی‌شود |
| `python -c "…"` طولانی | `command line is too long` |
| نام فایل فارسی | خرابی encoding |
| کوتیشن تودرتوی `\"` داخل `-c` | `SyntaxError: unterminated string literal` |
| اسکریپت `.ps1` بدون امضا | نیاز به `-ExecutionPolicy Bypass` |
| `sites.pplx.app` با `urllib` | HTTP 403 — نیاز به احراز مرورگر |
| صفحهٔ artifact پرپلکسیتی | کد در iframe تودرتو است؛ `document.body.innerText` پوستهٔ بیرونی را می‌گیرد نه کد |

## الگوهای کارآمد

فایل کوچک:

```powershell
@'
...python code...
'@ | Set-Content -Path x.py -Encoding UTF8
python x.py
```

فایل بزرگ یا حاوی فارسی — gzip + base64:

```powershell
$b='<base64>'
$ms=New-Object IO.MemoryStream(,[Convert]::FromBase64String($b))
$gz=New-Object IO.Compression.GzipStream($ms,[IO.Compression.CompressionMode]::Decompress)
$out=New-Object IO.MemoryStream; $gz.CopyTo($out)
[IO.File]::WriteAllBytes("x.py",$out.ToArray())
```

## محیط

| قلم | مقدار |
|---|---|
| Python | 3.13 در `C:\Program Files\Python313` |
| مخزن کاری | `C:\Users\Armin\Desktop\OCTOPUS-NBB-CP-WORKING\nbb-control-plane` |
| vault مرجع | `F:\backup` |
| Downloads | `C:\Users\Armin\Downloads` |
| شاخهٔ git | `claude/second-brain-governor-v02-2a6e36` |

## بهداشت git

دو دیتابیس زنده و یک فایل موقت اشتباهاً وارد git شدند و در `d964f5f` بیرون رفتند:

```
_ops/observatory/data/*.db
_ops/observatory/data/*.db-*
__pycache__/
.pytest_cache/
setup_files.py
```

دلیل: دیتابیس زنده با هر اجرای ساعتی رشد می‌کند و conflict می‌سازد.
**شاهد در انبار می‌ماند، نه در git.**
