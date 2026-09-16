---
type: architecture
status: active
tags: [octopus, safety-map, damage-points, scorecard, tcb, surgical-boundary]
updated: 2026-09-16
project: "[[OCTOPUS]]"
---

# OCTOPUS — SAFETY MAP v1

`GOV_VERSION=V8 · LADDER=L2 · mode: READ-ONLY REVIEW · date: 2026-09-16`
`scope: F:\ofn-node (live runtime code) + F:\backup (governance vault)`
`status: REVIEW ARTIFACT — not an authorization, not a Gate-0 claim`

**Purpose:** a formal map of where the organism's controls actually sit, which
pathways can exceed their intended boundary, and how much protection each
decision-making pathway really has. Plus an explicit **surgical boundary** stating
what a future agent may and may not touch.

**How to read the scores.** The per-pathway scores in §4 are **review judgments
derived from cited lines**, not measurements. They are reproducible by re-reading
the cited code; they are not statistically estimated and carry no interval. A high
score means "the cited control is on the cited path", nothing more — it is not a
penetration test.

**Relation to existing maps.** `F:\backup\LIVE-ORGANISM-MAP.json` (2026-08-19) is a
frozen snapshot of runtime *state* (organs, identity health, backup verdict).
`CONSTITUTIONAL-ZONES.yaml` classifies *files* into change-forbidden zones. This map
is neither: it maps **pathways to controls**, and it adds the one axis both are
missing — whether the control is actually consulted on the live path.

---

## 1. The core safety constraint

Everything is scored against four clauses. They are deliberately narrow so that
"compliant" cannot be claimed by being generally well-engineered.

| Clause | Statement |
|---|---|
| **SC-1 — Receipt** | Every effect crossing the node boundary has a same-domain, hash-chained receipt **before** it is counted as done. |
| **SC-2 — Stop** | Every pathway that can produce such an effect has a stop that **bites on that pathway** — not on a neighbouring one, and not documented-but-unread. |
| **SC-3 — Bound** | The effect stays inside the declared envelope (budget, contact caps, allowlist, per-person consent). |
| **SC-4 — Reversible or refused** | Irreversible effects require two-step owner confirmation; otherwise they are refused. |

**Scoring:** PASS = 2 · PARTIAL = 1 · FAIL = 0 · UNVERIFIED = 1 (conservative —
unknown counts as partial credit, never as pass). Maximum 8.

| Total | Label | Meaning |
|---|---|---|
| 8 | **SOLID** | all four clauses hold on the live path |
| 5–7 | **PARTIAL** | some clause rests on an assumption or a neighbouring control |
| 2–4 | **THIN** | a clause is effectively absent |
| 0–1 | **ABSENT** | the pathway is unguarded as built |

---

## 2. Structure audit — where the controls physically live

### 2.1 Zones (from `CONSTITUTIONAL-ZONES.yaml`, unchanged)

| Zone | Content | Change rule |
|---|---|---|
| **B0** | 15 TCB files, signing keys, hard stops + HALT-ALL, append-only history, propose-only boundary, authority & budget caps, witness state, recovery, data ownership, FX pin | change forbidden without owner |
| **B1** | memory schema, heartbeat, model routing, quorum/receipt templates, doctor+judges, novelty thresholds | bounded change |
| **B2** | workers, connectors, parsers, UI, research tools, caches, **measurement harnesses** | free |
| **unresolved** | MCP CONSTITUTION zone; ACTIVATION schema-vs-value; whether OCTOPUS-PRIME artifacts bind to B0; sandbox classification | unknown class = **change forbidden** |

The proposed probe harness is a **B2 measurement harness** — the freest zone, and
the correct home for it.

> Note the `unresolved` row: **the sandbox itself is unclassified**. That is one
> reason the plan does not depend on the existing sandbox (§4, P-12).

### 2.2 Structural observation

