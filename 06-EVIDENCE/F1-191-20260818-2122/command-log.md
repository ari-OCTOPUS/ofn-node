F1 REALITY INVENTORY — command log
started 2026-08-18T21:22:21+1000
node: .191 laptop-brain (DESKTOP-KA9RFN5)
operator: ZCode GLM-5.3 under OWNER-CHIEF DECISION EXECUTE_F1_READ_ONLY_DISCOVERY_AND_EVIDENCE_OUTPUT
logging-method: batch append per section, exact commands + timestamps

[2026-08-18T21:22:54+1000] F1.1 commands (PS via Git Bash):
- powershell Get-CimInstance Win32_Process -> 01-process-all.raw.json (143179 bytes)
- sed redaction pass -> 01-process-all.json ; raw temp DELETED (contained 1 key-like match; secret-handling rule); redactions=1
[2026-08-18T21:23:04+1000] F1.1:
- powershell Get-NetTCPConnection -State Listen -> 01b-listen-tcp.txt
- powershell Get-NetUDPEndpoint -> 01c-listen-udp.txt
[2026-08-18T21:23:22+1000] F1.1:
- python -X utf8 filter_processes.py -> 01d-process-filtered.tsv
[2026-08-18T21:23:45+1000] F1.1: uptime parser patched (WCF /Date() format); rerun filter_processes.py -> 01d-process-filtered.tsv
[2026-08-18T21:24:24+1000] F1.2:
- Get-Service running -> 02a
- Get-ScheduledTask non-disabled -> 02b (12 OCTOPUS tasks found)
- Get-ScheduledTaskInfo x12 -> 02d-taskinfo.txt
- Win32_StartupCommand -> 02c (no OCTOPUS entries)
[2026-08-18T21:29:51+1000] F1.5: Get-NetTCPConnection established / Get-NetIPAddress / Get-NetAdapter -> 05a/05b/05c
[2026-08-18T21:31:30+1000] F1.6/8: sqlite read-only row counts -> 07c-dbcounts.txt; flag contents + heart cadence -> 07b-heart-flags.txt
[2026-08-18T21:37:12+1000] F1.4: find .git dirs + bundles; git rev-parse/branch/remote/status/worktree/stash -> 04-repo-map.txt
[2026-08-18T21:55:34+1000] F1.3 resumed (bounded scope, heavy trees pruned: .claude/worktrees, venv/.venv/.test-venv, __pycache__, _archive-binaries) -> 03-storage-30d.tsv (33812 files); summary/zero-byte/secrets/probes -> 03b
F1.4 repo facts + germline mirror + stub .git + envelopes peek -> 04-repo-map.txt, 06b
F1.5 -> 05a/05b/05c
F1.6 + subsystem verification -> 06-agent-map-raw.txt, 07b/07c/07d/07e
/sh chain verification: center.py:3213 handler, _is_owner:2657, _ops/shell_capability.py active() — ACTIVATION-RAW-SHELL.flag EXISTS (ARMED), no STOP-RAW-SHELL
concurrent writer observed: octopus-research-sprint/ scaffold (37 files, placeholders) created 21:20-21:22 during this run — INFERENCE another local agent session; recorded, non-blocking
finished all sections
