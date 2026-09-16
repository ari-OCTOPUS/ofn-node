# FORGOTTEN-250 — داشبورد رجیستر بدهی (2026-09-15)

۲۵۰ ورودی = ۱۰۰ حمل‌شده (صبح امروز) + 150 تازه. SEASON_LEFTOVER: **40**.

classes: OPEN_WORK 107 · DEBT_HIDDEN 40 · SEASON_LEFTOVER 40 · RULING_UNEXECUTED 24 · DOC_RUNTIME_DISCREPANCY 23 · ABANDONED_PLAN 11 · ABANDONED 5

## ده مورد اول با plan اجرا

### [F-001] rank 21.0 — G8-021 executed but never retired — request now self-stale (base 02fb704d vs live fc993720), burns component budget each
- anchor: `138:/home/ari/ofn/state/ops-agent/state/canary-requests + ops-receipts.jsonl` · `OPS_B_STALE_BASE have:fc993720 at 07:05:00Z`
- plan: بستن با same lane-starvation/budget-burn class that stalled 020 for 2h; supersede-or-retire unblocks W24 pacing immediately

### [F-002] rank 20.8 — Executor starvation defect OW-8: 'return budget-blocked' aborts whole B8 category loop; one blocked request starves inde
- anchor: `F:/backup/09-LANES/OCTOPUS-FORENSIC-REORIENTATION-20260915/OPEN-WORK.json` · `OW-8 runtime-proven 2026-09-15T06:38Z`
- plan: بستن با any future blocked request freezes every independent deploy lane — autonomy cannot drain its own queue

### [F-005] rank 20.6 — fleet-jobs bus: 61 of 91 rows stuck non-terminal (17 QUEUED, 16 LEASED, 15 RUNNING, 13 ACK_RESULT, 13 PERSISTED) — most 
- anchor: `138:/home/ari/ofn/state/fleet-jobs/fleet_jobs.jsonl` · `state histogram 07:10Z`
- plan: بستن با 'closed loop live' claims rest on timers; the bus itself shows most work never completes — training data and scheduling integrity

### [F-007] rank 20.4 — TRAFFIC-DECISION owner card open — 'the single real money unlock' (ads/outreach/market choice) blocks the entire revenue
- anchor: `138:/home/ari/ofn/state/revenue-drive/owner-review.json + F:/backup/01 - Dashboard/OCTOPUS-VITAL-DATA-2026-09-08.md` · `'تنها قفلِ واقعی جلوی پول'`
- plan: بستن با verified_cash=0 with 17 authorized packets unsent; one owner decision opens the funnel's next stage

### [F-006] rank 15.6 — restore_drill NOT_RUN — the biggest hidden risk per GOV-V8's own register, unexecuted in three ruling docs + no drill ar
- anchor: `F:/backup/06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/GOV-V8-REVENUE-IGNITION-2026-09-05.md` · `L188 'restore_drill: NOT_RUN ... بزرگ‌ترین ریسک پنهان'`
- plan: بستن با every durability claim (snapshots, 180 copies, RPO/RTO) is unbacked until one drill restores and read-backs

### [F-008] rank 15.4 — secrets unrotated (risk_accepted) + chat-pasted Claude key not deleted + 76 committed files leak IPs/board names + publi
- anchor: `F:/backup/06-EVIDENCE/OCTOPUS-OWNER-BOARD-2026-08-24/CURRENT-TRUTH.md` · `L60 WARNINGS + L130 sanitize backlog + CHAT_KEY_WARN`
- plan: بستن با credential exposure is the only unfixed item that can convert every other investment into loss; chat-key deletion is a 30-second owner action

### [F-003] rank 13.0 — 114/160 reboot-orphans: evaluator+ingestion run under nohup, staged systemd units never installed (OW-4)
- anchor: `F:/backup/09-LANES/OCTOPUS-FORENSIC-REORIENTATION-20260915/staged-units/INSTALL-PLAN-114-160.md` · `STAGED, NOT APPLIED`
- plan: بستن با one power event silently opens the closed learning loop; install is 10 min with the staged plan

### [F-012] rank 13.0 — G22 runtime behavioral proof owed: enforcement code is live but the queued negative probe has received no disposition (s
- anchor: `F:/backup/09-LANES/OCTOPUS-FORENSIC-REORIENTATION-20260915/ROUND2-VERDICTS-20260915.md` · `'enforcement = PENDING_PROBE'`
- plan: بستن با dependency gate is the DAG's backbone; without behavioral proof a future regression could re-enable decorative dependencies

### [F-013] rank 13.0 — PB-1 24h continuity soak cannot PASS before 2026-09-16T04:31Z — acceptance check owed
- anchor: `F:/backup/09-LANES/OCTOPUS-BODY-ADAPTATION-NEXT-20260915/CURRENT-STATE.json` · `'reported_status': 'IN_PROGRESS'`
- plan: بستن با laptop-independence is the season's acceptance keystone; a missed-tick count decides it honestly

### [F-014] rank 13.0 — TRIO-002 + W3G30-COMBINED deploys complete the G28 arc (decision consumer, precondition freeze, CATSCOPE) — queued, exec
- anchor: `138: canary-requests/native-Z-SUCCESSOR-TRIO-002.json + W3G30` · `ROUND31 'QUEUED (inside TRIO v3d) awaiting only TRIO deploy'`
- plan: بستن با decision-consumer protection stays inert until deployed ('first real card NO_TASK' risk)

## جدول کامل (مرتب بر رتبه)

