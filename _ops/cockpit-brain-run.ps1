# cockpit-brain-run.ps1 — یک بیداریِ مغزِ کنترل‌پنل.
#
# GO ِ مالک ۲۰۲۶-۰۸-۰۵: بیداری هر ۵ دقیقه، سکوت = سالم.
#
# چرا اسکریپتِ جدا و نه یک حلقهٔ دائمی: حلقهٔ دائمی وقتی می‌میرد بی‌صدا
# می‌میرد و مالک ماه‌ها نمی‌فهمد (این مخزن یک بار همین را خورد — بات ۳.۹
# ساعت مرده بود). Task Scheduler خودش زنده‌کننده است و «آخرین اجرا» را
# نگه می‌دارد، پس مرگش قابلِ دیدن است.
#
# ⚠️ فلگ‌ها از OCTOPUS-flags.cmd بار می‌شوند — بدونِ آن، پروسه فلگ‌های
# OCTOPUS_* را ندارد و هرچه بسنجد دربارهٔ **خودش** است نه ارگانیسم.
# این دقیقاً تله‌ای است که در جلسهٔ ۰۸-۰۴ پنج بار زد.

$ErrorActionPreference = "Stop"
$ops  = "F:\backup\_ops"
$log  = Join-Path $ops "state\cockpit_brain\run.log"
New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null

function Write-Log([string]$m) {
    $line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $m
    Add-Content -Path $log -Value $line -Encoding utf8
}

try {
    # بارِ فلگ‌ها — همان تجزیه‌ای که RESTART-PROCESS.ps1 می‌کند
    $flags = Join-Path $ops "OCTOPUS-flags.cmd"
    if (Test-Path $flags) {
        foreach ($ln in (Get-Content $flags -Encoding utf8)) {
            if ($ln -match '^\s*set\s+([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
                [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2].Trim(), "Process")
            }
        }
    }

    if ($env:OCTOPUS_COCKPIT_BRAIN -ne "1") {
        Write-Log "SKIP flag off"
        exit 0
    }

    $env:PYTHONIOENCODING = "utf-8"
    $out = & python -X utf8 (Join-Path $ops "cockpit_brain_tick.py") 2>&1
    $code = $LASTEXITCODE
    # خروجی همیشه ثبت می‌شود — سکوتِ بی‌رد همان چیزی است که این پروژه
    # بارها از آن ضربه خورده.
    Write-Log ("exit={0} {1}" -f $code, ($out -join " | "))
    exit $code
}
catch {
    Write-Log ("ERROR {0}" -f $_.Exception.Message)
    exit 1
}