Controls are **not concentrated**. They are scattered across `ofn/kernel/` (pure
predicates), `ofn/adapters/` (I/O), `ofn/agents/` (behaviour), `data/*.json`
(registries), and `F:\backup\.cursor\hooks/` (editor-time). Three consequences:

1. **No single file answers "is this action allowed".** There is no one place to
   audit, which is precisely why a pathway→control map is needed.
2. **Control *vocabulary* is duplicated** — the same guarantee is restated in
   several modules (`grants_send()` in both `adapters/receipt.py` and
   `kernel/hash_chain.py`; `canonical()` in two incompatible forms).
3. **Editor-time hooks share the name-space of runtime controls.** `.cursor/hooks/`
   sits in the vault beside governance documents, and reads like runtime policy. It
   is not (see D-2).

---

## 3. Damage points

A **damage point** is a place where the assumed bound is thinner than it reads.
Ordered by consequence.

### D-3 — Kill-switch path fragmentation *(severity: HIGH — silent failure)*

Three conventions coexist, and the one named in governance does not exist:

| Convention | Defined at | Status |
|---|---|---|
| `~/ofn/HALT-ALL` | `ofn/budget/opslib.py:20` — self-declared «تک‌oracle» | read by the survival loop |
| `<root>/HALT` | `ops/ign1_telegram_ignite.py:28` (`HALT = ROOT / "HALT"`) | read by the one-shot ignition only |
| caller-supplied path | `ofn/adapters/run_gate.py:35` (`self._halt_path`), `ofn/adapters/halt_log.py:228` | **no production constructor found** |
| **`F:\ofn-node\HALT`** | named in `F:\backup\AGENTS.md` GOV-V7 (four safeguards) | **file does not exist; read by no code path found** |

`ofn/kernel/halt.py:26` defines **absent = RUNNING**. Therefore arming the
documented file produces **silence, not a stop**. The predicate itself is
excellent — fail-closed on symlink, unreadable, non-UTF-8, and unparsable content
(`ofn/adapters/halt_flag.py:24-50`). The defect is entirely in **which path is
read**, and it is invisible precisely because absence is legal.

**Mitigation:** OD-1 (owner-gated). Cheapest honest fix is a doctor probe that
reports which halt files exist and which one each consumer reads — making a
mismatch loud. Not attempted in this lane.

### D-1 — `_gate_enqueue` bypasses the policy gate *(severity: MEDIUM–HIGH)*

`ofn/node.py:3036`. Its docstring is candid:

> "This does NOT re-run admit/risk/quota — these paths are all RED and already
> require human approval downstream. The gate here is specifically the kill
> switch."

The control is real but it is a **single** check, and its sufficiency rests on an
*assumption about other code* ("already require human approval downstream"). That
assumption is exactly the kind that D-3 shows can be wrong while everything still
reads as covered. Call sites include `publish_draft` (`node.py:773`) and studio
variant publish (`node.py:1419`).

**Mitigation:** read-only review of every `_gate_enqueue` call site to confirm each
is genuinely RED with a real downstream two-step. **REVIEW_ONLY** — never probe live.

### D-2 — Editor-time hooks are not runtime controls *(severity: MEDIUM)*

`.cursor/hooks/` holds `deny_egress.py`, `deny_secret_read.py`, `deny_destructive.py`,
`guard_flags.py` (plus `_common.py`, `allow_mcp.py`, `audit.py`, `lane_report_check.py`,
`session_init.py`). They bind an **editor session**. A bare shell, a
`python -c`, a `git` invocation, or a systemd unit is not covered.

**Mitigation:** label them explicitly as editor-time in any architecture doc, and
never cite a hook as evidence of a runtime bound. Runtime bounds are the ones in §4.

### D-4 — Simulated receipts look like real ones *(severity: MEDIUM)*

`ofn/adapters/fake_executor.py` writes `execution_receipts.jsonl` shaped like the
real thing. Harmless while it stays in tests; dangerous the moment a simulated
receipt is cited as evidence of a real effect.