| rank | id | قلمرو | class | عنوان |
|---:|---|---|---|---|
| 21.0 | F-001 | runtime | OPEN_WORK | G8-021 executed but never retired — request now self-stale (base 02fb704d vs live fc993720), burns c |
| 20.8 | F-002 | lanes | OPEN_WORK | Executor starvation defect OW-8: 'return budget-blocked' aborts whole B8 category loop; one blocked  |
| 20.6 | F-005 | runtime | DEBT_HIDDEN | fleet-jobs bus: 61 of 91 rows stuck non-terminal (17 QUEUED, 16 LEASED, 15 RUNNING, 13 ACK_RESULT, 1 |
| 20.4 | F-007 | runtime | OPEN_WORK | TRAFFIC-DECISION owner card open — 'the single real money unlock' (ads/outreach/market choice) block |
| 15.6 | F-006 | 06-EVIDENCE | RULING_UNEXECUTED | restore_drill NOT_RUN — the biggest hidden risk per GOV-V8's own register, unexecuted in three rulin |
| 15.4 | F-008 | 06-EVIDENCE | OPEN_WORK | secrets unrotated (risk_accepted) + chat-pasted Claude key not deleted + 76 committed files leak IPs |
| 13.0 | F-003 | lanes | OPEN_WORK | 114/160 reboot-orphans: evaluator+ingestion run under nohup, staged systemd units never installed (O |
| 13.0 | F-012 | lanes | OPEN_WORK | G22 runtime behavioral proof owed: enforcement code is live but the queued negative probe has receiv |
| 13.0 | F-013 | lanes | OPEN_WORK | PB-1 24h continuity soak cannot PASS before 2026-09-16T04:31Z — acceptance check owed |
| 13.0 | F-014 | runtime | OPEN_WORK | TRIO-002 + W3G30-COMBINED deploys complete the G28 arc (decision consumer, precondition freeze, CATS |
| 13.0 | F-016 | surfaces | OPEN_WORK | AUTO1 owner display phone number never supplied — fail-closed caller queue dark since 09-08 (recurri |
| 13.0 | F-026 | 06-EVIDENCE | OPEN_WORK | buy.nsw supplier registration: nightly-email path awaiting owner's 30-minute action (season hero ite |
| 12.8 | F-004 | lanes | OPEN_WORK | W24 live-ingest end-to-end still unproven: binder deploy pending + zero owner TG traffic since STRAT |
| 12.8 | F-019 | lanes | DEBT_HIDDEN | imap customer-reply alert consumer absent: replies to the 3 sent quotes land unseen until the 6h rev |
| 12.8 | F-020 | runtime | OPEN_WORK | 17 CHANNEL_AUTHORIZED packets unsent + rate-card single-source — funnel staged but stalled at owner  |
| 12.8 | F-071 | surfaces | OPEN_WORK | MONEY-BATCH owner card: send 5 quote packets vs owner-sends — vote never cast |
| 12.6 | F-010 | 06-EVIDENCE | OPEN_WORK | G19 producer lifecycle unproven (restart/cursor-loss/rotation/truncation) + G27 WAL-or-temp-file ato |
| 12.6 | F-070 | 06-EVIDENCE | RULING_UNEXECUTED | B-1 bootstrap single-order payment path proposed (ERRATA-AND-UNBLOCK), never executed, owner decides |
| 12.6 | F-098 | carried-misc | OPEN_WORK | CHECKOUT-1: zero orders with store live — no checkout funnel diagnosis ever run (251+ checks recorde |
| 12.6 | F-099 | carried-misc | OPEN_WORK | WORKER-BIND 7-step exec checklist unticked (re-hash, HB paths, mesh proof, shadow-ledger rows, JetSt |
| 12.6 | F-100 | carried-misc | OPEN_WORK | deep-scan itself must become a service: this 100-list is a snapshot; without a weekly tick it rots i |
| 12.4 | F-009 | lanes | OPEN_WORK | owner-decision backlog register: ~20 votes pending across seasons (D-0..D-3 ziman, MP-V41 ×3, EX2 go |
| 12.4 | F-017 | lanes | ABANDONED_PLAN | hardware build-out T1-T6 not started per corrected DoD (4 boards still idle, NPU unused, node auth P |
| 12.4 | F-069 | lanes | OPEN_WORK | money gate: no callable spend package exists — design-only; identity requirement for bare «بفرست» st |
| 10.4 | F-091 | carried-misc | OPEN_WORK | D3 key rotation checklist unticked (GLM/DEEPSEEK/TG tokens) |
| 10.2 | F-047 | carried-misc | OPEN_WORK | S: SSD archive offline since mid-op (36.4GB of archives disconnected) — deletions were stopped, but  |
| 10.0 | F-018 | lanes | OPEN_WORK | owner physical step pending: SD-card swap + power for remaining boards ( enrollment's 'only blocker  |
| 10.0 | OPS-1 | _ops | SEASON_LEFTOVER | STOP-FUGU circuit breaker auto-tripped 2026-09-15 05:56 and was never reset; paid/primary brain quar |
| 10.0 | OPS-2 | _ops | SEASON_LEFTOVER | deep_think sessions never reached the expensive brain all season (54 paid-call-failed alerts Sep 7-1 |
| 10.0 | OPS-3 | _ops | SEASON_LEFTOVER | lead_email_intake IMAP failing every day of the season window (~39 alerts Sep 8-15) - lead pipeline  |
| 10.0 | SE-3 | 01 - Dashboard (season sweep) | SEASON_LEFTOVER | verified_cash still $0.00 — Ziman store live with 251+ checkout checks and zero orders |
| 10.0 | 4D-16 | 4d_system | RULING_UNEXECUTED | VERDICT_QUEUE: all 4 governing verdicts (30-day run, Telegram, self-code risk, budget cap) still 'op |
| 10.0 | 4D-18 | 4d_system | OPEN_WORK | 24/7 self-heal supervisor promised but never installed: no supervisor_log.jsonl/logs, no CONTROL_PLA |
| 10.0 | OPS-7 | _ops | RULING_UNEXECUTED | SIG-IV independent verification still pending: owner's WAVE1 executive-order gate 1 never passed (ve |
| 10.0 | RT-1 | runtime | OPEN_WORK | board138 deep-scan findings-current.json holds ~65 open findings; G8-021 executed but never retired, |
| 10.0 | RT-8 | runtime | DEBT_HIDDEN | board138 ~/ofn dirty: data/gates.json (governance) modified uncommitted + live-code .bak files from  |
| 9.8 | F-011 | runtime | OPEN_WORK | OW-9: B5 circuit breaker OPEN since 06:38Z, feeding failures not root-caused |
| 9.8 | F-051 | lanes | OPEN_WORK | PB-4 retest owed with 371-fact corpus + held-out questions (first run n=12, powered but small) |
| 9.8 | KN-5 | 07 - Knowledge | OPEN_WORK | 60MB raw DNA + GenomeInsight PDF + derived دیتا.txt still inside vault vs rule O-04; old Silabi-Bot  |
| 9.8 | RT-15 | runtime | OPEN_WORK | ops_agent.py.pre-retirefix-20260915 backup next to live ops_agent.py on 138 — today hotfix uncommitt |
| 9.6 | F-049 | 06-EVIDENCE | OPEN_WORK | semantic retrieval stage pending (extractive-v1 keyword-only) — the last open intelligence blocker |
| 9.0 | F-031 | carried-misc | OPEN_WORK | Google Business Profile listing pending owner login (directory legs YP/TrueLocal captcha-blocked, Ho |
| 9.0 | F-046 | runtime | DEBT_HIDDEN | smartmontools.service FAILED on 138 — disk monitoring down on the node that survived a full disk cri |
| 8.6 | F-022 | 06-EVIDENCE | RULING_UNEXECUTED | Class B recovery armed but never executed in production (G2) — rollback path untested where it matte |
| 8.6 | F-025 | surfaces | OPEN_WORK | containment rollback plan never exercised (sandbox escape/fire drill) |
| 8.6 | F-057 | surfaces | OPEN_WORK | OP-8: paid calls burn without output — measured open at 64%, no mitigation applied |
| 8.6 | F-084 | lanes | OPEN_WORK | C-R0 identity: workers-comp + painter licence certificates still missing from vault |
| 8.6 | F-097 | carried-misc | OPEN_WORK | mesh auth hardening: node_id auth PASS but PENDING_AUTH on all 4 workers + NATS password ask (season |
| 8.4 | F-023 | carried-misc | OPEN_WORK | studio-consent chain 14/14 bullets unsigned (Saba+owner attestations, collection_id linkage, 182 wit |
| 8.4 | F-027 | 06-EVIDENCE | OPEN_WORK | PARKED-LANES: 8 lanes locked until 'campaign verified_payment_count=1' — no first payment has ever u |
| 8.4 | F-028 | carried-misc | OPEN_WORK | Ziman season TODO: PayID setup, real pricing+photography of 20 units, unit costs, competitor table — |
| 8.4 | F-038 | 06-EVIDENCE | OPEN_WORK | owner-key chain: B1 ED25519 formal signing pending chat approval; owner-key.enc hash never reproduce |
| 8.4 | F-056 | lanes | OPEN_WORK | NPU capacity unmeasured/unused: 6 benchmark PASS rows but 138 row NOT_RUN; 'nominal 42 TOPS' explici |
| 7.0 | F-021 | 06-EVIDENCE | OPEN_WORK | deploy keys disabled on ofn-node (G1): autonomy branches cannot push; owner toggle pending |
| 7.0 | F-044 | 06-EVIDENCE | OPEN_WORK | WAL re-arm value REPORTED but UNVERIFIED until independent read |
| 7.0 | F-045 | lanes | OPEN_WORK | B-PULSE-IMAP: the exact 15875B listener file on 138 never confirmed + LANE-MATRIX naming clash unres |
| 7.0 | F-082 | lanes | DOC_RUNTIME_DISCREPANCY | llama-8081 on 138: notes say live, probe said DOWN + binary absent (resolution: null) — and 180 now  |
| 7.0 | 4D-1 | 4D-Vault | SEASON_LEFTOVER | No recurring vault reindex: owner-only scheduling decision left open; chroma only manually touched s |
| 7.0 | ARC-1 | archive-cluster | SEASON_LEFTOVER | Season handoff archived 2026-09-07 with EX1 criterion v3.0=NOT_PASSED and EX3 not started (live lane |
| 7.0 | DOC-4 | OCTOPUS-DOCTOR | SEASON_LEFTOVER | SCAN-2026-09-15: confirmed_revenue = 0 🔴 — the whole organism shows zero confirmed revenue while 03- |
| 7.0 | SE-5 | 01 - Dashboard (season sweep) | SEASON_LEFTOVER | Containment rollback plan never exercised while organism self-deploys patches |
| 7.0 | SE-8 | 06-EVIDENCE (season sweep) | SEASON_LEFTOVER | SEASON-CORRECTION phase-1 funnel un-stall (>=30 fresh leads, 3 warm follow-ups) — execution not evid |
| 7.0 | SE-14 | 01 - Dashboard (season sweep) | SEASON_LEFTOVER | ziman-gift.com NXDOMAIN (expired) — owner renewal card unanswered since 09-08 while store counts tra |
| 7.0 | 4D-17 | 4d_system | OPEN_WORK | Telegram owner channel never configured: empty token in .env, every decision packet 'queued (not-con |
| 7.0 | 4D-19 | 4d_system | RULING_UNEXECUTED | B10 standalone git init ordered 'owner must run once on Windows' - never executed; contradicts MANIF |
| 7.0 | 4D-20 | 4d_system | ABANDONED | Promised one-month autonomous run lasted 6 days (2026-08-15 to 2026-08-21) and was never concluded;  |
| 7.0 | 4D-22 | 4d_system | RULING_UNEXECUTED | Kill-switch unimplemented: KillSwitchCommand 'v1: always False remains', no live execution path desp |
| 7.0 | ARC4-2 | 04 - Architect System | DEBT_HIDDEN | E4 double-fire structural gap still live: chrono.py request() mints fresh uuid4 and release_gated_ef |
| 7.0 | INB-1 | 00 - Inbox | OPEN_WORK | OWNER-PENDING master checklist: 15+ unchecked owner votes (VOTE1-4 hard-test, P0 PEP wire, telegram  |
| 7.0 | INB-2 | 00 - Inbox | RULING_UNEXECUTED | Owner-approved A2-001 merge/push/.180/ofn-bridge never executed despite explicit 'owner-approved' ti |
| 7.0 | INB-3 | 00 - Inbox | OPEN_WORK | OCTOPUS-Cortex ONLOGON schtask never registered; cortex dies on next Windows reboot (owner vote pend |
| 7.0 | PRJ-8 | 03 - Projects | DEBT_HIDDEN | Project-F miniapp: 8 read-only API routes (/api/state,/api/legs,…) served with NO initData auth on a |
| 7.0 | PRJ-9 | 03 - Projects | OPEN_WORK | Project-F: 11 owner verdicts + GATE 0 + 3 human signatures A pending since 2026-07-20; R9/R10 backlo |
| 7.0 | PRJ-16 | 03 - Projects | RULING_UNEXECUTED | Control-plane approvals queue backlog: forensic report found 3 approvals stuck since 2026-07-25 (one |
| 7.0 | SML-6 | 01-TRUTH | OPEN_WORK | Season 5 Shopify manual checklist (5 steps) recorded as remaining, closure unproven |
| 6.8 | F-030 | lanes | OPEN_WORK | 18 enrichment rows verified:false in painting leads (research pass never run) + ~19 strata leads own |
| 6.8 | F-033 | surfaces | OPEN_WORK | Airtasker zero leads — cause UNKNOWN, never measured (watch wired but intake empty) |
| 6.8 | F-035 | lanes | DOC_RUNTIME_DISCREPANCY | W24 chain documentation claims PB-4 NOT_RUN / corpus=6 — stale vs runtime (PB-4 IMPROVED 0.75v0.0, f |
| 6.8 | F-036 | 07-HANDOFF | DOC_RUNTIME_DISCREPANCY | engineering-entrypoint chain stale: AGENTS.md points at 09-04 while 0906/0907 exist and none referen |
| 6.8 | F-050 | surfaces | DEBT_HIDDEN | memory-consolidate always produces 0 semantic notes — by-design or broken edge, never determined |
| 6.8 | F-053 | lanes | OPEN_WORK | GAP-LEDGER.jsonl canonical missing (0 rows vs 64 in markdown twin) — L6 blocker G_P1 forever open |
| 6.8 | F-073 | 06-EVIDENCE | RULING_UNEXECUTED | GOV-AUTONOMY-V3 defines an OWNER_DECISIONS_PENDING counter — never wired to any dashboard/card gener |
| 6.8 | F-080 | lanes | DEBT_HIDDEN | INITIATIVE two-bot mr trap live and unfixed — owner TODO since 08-06 (40 days) |
| 6.8 | F-083 | lanes | OPEN_WORK | Airtasker latency/payload values unmeasured against real app push |
| 6.8 | F-085 | surfaces | OPEN_WORK | Q-MARKET: Atelier theme still Draft (unpublished after price ×1.5 exec); W9-1R call-service purchase |
| 6.8 | OPS-4 | _ops | SEASON_LEFTOVER | tg-center silently dying all season: ~24 WATCHDOG REVIVE relaunches Sep 6-15 incl. 3x on Sep 15 |
| 6.8 | OPS-5 | _ops | SEASON_LEFTOVER | chrono.db 'database is locked' beat errors recurring in season (8 events; 2 on Sep 15) - heartbeat w |
| 6.8 | PRJ-1 | 03 - Projects | SEASON_LEFTOVER | Ziman customer domain ziman-gift.com dead (NXDOMAIN) — owner's 2-minute Shopify fix still pending si |
| 6.8 | PRJ-4 | 03 - Projects | SEASON_LEFTOVER | TOP-5 outreach GO'd 2026-09-07 (Whelan #1, 7/7 QUALIFIED) — pack prepared but no evidence the human  |
| 6.8 | RT-2 | runtime | SEASON_LEFTOVER | octopus-revenue-drive.service dead 4h27m mid-season-window on 138 |
| 6.8 | SML-12 | agent-prompts | SEASON_LEFTOVER | CAPABILITY-GAP megaprompt deadlines (standing GO to 09-14, msg38 same-day) expired with no outcome r |
| 6.8 | SE-12 | 07-HANDOFF (season sweep) | SEASON_LEFTOVER | Owner directive 09-11 fuel fix option-1 (base caps 700/800 to 1500) — landing unverified, burn recur |
| 6.8 | 4D-24 | 4d_system | DEBT_HIDDEN | TCB guards itself with no external validator/checksum auditor - acknowledged single point of failure |
| 6.8 | 4D-26 | 4d_system | DEBT_HIDDEN | BLACK-BOX.md relocation target F:\Black Box does not exist and restore bundle _history/nbb-cp-full-h |
| 6.8 | ARC4-5 | 04 - Architect System | DEBT_HIDDEN | Telegram/WebApp Phase 0: BEARER patch committed on a separate branch (00c4fbf) with deploy=0 and 'Gi |
| 6.8 | DOC-2 | OCTOPUS-DOCTOR | DOC_RUNTIME_DISCREPANCY | F-AUTO-BRAKE (scan 2026-09-09): heart braked again — effective_period_s=900 with brake:cardiac vs bi |
| 6.8 | OPS-19 | _ops | RULING_UNEXECUTED | Owner ruling 2026-07-30: narrow constitution fix for self-merge WITH safety net (regression vs pinne |
| 6.8 | RT-3 | runtime | DEBT_HIDDEN | Laptop F:/ofn-node working tree dirty: 19 files +1145/-556 uncommitted, incl budget/opslib.py DELETE |
| 6.8 | RT-7 | runtime | OPEN_WORK | OWNER-CHECKLIST.md: all 4 owner-only actions (ABN/insurance, .com.au domain, deploy keys, NSW licenc |
| 6.8 | RT-10 | runtime | RULING_UNEXECUTED | ETI fast-convergence lane armed a one-command reconciliation due 2026-09-13T06:30Z never executed |
| 6.8 | SML-13 | agent-prompts | OPEN_WORK | CONNECT-ALL phase A (octopus-shopify-watch on 138) gated on D0_domain awaiting owner DNS, no closure |
| 6.6 | F-015 | lanes | OPEN_WORK | PR backlog cluster: #102 CODEOWNERS (Elahe), #106 merge, #201/#208 painting, #236-238 CODEOWNERS, #2 |
| 6.6 | F-029 | lanes | ABANDONED_PLAN | REV-1 shelf SKU never built + SKU C/D/E path open (Q-MARKET-COMPARE agreed path) |
| 6.6 | F-041 | 06-EVIDENCE | OPEN_WORK | G3: load1 self-measurement extractor missing — reconcile window EXPIRED_UNOBSERVED, scoped proposal  |
| 6.6 | F-052 | lanes | OPEN_WORK | F2 capability/freshness wiring into scheduler self-model — shadow designed, never wired |
| 6.6 | F-086 | surfaces | OPEN_WORK | 24 verify FAILs outstanding from 09-09 GAP/VBAA round (OP-1b canonical folder + OP-2 ledger-writer r |
| 6.6 | F-095 | lanes | OPEN_WORK | T4 media-change MAC/DHCP strategy design + proof outstanding (hardware exec) |
| 6.6 | OPS-18 | _ops | SEASON_LEFTOVER | CHECKLIST-lead-arming-2026-08-01: 17 boxes never ticked; SMTP self_test proof and real-source phases |
| 6.6 | PRJ-2 | 03 - Projects | SEASON_LEFTOVER | Ziman msg38 season deadline 2026-09-08T12:10Z passed with state carrier unreadable from laptop — no  |
| 6.6 | RT-5 | runtime | RULING_UNEXECUTED | GAP-LEDGER canonical switch (OP-1b) blocked since 2026-09-09 on '2 of 4' Downloads files still missi |
| 6.4 | F-024 | 06-EVIDENCE | OPEN_WORK | missing-wirings census: 50 gaps found 09-03, only items 13/21 auto-fixed — 48 wirings still absent i |
| 6.4 | F-034 | carried-misc | DEBT_HIDDEN | brushline painting pipeline: 4 open phase TODOs (asset enhancement Phase 2, DA/strata signals Phase  |
| 6.4 | F-039 | surfaces | RULING_UNEXECUTED | UNLOCK-REGISTRY: 15+ locks sit PROPOSED never executed (secret_rotation repurpose, OWNER_KEY, L4 run |
| 6.4 | F-040 | 06-EVIDENCE | OPEN_WORK | freedom-v2 phase 2 open: no-witness recovery, cross-node apply, GitHub push autonomy |
| 6.4 | F-042 | lanes | DEBT_HIDDEN | JetStream consumers=0: NATS durability installed but nothing subscribes — 'NOT_CLAIMED' honesty alre |
| 6.4 | F-043 | 06-EVIDENCE | OPEN_WORK | sensorium in-band receipts non-canonical + clock correctness unproven |
| 6.4 | F-064 | lanes | OPEN_WORK | EX1 acceptance chain: original contract NOT_PASSED, v3.1 draft unadopted, EX3 blocked, three C-contr |
| 6.4 | F-065 | lanes | ABANDONED_PLAN | L2-L6 research lane stack blocked: blind-test gate → real recorded split (owner) → 29 verifies re-ru |
| 6.4 | F-068 | 06-EVIDENCE | RULING_UNEXECUTED | economic-learning: zero-payment failure trio open until differing-parameter test (design-only, QUEUE |
| 6.4 | F-074 | 06-EVIDENCE | OPEN_WORK | EDGE6 business loop blocked + GitHub publication remote unlocated (Telegram webapp phase0) |
| 5.0 | ARC-2 | archive-cluster | SEASON_LEFTOVER | Named metric defect P3-ORPHAN-SCALAR archived inside season worktree; 4 contradiction rows still sta |
| 5.0 | GAP-1 | runtime | SEASON_LEFTOVER | GAP ledger verify: 15 tools.* modules absent on 138 -> 24 FAIL remain unactioned since 09-09 measure |
| 5.0 | OPS-6 | _ops | SEASON_LEFTOVER | GITWRITE-FAILED.flag re-fired today (2026-09-15_055021, lock TIMEOUT after 40 attempts) and has been |
| 5.0 | OPS-15 | _ops | SEASON_LEFTOVER | debate SURVIVORS-QUEUE: 388 entries, 234 pending-human + 154 undecided-after-3-rounds, none ever res |
| 5.0 | 4D-3 | 4D-Vault | OPEN_WORK | MOC 'خودتنظیم‌گری و خودآگاهی' pinned status: seed - all 5 related notes (Governor/PulseCore/MycoCard |
| 5.0 | 4D-4 | 4D-Vault | OPEN_WORK | 46 broken wikilinks vault-wide; 22+ atomic notes of the 'SOG engineering grammar' (15 principles) wi |
| 5.0 | 4D-9 | 4D-Vault | DEBT_HIDDEN | Entire 4D-Vault is a chroma.sqlite3 reconstruction (last real content 2026-07-11/12); original Deskt |
| 5.0 | 4D-21 | 4d_system | OPEN_WORK | B11 LLM-stack migration decision requires >=30 shadow records; llm_shadow.jsonl stuck at 6 records s |
| 5.0 | 4D-23 | 4d_system | DEBT_HIDDEN | Self-code approval pipeline never exercised end-to-end: proposals sandbox empty since creation, 0 pr |
| 5.0 | 4D-27 | 4d_system | RULING_UNEXECUTED | B6 SOG integration: steps 2-3 draft-only behind 'boss choice'; 3 owner decisions open (boss, nbb_cp  |
| 5.0 | 4D-29 | 4d_system | OPEN_WORK | Second-Brain Super-Governor: CLAUDE.md still stamps spec 'هنوز ساخته نشده'; Phase 2/3 blocked on own |
| 5.0 | 4D-31 | 4d_system | DOC_RUNTIME_DISCREPANCY | REGISTRY.md declares 4d_system 'active-ready' while DEPRECATED.md marks the folder archive/opt-in an |
| 5.0 | ARC4-1 | 04 - Architect System | RULING_UNEXECUTED | MASTER-PLAN repair-and-complete (EFE-vision, TG-gap, Hebbian-bridge) has sat 'AWAITING OWNER RATIFIC |
| 5.0 | ARC4-7 | 04 - Architect System | DEBT_HIDDEN | G-26/G-15: fusion self-improvement loop 'proof' of 0.6→0.8→1.0 was entirely MOCK with keyword scorer |
| 5.0 | ARC-7 | archive-cluster | DOC_RUNTIME_DISCREPANCY | CURRENT-TRUTH mirror drift: archived mirror-cleanup-20260902 copy differs from live 01-TRUTH/CURRENT |
| 5.0 | DOC-1 | OCTOPUS-DOCTOR | DEBT_HIDDEN | F-AUTO-FROZEN-CONTROL-PLANE: octopus_state self_awareness stuck 'green' since 2026-07-18 with 0 writ |
| 5.0 | KN-2 | 07 - Knowledge | OPEN_WORK | genome-system plan milestones never executed: off-site backup #3 (restic/rclone) + monthly restore d |
| 5.0 | OPS-10 | _ops | ABANDONED | action_bridge completed with 66 green tests + 8 red mutations but wired to nothing: IMPLEMENTED_NOT_ |
| 5.0 | PRJ-5 | 03 - Projects | OPEN_WORK | Lead pipeline: SMTP transport written+tested but dark; owner vote on OCTOPUS_SMTP_* / WIRE_LEAD_OUTB |
| 4.8 | KN-4 | 07 - Knowledge | SEASON_LEFTOVER | Orphan quarantined in genome ledger dated 2026-09-02, file created 2026-09-08: SELF_IMPROVE_DIGEST b |
| 4.8 | SE-1 | 01 - Dashboard (season sweep) | SEASON_LEFTOVER | Nodes 114/160 run via nohup — systemd units never installed (continuity risk) |
| 4.8 | SE-6 | 01 - Dashboard (season sweep) | SEASON_LEFTOVER | G27 producer ACK boundary lacks WAL/atomic temp-file — known receipt-loss window left open |
| 4.8 | 4D-6 | 4D-Vault | DOC_RUNTIME_DISCREPANCY | Vault appendix provenance points to Desktop originals (4D/SOG-multiagent-handoff 2.md) that exist no |
| 4.8 | 4D-10 | 4D-Vault | OPEN_WORK | MAS-Audit checklist promised a spec + implementation plan 'later' (بعداً) - never produced |
| 4.8 | 4D-30 | 4d_system | DEBT_HIDDEN | Daemon died with unresolved HIGH-priority kernel review pending: manifest_fresh=false, action=review |
| 4.8 | ARC4-3 | 04 - Architect System | OPEN_WORK | architect PROJECT 2026-08-29: 'مگاپرامپت کل سامانه GO نیست' — whole-system megaprompt un-GO'd; 138 L |
| 4.8 | ARC4-4 | 04 - Architect System | DEBT_HIDDEN | ofn.service on node 191: UNPROVEN_RESTART_REQUIRED, V2 returns 401, fixed=NO — live leg running unpr |
| 4.8 | ARC4-9 | 04 - Architect System | RULING_UNEXECUTED | DECISIONS-REGISTRY D6/D7 fallback ladder (glm/ollama=propose, A0-A2 auto) ratified 2026-08-16 — but  |
| 4.8 | DOC-3 | OCTOPUS-DOCTOR | DOC_RUNTIME_DISCREPANCY | int('متوسط') crash signature ×346: F-05 declared it fixed+closed on 2026-07-29, yet the same signatu |
| 4.8 | DOC-5 | OCTOPUS-DOCTOR | DEBT_HIDDEN | F-02 self-referential reward (🔴, never revised): outcomes.jsonl 0/230 rows have an outcome field; 83 |
| 4.8 | DOC-6 | OCTOPUS-DOCTOR | DEBT_HIDDEN | F-06 zero-cost structural hole (🔴 open): subscription:max forces est_worst_case()=0, so EFE's Cost t |
| 4.8 | DOC-7 | OCTOPUS-DOCTOR | RULING_UNEXECUTED | F-08: test suite not hermetic — 56 persistently red files on a clean HEAD worktree keep the day --li |
| 4.8 | DOC-9 | OCTOPUS-DOCTOR | DEBT_HIDDEN | Doctor findings vault ballooned to 222 files — ~200 auto-alert findings (F-AUTO-ALERT-*) with repeti |
| 4.8 | GEX-1 | _github-export | OPEN_WORK | ofn-node export worktree dirty on branch export/octopus-surgery-20260830 with 45+ local agent/* bran |
| 4.8 | GEX-2 | _github-export | RULING_UNEXECUTED | Export HANDOFF 'قدم بعد': owner must hand CONTROL_URL+key for G7 Gate 0 and same-day secret rotation |
| 4.8 | INB-4 | 00 - Inbox | OPEN_WORK | Telegram live-activation blocked solely on BotFather token rotation — 'تنها قدم باقی‌مانده' |
| 4.8 | INB-13 | 00 - Inbox | OPEN_WORK | Quote engine LOCKED pending owner approval of OCP rate card (live revenue path frozen since 2026-09- |
| 4.8 | KN-3 | 07 - Knowledge | DEBT_HIDDEN | genome-system daily backup promise broken: STATUS.json schedule says 'backup: daily' but _backups ho |
| 4.8 | KN-8 | 07 - Knowledge | RULING_UNEXECUTED | OCTOPUS-TRUTH open-work list: independent verify_live_store.py never run on live DB, ADR-041 still m |
| 4.8 | KN-9 | 07 - Knowledge | DEBT_HIDDEN | CURRENT-REALITY: 4 legs dead (mining/crypto/studio_pf/knowledge), daemon 4d stopped since Aug 2, 14  |
| 4.8 | OPS-8 | _ops | DEBT_HIDDEN | T5 supervision taxonomy built and tested but never consumed: tg-center-watchdog.ps1 has zero referen |
| 4.8 | OPS-9 | _ops | OPEN_WORK | 60-minute polling-only soak required by every version of the loop-closure acceptance criteria was ne |
| 4.8 | OPS-11 | _ops | ABANDONED | world_discovery organ: 85/85 tests pass but explicitly IMPLEMENTED_NOT_INTEGRATED pending senior-age |
| 4.8 | OPS-12 | _ops | OPEN_WORK | unified_control package (Self→Compass→Heart→Mission→Action) not integrated; Self-model freshness mar |
| 4.8 | OPS-13 | _ops | OPEN_WORK | handshake A2-001 Mirror Manifest Verifier reached QUARANTINED_PASS (tests 10/10 twice) but never mer |
| 4.8 | OPS-14 | _ops | OPEN_WORK | D1 independent-audit package (Ed25519 manifest, AEB bundles, RUN-AUDIT.ps1) prepared 2026-08-15/16 b |
| 4.8 | OPS-23 | _ops | OPEN_WORK | MiniApp phase 4 'control' write-actions (leg.pause, mission.approve, flag.toggle, doctor.run...) pro |
| 4.8 | PRJ-3 | 03 - Projects | DEBT_HIDDEN | Ziman branding engine built but never called: branding:null for 3+ weeks, drafts_count=0, capacity/i |
| 4.8 | PRJ-14 | 03 - Projects | DEBT_HIDDEN | OWNER BOARD budget engine expired: 'Sakana Max ends Aug 27' / 'Budget engine to 2026-08-27' — no ren |
| 4.8 | RT-4 | runtime | OPEN_WORK | F:/ofn-node has 227 untracked files incl 31 untracked 09-LANES dirs (P1-*, GAP-19x, BOARD-SELF-MODEL |
| 4.8 | SML-2 | 06-RISKS | RULING_UNEXECUTED | TCB #3 ratify (C-035 anchor patch) PATCHED-UNSIGNED; real 3-key rotation D3 still open |
| 4.8 | SML-3 | 06-RISKS | DEBT_HIDDEN | P10 daily_cap wiring bug (daily_pool->0.0) recorded OPEN with fix promised in FASE 6, never landed |
| 4.8 | SML-7 | 01-TRUTH | OPEN_WORK | Shipping-policy PR #189 recorded OPEN in Season 5 register |
| 4.6 | PRJ-13 | 03 - Projects | SEASON_LEFTOVER | Accounting telemetry escalate conflict + budget guard 'in deep debug' logged 2026-09-07 with no reso |
| 4.6 | RT-9 | runtime | SEASON_LEFTOVER | 12 days of ECONOMIC-LEARNING auto-runs (auto-20260904..auto-20260915) untracked on board138 |
| 4.6 | RT-14 | runtime | SEASON_LEFTOVER | Six agent/eti-* branches and five E: worktrees linger unmerged; run2 ended canonical PARTIAL never c |
| 4.6 | SE-4 | 01 - Dashboard (season sweep) | SEASON_LEFTOVER | Memory durability restart/restore: two same-day verdicts conflict (PARTIAL-untested vs PASS) |
| 4.6 | SE-7 | 06-EVIDENCE (season sweep) | SEASON_LEFTOVER | STOP-FUGU manual flag blocks the paid fugu path since 09-15; FX pin verification degraded to LOCAL |
| 4.6 | SE-15 | 01 - Dashboard (season sweep) | SEASON_LEFTOVER | UNLOCK-REGISTRY rows L04 (secret_rotation) and L11 (OWNER_KEY rewording) frozen at PROPOSED since 09 |
| 4.6 | ARC4-6 | 04 - Architect System | DEBT_HIDDEN | MiniApp root cache went LIVE 'با WIP پذیرفته‌شده' but loaded source hash is 'هنوز dirty/uncommitted' |
| 4.6 | ARC4-8 | 04 - Architect System | OPEN_WORK | Worker-agent build (2026-08-16) phases 0-8 coded and committed, but owner verdicts on 3 questions +  |
| 4.6 | OPS-20 | _ops | OPEN_WORK | HEALTH-BASELINE P1 (2026-07-18) still open: 14 pre-existing red tests (mining/ziman schema drift) ne |
| 4.6 | OPS-21 | _ops | DEBT_HIDDEN | Saba Studio and LangarBot still shipped without singleton guards — 'add before going live' pending s |
| 4.6 | RT-6 | runtime | DOC_RUNTIME_DISCREPANCY | docs/DISCOVERY.md still sells the retired email channel as live frontier (sent 2026-09-01, 'first au |
| 4.6 | RT-13 | runtime | OPEN_WORK | Four unmerged worktree branches with real work: s2b-claim-record, autonomy-full-20260912, transform- |
| 4.6 | SML-1 | _memory | OPEN_WORK | Organism runtime state DEGRADED with zero green streak in NOW.md |
| 4.6 | SML-14 | 07-HANDOFF | DOC_RUNTIME_DISCREPANCY | GAP-LEDGER count contradiction (0 rows in vault vs 64 claimed) open with resolution null |
| 4.6 | SML-16 | 07-HANDOFF | OPEN_WORK | EX1 v3.0 NOT_PASSED and EX3 unstarted after owner three-layer answer |
| 4.0 | F-048 | 06-EVIDENCE | DEBT_HIDDEN | 4d consolidation tick was dead 11 days (08-23→09-03) — 'partially healed' per agent note; feed conti |
| 3.8 | F-076 | 06-EVIDENCE | OPEN_WORK | unwired services: effect-zero claim paths + undeclared http.server :8765 — both 'status: active' sin |
| 3.8 | F-077 | 06-EVIDENCE | OPEN_WORK | COMMIT-GAP: 'cap30 restart verified' documented as false vs git — gap acknowledged, never remediated |
| 3.8 | F-078 | 06-EVIDENCE | OPEN_WORK | HOURLY-PUSH GITWRITE-FAILED flag never deleted; auto-push path not green; owner decision owed |
| 3.8 | F-087 | lanes | OPEN_WORK | N-ALIVE: find_channels.py + CATALOG.json never copied to 138 timer; season5-gates-final.json unwritt |
| 3.8 | F-096 | lanes | OPEN_WORK | 182 SD-slot: 128GB card undetected after 3 tries — card-or-slot fault never dispositioned |
| 3.8 | INB-5 | 00 - Inbox | SEASON_LEFTOVER | Season sentinels: octopus-gap001-boot-probe + octopus-miniscientist-daily systemd units FAILED on .1 |
| 3.8 | SE-9 | 06-EVIDENCE (season sweep) | SEASON_LEFTOVER | GO-date contradiction (GO 09-21 vs GO-EXT2 10-07) scheduled for reconciliation, unresolved |
| 3.8 | SE-11 | 06-EVIDENCE (season sweep) | SEASON_LEFTOVER | Two cheap owner unlocks (AUTO1 phone, buy.nsw registration) named repeatedly, still pending |
| 3.6 | F-032 | 06-EVIDENCE | OPEN_WORK | FeetFinder KYC 0/9 uploads + OnlyFans cookie/API rejects — studio platforms blocked |
| 3.6 | F-054 | lanes | ABANDONED_PLAN | DEEP-SCAN-10ASPECTS sha manifest incomplete after two aborted runs (script stranded in %TEMP%) |
| 3.6 | F-063 | carried-misc | DEBT_HIDDEN | vbaa xfail invariant trio (INV-SUBSTRING, INV-CRYPTO, INV-DERIVED) unresolved in 4 copy locations |
| 3.6 | F-066 | lanes | OPEN_WORK | H9 test battery accrues to 2026-09-22 or n>=30/arm; analyzer one-shot verdict PENDING_CONTINUE; hard |
| 3.6 | F-072 | 06-EVIDENCE | OPEN_WORK | GOV_V6_ON_MAIN=NO: governance gate + ofn/agents classification never landed on main |
| 3.6 | F-075 | 06-EVIDENCE | ABANDONED_PLAN | L191 findings: business chain EDGE-1..14 undiagnosed, MODEL_RUNTIME_BLOCKED, forensic pointer active |
| 3.6 | F-089 | carried-misc | OPEN_WORK | 02-DECISIONS ledger: verified_in_code column unfilled; D-22/D-25 budget reconcile; D-32 signing open |
| 3.4 | F-037 | 06-EVIDENCE | OPEN_WORK | August incident ledger unresolved: C-042 milli-rounding starvation (fix deferred), C-043 suspected_v |
| 3.4 | F-062 | carried-misc | DEBT_HIDDEN | OFN real-publish returns RULE_NOT_IMPLEMENTED across 3 mirror copies — external publish capability e |
| 3.0 | F-055 | lanes | DOC_RUNTIME_DISCREPANCY | P6 QA seal cited but its direct file unlocatable (Q1 read-only lookup never done) |
| 3.0 | F-088 | lanes | OPEN_WORK | ESP32 labels.json absent — owner named the devices but NOW tables cannot render |
| 3.0 | ARC-3 | archive-cluster | SEASON_LEFTOVER | Season W1-FREE lane evidence archived with 'HOLD_EXTERNAL: yes. No commit.' — findings never landed  |
| 3.0 | 4D-5 | 4D-Vault | DOC_RUNTIME_DISCREPANCY | MOC-سیستم documents physical location as C:/Users/Armin/Desktop - stale; truth moved to F:/backup pe |
| 3.0 | 4D-25 | 4d_system | DOC_RUNTIME_DISCREPANCY | Channel doctor: registered 'financial_nervous' channel FAIL (layer absent from repo), 3 channels UNK |
| 3.0 | 4D-28 | 4d_system | DEBT_HIDDEN | 47 inherited nbb_cp fixture errors accepted into the 'full suite' and never fixed |
| 3.0 | INB-6 | 00 - Inbox | DOC_RUNTIME_DISCREPANCY | Duplicate Board2 status pair in Inbox pointing to two DIFFERENT canonical paths for the same note 61 |
| 3.0 | KN-1 | 07 - Knowledge | DOC_RUNTIME_DISCREPANCY | genome-system loop retired 2026-07-17, but plan.yaml still status:active and Knowledge index still p |
| 3.0 | PRJ-12 | 03 - Projects | DOC_RUNTIME_DISCREPANCY | Accounting ACC-V8 status contradiction: VERDICT_QUEUE says 'open' while STATUS-GAP-REPORT records 'a |
| 2.8 | F-081 | lanes | DOC_RUNTIME_DISCREPANCY | 8791 three-tenant contradiction unresolved (resolution: null) |
| 2.8 | F-090 | carried-misc | RULING_UNEXECUTED | three pre-registration signatures never cast (K9 three-seed REJECT, judge-bias phase2, four-arm abla |
| 2.8 | 4D-2 | 4D-Vault | SEASON_LEFTOVER | Uncommitted whitespace-only churn on 2 vault notes dated today (2026-09-15): half-finished season op |
| 2.8 | 4D-8 | 4D-Vault | DEBT_HIDDEN | Reconstruction corruption debt: 2,984 overlap trims left headers glued to math blocks (e.g. '$$## نم |
| 2.8 | 4D-15 | 4D-Vault | DEBT_HIDDEN | 97% of vault (2,975/3,055 files) is auto-generated 🔍 discovery dumps from daemon runs; curated atomi |
| 2.8 | ARC-5 | archive-cluster | DEBT_HIDDEN | worktree-rescue-2026-07-24: 1,120 md files from 3 dead worktrees (admiring-galileo, c3fix-verify, c7 |
| 2.8 | GEX-6 | _github-export | DOC_RUNTIME_DISCREPANCY | Live START-HERE names 'ofn-node @ release/p0 → docs/DISCOVERY.md' as code guide; export branch is su |
| 2.8 | INB-9 | 00 - Inbox | OPEN_WORK | Open Q-git ruling (60+241 files) plus unfinished 100-step discovery tech queue (INTENTS/UI, doctor d |
| 2.8 | INB-10 | 00 - Inbox | RULING_UNEXECUTED | Arming-order 2026-07-29: flag groups 0/4/5/8 waiting on owner AUTH; two referenced flags absent from |
| 2.8 | INB-15 | 00 - Inbox | OPEN_WORK | Morning-cards: live-rate activation explicitly deferred (موکول) and 4d shadow→live left at approve-g |
| 2.8 | OPS-17 | _ops | OPEN_WORK | CHECKLIST-100-improvements-2026-08-01: 100 of 100 boxes unchecked, 0 done, six weeks later |
| 2.8 | OPS-24 | _ops | DOC_RUNTIME_DISCREPANCY | wiring.py docstring claims heartstate beat is 'default OFF behind HEARTSTATE_SHADOW' while the live  |
| 2.8 | OPS-26 | _ops | OPEN_WORK | CAPABILITY-JOURNAL: 10+ decision-capability rows stuck at owner-vote 'pending' (COLLAB_USE_MODEL dar |
| 2.8 | OPS-27 | _ops | OPEN_WORK | BETA-ALLOWLIST trusted-operator table is an empty placeholder: rows say '(اضافه کن) pending' |
| 2.8 | PRJ-7 | 03 - Projects | OPEN_WORK | WLOS v0.1.1 (135/135 green) never had its first live run; restore drill acceptance #15 still open; c |
| 2.8 | PRJ-17 | 03 - Projects | DOC_RUNTIME_DISCREPANCY | NBB-Control-Plane v0.2 skeleton: all four integration verdicts (NBB-V1..V4) still open; rebuilt from |
| 2.6 | F-060 | 06-EVIDENCE | DOC_RUNTIME_DISCREPANCY | DeepSeek provider exists as lab stub (3× NotImplementedError) in FUGU-BIZ-SPRINT while a different l |
| 2.6 | F-079 | 06-EVIDENCE | OPEN_WORK | tunnels absent/stale + hold external (L191 forensic debug 'status: active') |
| 2.6 | F-093 | surfaces | ABANDONED_PLAN | PARALLEL-AGENTS-CONSOLIDATION 2026-07-18 checklist: merge decision, Abbas chat_id, ABN, BotFather to |
| 2.6 | SE-2 | 01 - Dashboard (season sweep) | SEASON_LEFTOVER | PB-1 24-hour continuity window cannot PASS before 2026-09-16T04:31Z — verdict still open |
| 2.6 | SE-10 | 06-EVIDENCE (season sweep) | SEASON_LEFTOVER | DEEP-SCAN-250 owner contract (100 carried + ~150 new, >=40 SEASON_LEFTOVER) exceeds executed scan qu |
| 2.6 | SE-13 | 07-HANDOFF (season sweep) | SEASON_LEFTOVER | Hero drafts produced but published:false — publication idle at class Z with no owner GO |
| 2.6 | GEX-8 | _github-export | OPEN_WORK | Human sales follow-ups exported as live next-steps (عباس follow-up→quote→booked; ملیحه 3 listings; س |
| 2.6 | OPS-16 | _ops | DOC_RUNTIME_DISCREPANCY | EXTERNAL_ACTIONS.json says EXTERNAL_ACTIONS=1 while the same-day counter records count=2 (send1+send |
| 2.6 | OPS-22 | _ops | DEBT_HIDDEN | Four parallel telegram controllers never consolidated (merge bot #1 and #7) — open since 2026-07-18 |
| 2.6 | RT-11 | runtime | ABANDONED | germline FOR-BOARD-ACTION-NEEDED.md (2026-08-17): 3 board-cp acks pending from a silent Windows agen |
| 2.6 | SML-4 | 06-RISKS | OPEN_WORK | improve-to-digest chain READY-FOR-OWNER-VOTE since 2026-08-19, no vote recorded |
| 2.6 | SML-8 | 01-TRUTH | DOC_RUNTIME_DISCREPANCY | SEASON.md on node 138 still titled SEASON 4 while gates file says Season 5 |
| 2.6 | SML-11 | PRE-0 | ABANDONED | PRE-0 Execution Board P0-P6 phases all unchecked since 2026-07-11 |
| 2.4 | F-058 | surfaces | ABANDONED_PLAN | AIE pilot failed honestly; PYMDP v2 registered, never run |
| 2.4 | F-059 | lanes | ABANDONED_PLAN | 4d_system graph builder not implemented (deferred); baselines unverified |
| 2.4 | F-061 | lanes | DEBT_HIDDEN | h1_buysw adapter never implemented (test skipped 'not yet implemented'; golden_response needs API ke |
| 2.4 | F-067 | lanes | ABANDONED_PLAN | GEN-v4 lab candidates (H8 replication, 500-gen budget) not authorized — generalization program parke |
| 2.4 | F-092 | surfaces | ABANDONED_PLAN | 08-PLANS AI-landscape research acceptance unmet (50 sources, 3 connectors) |
| 2.4 | F-094 | lanes | ABANDONED_PLAN | N3V2-MATH: 30 formula rows untested, 9 quarantines, SIG_IV PENDING |
