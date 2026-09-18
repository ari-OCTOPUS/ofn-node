# OCTOPUS-HARDWARE-EXEC-20260915 — ACTIONS-LOG

GOV_VERSION=V8 · LADDER=L2 · HOLD customer_send  
All times UTC unless noted. Rollback noted per action.

| UTC | action | detail | rollback |
|-----|--------|--------|----------|
| 2026-09-15T03:04:00Z | Owner review lock recorded | Docs/queue only; DENY live NPU install / GO-B4 this turn; HOLD customer_send | N/A (docs); originals untouched |
| (pre-T0, same day) | Preserve PRE-T0 | Copy old raw inventory/capabilities + live 138 dumps into `PRE-T0\`; bak old collector as `PRE-T0\fleet-inventory.sh.bak` | Restore from `PRE-T0\` if needed; do not delete PRE-T0 |
| (pre-T0, same day) | Mesh probe from ari@192.168.0.138 | 100/160/193/114/180/182 reachable via mesh key; python3 on 100; NO_PYTHON3 on 160/193/114 | Read-only; no rollback |
| (pre-T0) | Bak old collector on 138 | `fleet-inventory.sh.pre-t0-20260915` bak on 138; lane copy under `PRE-T0\fleet-inventory.sh.bak` | Restore bak path on 138 / from PRE-T0 |
| (pre-T0) | Install collector v2 alongside | Stage `fleet-inventory-v2.sh`, `fleet-collect-t0.sh`, `fleet-t0-aggregate.py` under lane `scripts\` and 138 `~/hw-exec-t0/` | Remove staged v2 paths; leave PRE-T0 bak; do not delete receipts |
| 2026-09-15T03:11:29Z → 03:11:42Z | Run T0 collect | From ari@192.168.0.138; all 7 nodes exit 0; write `T0-RECEIPTS\` + `/home/ari/fleet-inventory-t0.json` | Keep receipts; re-run collect only; PRE-T0 remains SoT for pre-fix dump |
| 2026-09-15 (post-T0) | Write EXEC lane docs | `LANE-REPORT.md`, `ACTIONS-LOG.md`, `NEXT-AGENT-MEGAPROMPT.md`, `INDEX.md` (UTF-8 Python) | Delete/replace these four files; do not touch PRE-T0 or T0-RECEIPTS |

### Preserve / install notes

- **Preserve PRE-T0:** old raws + old `fleet-inventory.sh.bak` under `PRE-T0\` — do not overwrite.
- **Bak old collector:** before v2, keep bak (lane + on 138 `fleet-inventory.sh.pre-t0-20260915`).
- **Install v2 alongside:** new scripts live under `scripts\` / `~/hw-exec-t0/`; do not treat as sole history — PRE-T0 + T0-RECEIPTS are the evidence chain.

| 2026-09-15T03:18Z | Honest 7-row census | PASS sha 65a85c8f… | n/a |
| 2026-09-15T03:20Z | librknnrt+model to 193 | OK | rm /opt/rknn-pilot on 193 |
| 2026-09-15T03:21Z | T2 pilot infer on 193 | PASS ~19.9ms / ~50fps | same |

| 2026-09-15T03:31Z | WORKER CONNECT 100/160/193/114 + roles | PASS RTT 4/4; may_authorize false | disable timers; restore nodes.json preimage |
| 2026-09-15T03:32Z | T2 expand 100/160/114/180/182 | 6/7 PASS; 138 NOT_RUN | rm /opt/rknn-pilot on workers |
| 2026-09-15T03:33Z | DOCS_LAG fix T1 PASS stamp | stamped | n/a |