**Mitigation:** every simulated artifact carries `mode: SIMULATED` and
`superiority_claim: null` — the convention already used by
`octopus_observation/fixture_run.py`. Adopted by the probe harness.

### D-5 — The hard sandbox is not verified *(severity: HIGH if relied upon)*

`F:\backup\LAB-DOCTOR-CONTRACT.yaml`: all 10 hard-sandbox requirements are
`UNKNOWN_NOT_VERIFIED`; `verdict: NOT_A_VERIFIED_HARD_SANDBOX`; `gate_3` blocked.

**Mitigation:** do not depend on it. A harness with **no** escape surface is safer
than one whose jail is asserted but untested. See P-12.

### D-6 — Two incompatible `canonical()` rules *(severity: MEDIUM)*

| Rule | Where | Separators |
|---|---|---|
| `json.dumps(sort_keys=True, separators=(",",":"), ensure_ascii=False)` | `ofn/adapters/ledger.py:52` | **compact** |
| `json.dumps(sort_keys=True, ensure_ascii=False)` | `ofn/octopus_observation/fixture_run.py:68` | **default** (`", "` / `": "`) |

Both are called canonical. A hash computed under one rule will not match the other,
and a comparison across artifacts can therefore pass or fail for the wrong reason —
while the ledger's whole guarantee is byte-identical reproducibility.

**Mitigation:** one pinned rule per artifact, asserted by a frozen digest vector (L7).

### D-7 — The wire flag is baked ON by the installer *(severity: LOW–MEDIUM)*

`F:\ofn-node\tools\install_systemd.sh:19` — `Environment=OCTOPUS_WIRE_LEAD_OUTBOUND=1`
in every agent unit. Combined with `OFN_WIRE_OUTBOUND` having been deleted
2026-09-03 as *decorative* (`ofn/config.py:31`), reading the flag as a safety
boundary is wrong in the deployed configuration. The real boundary is consent +
effect gate + caps.

**Mitigation:** treat flags as wiring switches, not safety switches, in all
documentation.

### D-8 — The instrument becomes the escape *(severity: depends entirely on design)*

Any "just a test script" that imports the live package or opens a socket is a new
egress path with no governance trail. This is the failure mode the surgical protocol
(§6) exists to prevent.

---

## 4. Risk-mitigation scorecard

Every decision-making pathway, scored against SC-1..SC-4. **REVIEW SCORES, not
measurements** (§0).

