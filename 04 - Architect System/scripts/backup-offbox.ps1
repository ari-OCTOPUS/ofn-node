# backup-offbox.ps1 — بک‌اپِ off-boxِ رمزنگاری‌شده و نسخه‌دار (BUILD-01).
# پیش‌نیاز: rclone نصب + remoteِ crypt به نامِ "vaultcrypt" (SETUP-README §بک‌اپ).
# ضدِ خطای خاموش: اگر rclone نبود یا شکست خورد، FAILED.flag در هر حالت نوشته می‌شود (منشور §۴).
$ErrorActionPreference = "Stop"
$stamp   = Get-Date -Format "yyyy-MM-dd_HHmm"
$src     = "F:\backup\04 - Architect System"
$dst     = "vaultcrypt:current"
$archive = "vaultcrypt:archive/$stamp"     # نسخهٔ جابه‌جاشده = تاریخچه
$flagDir = "F:\backup\_ops\backup"
$log     = "$flagDir\log_$stamp.txt"
$exclude = @("--exclude",".env","--exclude","*.key","--exclude","*.pem",
             "--exclude","secrets/**","--exclude","*_secret*")

New-Item -ItemType Directory -Force -Path $flagDir | Out-Null
try {
    # اگر rclone نصب نباشد، اینجا throw می‌شود → catch مارکر را می‌نویسد (نه سکوت)
    & rclone sync "$src" "$dst" --backup-dir "$archive" @exclude `
          --transfers 4 --log-file "$log" --log-level INFO
    if ($LASTEXITCODE -ne 0) { throw "rclone exit=$LASTEXITCODE" }
    Remove-Item "$flagDir\FAILED.flag" -ErrorAction SilentlyContinue
    "OK $stamp" | Out-File "$flagDir\LAST-OK.flag"
    Write-Host "backup OK $stamp"
} catch {
    "BACKUP-FAILED $stamp : $_" | Out-File "$flagDir\FAILED.flag"
    Write-Error "backup FAILED: $_"
    exit 1
}
