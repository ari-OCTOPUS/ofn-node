# RUNBOOK — اعتبارسنجی بکاپ کلید امضا (T42، دستور مالک #۷)

> فقط مالک اجرا می‌کند. ایجنت این فایل را می‌نویسد و به enc دست نمی‌زند و
> passphrase نمی‌خواهد (دستور #۷ §۳). پاسخ نهایی فقط یک کلمه است:
> `MATCH` یا `MISMATCH` — هیچ passphrase یا محتوای کلیدی در چت/لاگ/رسید/commit نمی‌آید.

## ورودی‌ها

- بکاپ: `F:\OCTOPUS-SURVIVAL-BACKUP-2026-08-19\owner-key.enc` (۱۴۴ بایت، فرمت
  `openssl enc` با ماجیک `Salted__`؛ sha256 = `4637015fa44d9755ca10e6c1e0bb01f00bdd699c8c46267afb5809dc091e9eb3`)
- لنگر مرجع: `_ops/owner-signing/TRUST-ANCHOR.md` →
  `2413e9746f13afc900b31ad4d966a6783d73662f661fa0d6dc578e9b244ab6b2`

## مراحل (PowerShell، همه در مسیر موقت خارج از repo)

```powershell
# ۰) مسیر موقت خارج از repo (نه F:\backup)
$t = Join-Path $env:TEMP ("octopus-keytest-" + [guid]::NewGuid().ToString('N').Substring(0,8))
New-Item -ItemType Directory -Path $t | Out-Null

# ۱) رمزگشایی بکاپ به PEM موقت (passphrase را در prompt تایپ کن — هرگز آرگومان/متغیر نشود)
openssl enc -d -aes-256-cbc -pbkdf2 `
  -in "F:\OCTOPUS-SURVIVAL-BACKUP-2026-08-19\owner-key.enc" `
  -out "$t\recovered.pem"
#   اگر فرمت رمزگشایی خطا داد (مثلاً بدون -pbkdf2 ساخته شده)، همین خط را یک‌بار
#   بدون -pbkdf2 تکرار کن؛ خطای دوم = MISMATCH-فرمت و توقف.

# ۲) استخراج کلید عمومی از نسخهٔ بازیابی‌شده
openssl pkey -in "$t\recovered.pem" -pubout -out "$t\recovered-public.pem"

# ۳) انگشت‌نگارتی DER و مقایسه با لنگر
$fp = (openssl pkey -pubin -in "$t\recovered-public.pem" -outform DER |
       sha256sum) -split ' ')[0]
$anchor = (Select-String -Path "F:\backup\_ops\owner-signing\TRUST-ANCHOR.md" `
           -Pattern '^([0-9a-f]{64})\s*$').Matches[0].Groups[1].Value
"recovered = $fp"
"anchor    = $anchor"
if ($fp -eq $anchor) { "MATCH" } else { "MISMATCH" }

# ۴) پاک‌سازی امن فایل‌های موقت (سه‌بار بازنویسی)
foreach ($f in @("$t\recovered.pem", "$t\recovered-public.pem")) {
  $len = (Get-Item $f).Length
  $fs = [IO.File]::Open($f, 'Open', 'Write')
  $buf = New-Object byte[] $len; (New-Object Random 42).NextBytes($buf)
  for ($i=0; $i -lt 3; $i++) { $fs.Seek(0,'Begin') | Out-Null; $fs.Write($buf, 0, $len) }
  $fs.Close()
}
Remove-Item -Recurse -Force $t
```

## حکم‌ها (طبق دستور)

```text
MATCH    → backup_recovery: VERIFIED
MISMATCH → backup_recovery: INVALID  → ساخت بکاپ تازه ضروری است
خطا/انصراف → UNTESTED → backup_recovery: UNKNOWN
```

## وضعیت فعلی

- **UNTESTED** — 2026-08-20: ایجنت B این runbook را نوشت؛ اجرای آن فقط با مالک
  است. نتیجه را مالک در یک کلمه اعلام و در
  `06-EVIDENCE/DIRECTIVE-7-REPORT-AGENT-B-2026-08-20.md` ثبت می‌کند.

## نکتهٔ فنی احتیاطی

اگر recovered.pem کلید خصوصیِ همان جفت کلید باشد، استخراج pubkey و انگشت‌نگارتی
دقیقاً مقدار لنگر را می‌دهد (محاسبهٔ deterministic). اگر بکاپ چیز دیگری باشد
(مثلاً کلید دیگر یا فایل خراب)، مقدار متفاوت یا خطای parse خواهید دید.