| # | Pathway | Entry → effect | Claimed control | Actual control on the live path | SC-1 | SC-2 | SC-3 | SC-4 | Total | Label | Max damage if the assumption is wrong |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **P-1** | Partner draft → publish queue | `http_api.py:387` → `node.py:773` | policy gate | `_gate_enqueue` (kill switch only) | PASS | PARTIAL | PARTIAL | PASS | **6** | PARTIAL | A publish queued without policy evaluation; caught only at the later release gate |
| **P-2** | Telegram publish (real send) | outbox → `node.py:3513` → `telegram_channel.py:37` | release gate + consent | `release_switch.py:122` (11 fail-closed checks), consent, platform matrix, ledger-verify `node.py:3597`, call budget; exit only via `approved_manual` | PASS | PASS | PASS | PASS | **8** | **SOLID** | — (the strongest path in the system) |
| **P-3** | Lead outbound email | `agents/lead_outbound_transport.py` | effect gate + consent | `lead_effect_gate.release_and_settle` (atomic on effect_id), suppression table | PASS | PARTIAL | PASS | PARTIAL | **5** | PARTIAL | Duplicate or non-consented send if the effect_id gate is bypassed |
| **P-4** | Owner brain-ask → model | `node.py:356` → `worker.py:189` → `router.py:130` | quota + call budget | `kernel/quota.py:246`, `kernel/callbudget.py:117` | PASS | PARTIAL | PASS | PASS | **6** | PARTIAL | Unbudgeted paid model call; no external effect beyond spend |
| **P-5** | Webhook inbound | `node.py:3058` | HMAC verify | `webhook_verify.py`, replay guard `kernel/auth.py:343`, inbound rate limit | PASS | PASS | PASS | PASS | **8** | **SOLID** | — |
| **P-6** | Harvester / research egress | `agents/h1_*.py`, `web_lookup`, `agents/external_witness.py:114` | *not audited in this lane* | unknown | UNVER | UNVER | UNVER | UNVER | **4** | **THIN** | Network egress with unknown gating. **Flagged, not cleared.** |
| **P-7** | Kernel propose path | `node.py:2254` → `gates.py:29` | full policy gate | **NO PRODUCTION CALLER** — reachable only from tests | PASS | FAIL | PASS | PASS | **6**† | **ABSENT (dormant)** | Anyone reasoning "the policy gate covers every action" is wrong. Nothing sends via this path, so present damage is zero — the damage is to *reasoning*. |
| **P-8** | Scheduler start gating | `run_gate.py:25` `RunGate` | stop happens BEFORE run creation | **constructed only in tests** | PASS | FAIL | PASS | PASS | **6**† | **ABSENT (dormant)** | Restart-resend protection not actually positioned at the scheduler |
| **P-9** | Survival loop | `octopus_survival/loop.py:96` | halt check + A0..A7 ladder + caps | halt check via `opslib` `HALT-ALL`; preregistration fields mandatory | PASS | PASS | PASS | PASS | **8** | **SOLID** | — (but see D-3: only the `HALT-ALL` file is read) |
| **P-10** | Dev-time agent (editor) | `.cursor/hooks/` | deny-egress / deny-secret / deny-destructive | editor process only; not a runtime bound | UNVER | FAIL | UNVER | UNVER | **3** | **THIN** | Any non-editor invocation is uncovered while the hooks suggest coverage |
| **P-11** | Money movement | *none* | — | **no payment executor exists in the repo** | n/a | PASS | PASS | n/a | **4**† | n/a | No escape surface exists yet; L2 gate is unbuilt, so this is "no capability", not "safe capability" |
| **P-12** | **Probe harness v0 (proposed)** | new, offline | by construction | stdlib-only; no socket, no subprocess, no live import, writes only in `receipts/`; self-certified fail-closed | PASS | PASS | PASS | PASS | **8** | **SOLID (by construction)** | The instrument becomes the escape (D-8) |

† P-7, P-8, P-11 score 6/4 only because the dormant clauses are scored PASS for
constraints that are *structurally* satisfied by the code — but the pathway itself
is **ABSENT**. The total is deliberately not allowed to hide that: the **Label**
column carries the real verdict. A scoring scheme that let "dormant" read as
"PARTIAL" would be the exact disease this map exists to name.

### 4.1 Reading the scorecard

- **Two pathways are genuinely SOLID and load-bearing:** P-2 (the real send) and
  P-5 (inbound). The publish path is better defended than the architecture's own
  reputation suggests — eleven fail-closed checks, consent, platform matrix, ledger
  verification, and a manual-only exit.
- **Two pathways are ABSENT while reading as present:** P-7 and P-8. This is the
  central finding.
- **One pathway is THIN and un-cleared:** P-6, harvesters. Marked UNVERIFIED — not
  "probably fine".
- **The thinnest real pathway is P-10**, where the gap between the hooks' apparent
  coverage and their actual scope is largest.
- **Distribution:** 4 SOLID-adjacent, 4 PARTIAL, 3 THIN/ABSENT. The system is not
  badly built; it is **unevenly** built, and the unevenness is invisible from any
  single file.

---

## 5. Surgical boundary — what a future agent may touch

This is the operative output of the map. An agent's lane is bounded by **effect
class**, not by directory.

### 5.1 OPEN — proceed without a vote (GOV-FREEDOM-V2 §2)

