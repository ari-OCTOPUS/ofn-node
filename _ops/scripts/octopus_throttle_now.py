"""One-shot: set OCTOPUS-related Windows processes to low priority (fix UI hitch)."""
from __future__ import annotations
import subprocess
from pathlib import Path
import json
from datetime import datetime, timezone, timedelta

AEST = timezone(timedelta(hours=10))
stamp = datetime.now(AEST).strftime("%Y-%m-%dT%H:%M:%S+10:00")

# Prefer Idle for tunnels; BelowNormal for python organism/center
IDLE_NAMES = {"cloudflared"}
BELOW_NAMES = {"python", "pythonw"}

ps = r"""
$ErrorActionPreference='SilentlyContinue'
$names = @('python','pythonw','cloudflared','node')
$procs = Get-Process -Name $names -ErrorAction SilentlyContinue
$out = @()
foreach ($p in $procs) {
  try {
    $target = 'BelowNormal'
    if ($p.ProcessName -eq 'cloudflared') { $target = 'Idle' }
    # skip tiny cursor helper noise? keep all python for now
    $p.PriorityClass = $target
    $out += [pscustomobject]@{ Id=$p.Id; Name=$p.ProcessName; Priority=$p.PriorityClass.ToString(); WS_MB=[math]::Round($p.WorkingSet64/1MB,1) }
  } catch {
    $out += [pscustomobject]@{ Id=$p.Id; Name=$p.ProcessName; Priority='FAIL'; WS_MB=0 }
  }
}
$out | ConvertTo-Json -Compress
"""

r = subprocess.run(
    ["powershell", "-NoProfile", "-Command", ps],
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
)
raw = (r.stdout or "").strip()
print(raw[:2000])
print("STDERR", (r.stderr or "")[:500])

ev = Path(r"F:/backup/06-EVIDENCE/OCTOPUS-LAPTOP-THROTTLE-2026-08-23")
ev.mkdir(parents=True, exist_ok=True)
try:
    data = json.loads(raw) if raw else []
except json.JSONDecodeError:
    data = {"raw": raw}
(ev / "PRIORITY-AFTER.json").write_text(
    json.dumps({"stamp_local": stamp, "result": data}, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
(ev / "NOTE.md").write_text(
    f"""# OCTOPUS laptop throttle — {stamp}

- Set `python*` → BelowNormal
- Set `cloudflared` → Idle
- Goal: reduce periodic UI hitch / mouse lag
- Do NOT kill organism/center unless owner asks
""",
    encoding="utf-8",
)
print("wrote", ev)
