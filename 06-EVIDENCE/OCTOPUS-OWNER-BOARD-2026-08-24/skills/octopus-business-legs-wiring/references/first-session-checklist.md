# 09 — FIRST SESSION CHECKLIST

این چک‌لیست برای شروع فوری ایجنت بعدی است.

## Step 1 — Establish root

```powershell
$ROOT = (git rev-parse --show-toplevel)
$SHA = (git rev-parse HEAD)
$BRANCH = (git branch --show-current)
```

Write these to `ops/01-RUNTIME-TRUTH-CURRENT.md`.

## Step 2 — Confirm clean/dirty boundary

```powershell
git status --porcelain
```

If dirty:

- classify each file as USER_CHANGE / AGENT_CHANGE / GENERATED / UNKNOWN
- do not revert anything without owner approval

## Step 3 — Runtime inventory

```powershell
Get-Process | Sort-Object ProcessName | Select-Object Id,ProcessName,Path
Get-NetTCPConnection -State Listen | Select-Object LocalAddress,LocalPort,OwningProcess
Get-ScheduledTask | Select-Object TaskName,State,TaskPath
```

On Linux/board:

```bash
ps aux
ss -lntup
systemctl --user list-timers
systemctl list-timers
```

## Step 4 — Doctor freshness

Look for:

```text
state/doctor/report.json
_ops state equivalents
board state dir if available
```

Record:

```text
exists
mtime
age
sha256
producer
consumers
```

## Step 5 — Targeted tests

Run only targeted tests first:

```powershell
python -m pytest tests/test_repair_api.py -q
python -m pytest --collect-only -q
python -m pytest tests -q -k "doctor or owner_absence or telegram_glass or cockpit or outbox or worker"
```

If pytest absent, use unittest and record that difference.

## Step 6 — Write receipts

Create:

```text
ops/07-RECEIPT-INDEX.jsonl
receipts/runtime-truth-<timestamp>.json
receipts/test-matrix-<timestamp>.json
```

## Step 7 — Ask owner only if blocked

Use `06-OWNER-QUESTIONS.md`.

Do not ask permission for read-only measurement. Ask before any mutation.

## Exit criteria for first session

- Runtime truth file exists
- At least one command receipt exists
- Doctor report status is PASS / UNKNOWN / BROKEN, not assumed
- One queue candidate selected
- No GitHub writes
- No external effects