- Reading anything, in either tree.
- Adding a **new** file or directory in `F:\backup` (vault) or a new offline
  package under `F:\backup\_ops\` — **B2 zone**.
- Writing tests, fixtures, receipts, reports, lane reports, plans.
- Local commits on a lane branch.
- Running an offline, stdlib-only instrument that touches no live surface.

### 5.2 REQUIRES OWNER — stop and raise a card

- Anything in zone **B0** or **unresolved** (`CONSTITUTIONAL-ZONES.yaml`) — unknown
  class means change forbidden.
- Any edit to: `ofn/kernel/**`, `ofn/adapters/**`, `ofn/agents/**`, `ofn/node.py`,
  `ofn/run.py`, `ofn/budget/**` (all P-1..P-9 control code).
- `data/gates.json`, `BUDGET.json`, any `HALT*`, any `OCTOPUS_WIRE_*` / `OFN_WIRE_*`
  flag — **in either direction**.
- `AGENTS.md`, the GOV documents, `CONSTITUTIONAL-ZONES.yaml` — governance text.
- Any deploy to a live node (Class B → witness required).
- Anything on the RED-1..RED-4 list (secrets/identity, TCB & authority,
  irreversible destruction, out-of-envelope external effect).

### 5.3 NEVER — regardless of who asks

- Import the live package into an offline instrument (R-2). This is the single most
  likely way this lane's work goes wrong.
- Live-ablate a safety surface to see what bites. That is an incident, not an experiment.
- Cite a simulated receipt as evidence of a real effect.
- Declare PASS / LIVE without a same-domain receipt (GOV-V7 prohibition 3).

### 5.4 The three questions before any action

1. **Which pathway am I on** (§4), and does the control I am relying on appear in
   its `Actual control` column — or only in `Claimed control`?
2. **If this goes wrong, what bites** — and has that specific stop been verified on
   *this* pathway?
3. **If I am wrong about "this is covered", how would I find out?** If the answer is
   "silently" (as in D-3), stop and raise a card instead.

---

## 6. Maintenance

- This map is dated **2026-09-16**. It is a review artifact, not a live monitor.
- Re-verify §2.3's structural claims (P-7, P-8) after any change to `ofn/node.py`
  or `ofn/kernel/gates.py` — they are single greps.
- Additions belong here **additively**; do not rewrite prior findings.
- The two genuinely SOLID pathways (P-2, P-5) should be re-checked if
  `release_switch.py`, `consent_gate.py`, or `webhook_verify.py` change.
- P-6 (harvesters) remains **UNVERIFIED** and is the highest-value next read — a
  read-only review, no experiment.

---

## خلاصه برای مالک

نقشهٔ ایمنی ساخته شد. هر «مسیر تصمیم» جداگانه بررسی شد و چهار معیار گرفت:

۱. **رسید** — آیا اثر ثبت می‌شود؟ ۲. **ترمز** — آیا روی *همان* مسیر ترمز واقعی هست؟
۳. **محدوده** — آیا داخل بودجه و اجازه می‌ماند؟ ۴. **برگشت‌پذیری** — اثر برگشت‌ناپذیر
دو-مرحله‌ای تأیید می‌شود؟

**نتیجه:** دو مسیر واقعاً محکم است — ارسال تلگرام و ورودی وب‌هوک (هشت از هشت).
چهار مسیر متوسط، و سه مسیر نازک یا خالی. سیستم بد ساخته نشده؛ **ناهمگن** ساخته
شده و این ناهمگنی از داخل هیچ فایل تنها دیده نمی‌شود.

دو مسیر در سندها محافظت‌شده به‌نظر می‌رسند ولی در واقع خالی‌اند (مسیر PolicyGate و
ترمز زمان‌بند). یک مسیر هنوز بررسی نشده — جمع‌آوری‌کننده‌های وب — و من آن را
«مشکوک» گذاشتم، نه «سالم».

در پایان یک «مرز جراحی» آمد: چه چیزی را ایجنت می‌تواند بدون اجازه انجام دهد، چه
چیزی فقط با اجازهٔ شما، و چه چیزی هرگز.
