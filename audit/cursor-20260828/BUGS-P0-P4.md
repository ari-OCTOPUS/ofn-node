# BUGS-P0-P4

scan: 2026-08-27T23:03Z · patches this session: **none on live units** (propose-only on 180; signed policy not edited)

## P0 — safety / secrets / unauthorized effect / ledger

| id | issue | root cause | smallest patch | test | rollback | commit locus |
|---|---|---|---|---|---|---|
| P0-none-new | No new P0 crash or secret dump found in this scan | — | Do not print /etc/octopus/secrets.env values | secret scan on audit branch | n/a | audit docs only |
| P0-bind-preexist | llama 8081 and gateway 8780 listen `0.0.0.0` | units already bound | **do not change this session**; owner must decide LAN-only | ss -lnt before/after | revert unit | 138/180 systemd with owner GO |
| P0-disk90 | 180 root 90% (49G/58G, 5.9G free) | evidence/backups/inbox growth | archive untracked evidence to 138/PC, no delete of frozen receipts | df -h | restore archive | 180 disk only after owner |

No live ledger rewrite. 180 does not write revenue.

## P1 — money path / transport

| id | issue | root cause | smallest patch | test | rollback | commit |
|---|---|---|---|---|---|---|
| P1-tg | octopus-telegram-bridge inactive; owner cannot APPROVE bizop | unit not enabled/running; fugu is another app | Owner: enable **one** owner-dialogue path; do not start a second bot | systemctl is-active; one dry telegram to owner only | disable unit | 138 mesh, owner GO |
| P1-witness | bizop witness_verdict PENDING_138_RELAY | 180 cannot mint; 138 did not mint | 138 mint three witness_request from existing packets | 182 journal PASS/DISPUTED | leave packets | 138 outbox only |
| P1-policy-182 | policy.json hash drift 182 vs 180/138 | copies diverged | 138 publishes canonical policy; 182 replace only with signed copy | sha256 match | keep 182 file | **not** 180 ofn/config.py |
| P1-mesh-ungit | business_cycle only on 180 mesh | no repo | add octopus-mesh as tracked tree **or** rsync from 180 via 138; no new orchestrator | sha256 worker files match | keep copies | new repo or ofn-node subtree — owner pick |
| P1-inbox-ping | 180 inbox ~1490, 385/400 ping | pings stored not compacted | compact processed pings with dry-run first | inbox count | restore backup | 180 mesh inbox |
| P1-pc-mirror | F:\backup not pulled | ssh/22 or cifs | fix laptop OpenSSH **or** accept DEGRADED | sync.json mirror_healthy | n/a | PC |

## P2 — UNKNOWN on executable cards

Painting missing suburb/budget/job_type; ziman price_aud null; studio restricted → BLOCKED_HONEST.  
Patch: feed live lead.yaml rows into cycle **after** 138 export, not more fixtures. Test: fixture still UNKNOWN; live row fills fields.

## P3 — tests / dead code

See TEST-GAPS.md and DEAD-CODE.md. TTL T21/T23 vs signed policy: do not edit policy.json to green tests.

## P4 — architecture beauty

ofn-l4 unused, 15 megaprompts, bak files, Armin empty repo. Later.

## This PR

Additive audit documents only. No runtime patch. No merge.
