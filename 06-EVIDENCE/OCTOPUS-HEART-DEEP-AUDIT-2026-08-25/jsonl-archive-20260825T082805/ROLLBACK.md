# P6 JSONL ROLLBACK
Stamp: 2026-08-25T08:28:05+10:00
Copy archive file back over live path. Post-rotate appends after truncate will be lost.

copy /Y "F:\backup\06-EVIDENCE\OCTOPUS-HEART-DEEP-AUDIT-2026-08-25\jsonl-archive-20260825T082805\arbiter-shadow-divergence.jsonl" "F:\backup\_ops\state\pulse\arbiter-shadow-divergence.jsonl"
copy /Y "F:\backup\06-EVIDENCE\OCTOPUS-HEART-DEEP-AUDIT-2026-08-25\jsonl-archive-20260825T082805\math-control-observe.jsonl" "F:\backup\_ops\state\pulse\math-control-observe.jsonl"
copy /Y "F:\backup\06-EVIDENCE\OCTOPUS-HEART-DEEP-AUDIT-2026-08-25\jsonl-archive-20260825T082805\tick-timing.jsonl" "F:\backup\_ops\state\pulse\tick-timing.jsonl"
copy /Y "F:\backup\06-EVIDENCE\OCTOPUS-HEART-DEEP-AUDIT-2026-08-25\jsonl-archive-20260825T082805\arbiter-shadow.jsonl" "F:\backup\_ops\state\pulse\arbiter-shadow.jsonl"
copy /Y "F:\backup\06-EVIDENCE\OCTOPUS-HEART-DEEP-AUDIT-2026-08-25\jsonl-archive-20260825T082805\heart-params-shadow.jsonl" "F:\backup\_ops\state\pulse\heart-params-shadow.jsonl"
REM fuel-stream.jsonl was not truncated — no rollback needed
copy /Y "F:\backup\06-EVIDENCE\OCTOPUS-HEART-DEEP-AUDIT-2026-08-25\jsonl-archive-20260825T082805\money-pulse.jsonl" "F:\backup\_ops\state\pulse\money-pulse.jsonl"
REM velocity-stream.jsonl was not truncated — no rollback needed
