# WHAT EXISTS — Node 138 body inventory (2026-08-28T00:30Z)
(name | node/path | type | status | input | output | consumer | exec-evidence | git | duplicate | use | verdict)
**Runtime core**
- ofn.service | /home/ari/ofn (python3 -m ofn.run) | code+service | LIVE | env+DBs+HTTP | 4 shells + /api/v1 + /api/v2 | browsers/bridge | pid1351408, :8791-94 | git reconcile d3fb20c clean | the monolith | business+API | KEEP
- Cockpit V2 read-only | web/cockpit-v2 + read_model | code | LIVE (:8794/cockpit-v2/) | /api/v2/owner | owner dashboard | owner | http 200 @00:12Z | git | none | owner view | KEEP
- Legacy panel | web/panel.html 121,601B | code | LIVE (/) | /api/v1 | owner UI | owner | sha 735134eb | git | superseded (M5) | KEEP till parity
- Shells ziman/lead/studio | web/*.html | code | LIVE (ports 8791-93) | /api/v1 | partner UIs | partners | listeners | git | — | business | KEEP
**Mesh runtime (octopus-mesh = DISK-ONLY, no git — GAP)**
- transport send/receive/bridge | bin/octomesh_* | code | LIVE | ssh stdin | queues+audit | daemons | 6489 processed / 1992 receipts | DISK | single | transport | KEEP + git-init proposal
- daemons supervisor/router/control-router/settler | bin/octopus_*.py + systemd | service | LIVE | queues | route/reconcile | each other | active units | DISK | none | cognition loop | KEEP
- verify-dispatcher | bin/octopus_verify_dispatcher.py | service | LIVE | processed/ | auto-verify to 182 | 182 worker | unit active | DISK | none | verification | KEEP + FIX(F-2 claims-embed)
- timers scheduler/budget/heartbeat | systemd | service | LIVE | events | cycles/metrics | — | list-timers | units on disk | none | ops | KEEP
- calibration engine | bin/octomesh_calibration.py + calibration/ | code+data | LIVE | outcomes | scores | reports | jsonl rows | DISK | none | learning | KEEP
- runtime common (state machine/approvals/budget) | bin/octopus_common.py | code | LIVE | — | gates | daemons | unit-tested | DISK | none | control | KEEP
**Bridges/bots**
- octopus-bridge | /home/ari/octopus-bridge (:8796) | code+service | LIVE | cloud mTLS | board_cp pull | cloud | pid589802 | git(2 dirty) | none | control-plane | KEEP
- octopus-telegram-bridge | unit file only | service | DEAD (no fragment, blocked-config) | — | — | — | inactive | DISK unit | vs alert.py | telegram | CONNECT decision
- ofn alert.py owner-push | ofn/adapters/alert.py | code | SHADOW | events | telegram send | owner | no poller | git | 2nd telegram path | CONNECT one canonical
- Telegram bots x5 | config bot_tokens keys: ziman, lead, studio, studio_partner, __owner__ | config | PARTIAL (mini-apps served; 0 pollers) | — | — | — | 0 pollers | git | — | dialogue | CONNECT
**Business stores** (~/.local/share/ofn)
- painting.sqlite(8 leads) / products(40) / studio(24) / ledger(175 audit) / facts / outbox(25) / consent / audience / assistant(47 chunks) / marketing / inbox | DB | LIVE | services | business data | APIs | row counts | daily backup | — | money path | KEEP
**Other trees**
- hypno-fugu-mini | hypno.run :8895 loopback | product | LIVE-SEPARATE | own DBs | mini-app | telegram webapp | pid672 | git(2 dirty) | none | not owner-decision | KEEP separate
- OCTOPUS/ vault docs | /home/ari/OCTOPUS | docs | SLEEPING | — | — | — | none | DISK | vs ofn/docs | truth | MERGE to one vault
- feet138/runs | disk | data | UNKNOWN | — | — | — | — | DISK | — | — | UNKNOWN
- FUGU-BIZ-SPRINT/ziman, TO-LAPTOP/exchange, ofn-downloads, ofn-old-*, ofn-v0.4-live-backup, ofn-full-backup-* | disk | data/backups | SLEEPING | — | — | — | — | DISK | legacy copies | — | ARCHIVE
- mesh quarantine/snapshots/tasks/constitutions | octopus-mesh/* | evidence+constitution | LIVE-RECORD | — | — | — | files | DISK | published copies in ofn/docs | history | KEEP
- cloudflared | :20241 loopback | infra | LIVE | — | hostnames->local | shells | pid669 | system | — | access | KEEP
