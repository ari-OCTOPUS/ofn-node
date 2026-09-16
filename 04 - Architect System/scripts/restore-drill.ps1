# restore-drill.ps1 — تمرینِ بازیابی (ماهانه). «بک‌اپِ تست‌نشده = بک‌اپِ نداشته».
# یک زیرمجموعه را از off-box به temp برمی‌گرداند تا صحت را چشمی diff کنی.
$ErrorActionPreference = "Stop"
$tmp = "C:\ops\restore-test"
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
try {
    & rclone copy "vaultcrypt:current/learning-engine" "$tmp\learning-engine" --log-level INFO
    if ($LASTEXITCODE -ne 0) { throw "rclone exit=$LASTEXITCODE" }
    Write-Host "restore-drill OK — محتوا در $tmp\learning-engine :"
    Get-ChildItem "$tmp\learning-engine" | Format-Table Name,Length,LastWriteTime
    Write-Host "حالا با نسخهٔ زنده diff بگیر؛ فرقِ غیرمنتظره = alert. نتیجه را در ledger ثبت کن (kind=drill)."
} catch {
    Write-Error "restore-drill FAILED: $_"
    exit 1
}
