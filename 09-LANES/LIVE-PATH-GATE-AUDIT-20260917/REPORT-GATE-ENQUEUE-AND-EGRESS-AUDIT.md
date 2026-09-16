---
type: report
status: active
tags: [octopus, audit, gate-enqueue, egress, halt-oracle, read-only, od-1]
updated: 2026-09-17
project: "[[OCTOPUS]]"
---

# REPORT — LIVE-PATH GATE AUDIT: `_gate_enqueue` callers + egress coverage

`GOV_VERSION=V8 · LADDER=L2 · mode: READ-ONLY AUDIT · date: 2026-09-17`
`no patch · no deploy · no live-node contact · no HALT file created/deleted/armed`
`scope: P1 (_gate_enqueue callers) + P2 (egress/harvester gate coverage), per owner directive`

**Method note.** Two read-only exploration passes traced the code; I then
independently re-ran the load-bearing checks myself (the halt-oracle consumer list,
the `approved_manual` setter, the telegram kill-source, and the `remote_brain`
egress path). Where a claim rests only on a pass I did not re-run, it is marked
`[delegated]`. Nothing in this report was executed against a node.

---

## 0. Correction to my own earlier finding (read this first)

In `plans/OCTOPUS-SAFETY-MAP-v1.md` I rated **D-1 (`_gate_enqueue` bypasses the
policy gate)** as MEDIUM–HIGH and wrote that it "rests on an assumption." **That
severity was wrong, and the audit refutes it.** Recorded here rather than quietly
edited, per the rule that lowering a grade is a successful outcome.

What is actually true:

- All four production callers pass `RiskTier.RED`.
- `approved_manual` has **exactly one production setter** — `Node.owner_decide` →
  `outbox.approve_manual` (`node.py:3370`). Verified by myself. (`node.py:2789` is a
  *read* that lists approved items, not a setter.)
- The owner route is `_owner_route`, requiring owner host + owner session + allowlist
  (`http_api.py:1207-1208`, `:639-646`, `:611-616`).
- **Nothing consumes `pending` outbox items automatically.** `outbox.claim()` is
  wrapped by `RunGate.claim` (`run_gate.py:60-66`) — and `RunGate` has no production
  consumer. Boot does `recover_stale(resend=False)`, which parks in-flight items to
  `HELD` (`adapters/boot.py:297`).

So the docstring's claim — "these paths are all RED and already require human
approval downstream" — is **correct for this repo's code**. D-1 is a gap in the
*capability to prove* safety, not evidence of an active defect. The owner's own
reading ("این یک شکاف در قابلیت اثبات امنیت است، نه الزاماً اثبات یک آسیب فعال")
was right and mine was overstated.

**The real structural safety property is stronger than the policy gate: there is no
automated external sender at all.** Every real dispatch requires a human owner
action. That, not `admit()`, is what the evidence supports.

---

## A. Reachable callers of `_gate_enqueue`

Definition `ofn/node.py:3036`; body = kill-switch check (`:3051`) then
`outbox.enqueue` (`:3054`). Exactly **four production call sites**, all in
`ofn/node.py`, all passing `RiskTier.RED`, all reachable from a live HTTP route:

| # | Caller | Gate call | Kind | Live entrypoint | Pre-gate checks at enqueue |
|---|---|---|---|---|---|
| 1 | `publish_draft` `:739` | `:773-778` | `PUBLISH_POST` | `POST /api/v1/studio/drafts/{id}/publish` (`http_api.py:981-998`) | consent `may_publish` (`:754-757`), media presence (`:768`) |
| 2 | `send_to_outbox` `:1344` | `:1419-1421` | `studio:publish` | `POST …/send-to-outbox` (`http_api.py:863-874`) | sensitivity fail-closed (`:1371-1379`), screening (`:1393-1397`), per-platform consent (`:1404-1409`) |
| 3 | `send_lead_reply` `:4012` | `:4063-4064` | `lead:reply` | `POST /api/v1/painting/leads/{id}/reply` (`http_api.py:928-952`) | channel allowlist note/sms/email (`:4022-4024`); **no consent at enqueue** |
| 4 | `send_lead_quote` `:4080` | `:4114-4115` | `lead:quote` | `POST /api/v1/painting/leads/{id}/quote` (`http_api.py:953-956`) | amount sanity (`:4092-4099`); **no consent at enqueue** |

Test call sites: none call it directly; `tests/test_gate_enforcement.py` exercises the
callers indirectly. A fifth `outbox.enqueue` exists at `node.py:2272` inside
`propose()` — that is the `admit` path, not a bypass of it.

---

## B. Paths with PROVEN approval (exits from `approved_manual`)

Two exits exist, both owner-route, both requiring the `approved_manual` precondition:

**B1 — `owner_outbox_complete`** (`node.py:3416`; `POST /api/v1/owner/outbox/{id}/complete`).
Records that a **human delivered the item outside the machine**. No machine dispatch.
Requires status `approved_manual` (`:3432-3434`), kill check (`:3436-3438`), RED
double confirm (`:3439-3441`). **WIRED.**

**B2 — `publish_to_telegram`** (`node.py:3513`; via `owner_publish_telegram` `:3991`;
`POST /api/v1/owner/outbox/{id}/publish-telegram`, `dry_run` defaults True). The only
machine dispatch in the system. Requires `approved_manual` (`:3536-3540`) then
`require_release_context` (`:3615` → `kernel/release_switch.py:122`). **WIRED.**

### The release-gate context, link by link (all read by me)

| Link | `path:line` | Verdict |
|---|---|---|
| kill switch in `_gate_enqueue` | `node.py:3051` | **WIRED** |
| outbox idempotency composite PK | `outbox.py:236-250` | **WIRED** |
| owner-only approval (sole setter) | `node.py:3370` + `http_api.py:1207,611-653` | **WIRED** |
| RED double-confirm at approval | `gates.py:104-107` via `node.py:3361` | **WIRED** (caveat §F.3) |
| `approved_manual` precondition at both exits | `node.py:3432`, `:3537`; SQL guards `outbox.py:305,357` | **WIRED** |
| kill re-check at completion and in release ctx | `node.py:3436`; `:3607` → `release_switch.py:82` | **WIRED** |
| release switch 11-gate verdict | `release_switch.py:79-119` at `node.py:3615` | **WIRED** |
| consent (studio paths) | `kernel/consent.py:199`; `node.py:754-757,1404-1409,3567-3570` | **WIRED** |
| consent (lead reply/quote enqueue) | `node.py:4006-4008` | **DOC_ONLY** — the comment claims it goes through the owner-approval gate like a studio publish; approval yes, consent check **absent** |
| platform matrix screen | `node.py:3574-3582` | **WIRED** (telegram path) |
| `CallBudget` REMOTE allows/record | `run.py:580`; `node.py:3588-3589,3643-3646` | **WIRED** |
| `Ledger.verify` hash chain before send | `ledger.py:159-183` at `node.py:3597-3599` | **WIRED** (telegram only) |
| telegram adapter real send | `telegram_channel.py:58-65` | **WIRED**, single caller `node.py:3637` |

**Answer to the audit's central question:** for none of the four callers could a code
path be constructed from caller to real external dispatch that skips a human owner
action. For the studio paths the human both approves and triggers the double-confirmed
publish; for the lead paths **the machine cannot dispatch at all** —
`publish_to_telegram` refuses items without a `caption` (`node.py:3541-3544`), which
every lead payload lacks (`:4056-4062`, `:4107-4113`). Lead items' only exit is the
manual-delivery receipt.

---

## C. Paths with UNPROVEN or ABSENT approval

| Path | Finding | Verdict |
|---|---|---|
| **`D27_DAILY_SEND_CAP` / `D27_DAILY_SPEND_CAP_AUD`** (`config.py:32-33`) | **No enforcement code reads them.** The only consumer is `agents/doctor.py:426-430` (diagnostics). `docs/runbooks/FLAG-CLAIMS.json` labels them "load-bearing" — the registry overstates the code. The actually-enforced lead cap is a *different* constant (`outbound_worker.py:52-58`). | **DOC_ONLY** |
| **Lane G SMTP arc** (`lead_outbound_transport.py:136,145`; `release_pipeline.py:329-334`; `owner_approvals.py:92-177`) | The most dangerous egress in the repo, fully and correctly guarded (halt → wire flag → conservation → daily cap → consent → atomic effect settle → suppression). **But no live entrypoint calls it.** Only tests drive `release_pipeline`. The two-step `approval_id:code` design exists only here — i.e. the *strongest* approval mechanism is on the *unreachable* path. | **TESTED_ONLY** |
| **`RunGate` / `outbox.claim`** automated-sender wrapper | No production consumer. This is *why* nothing auto-sends. | **TESTED_ONLY** |
| **`GATE_OPEN_UNTIL_UTC = "2026-09-16"` auto re-close** (`config.py:26,248-254`) | WIRED in code; after the window the gates re-close unless `OFN_KEEP_GATES_OPEN=1`, which would make `publish_to_telegram` refuse. Deployed value unknowable from the repo. | code **WIRED**, live effect **UNVERIFIED** |
| **Deployed env values** (`OFN_KEEP_GATES_OPEN`, `OFN_EXTRA_CLOSED_GATES`, telegram token, model keys, `OFN_ALERT_TELEGRAM`) | Live in `node.env`/`secrets.env` on the board. `FLAG-CLAIMS.json` values are dated 2026-09-02/03 — two weeks stale. | **UNVERIFIED** |
| **Out-of-repo `octopus-*` units** | The deployed board reportedly runs 7 units not present in this repo. If one invokes `release_pipeline`, the `owner_approvals` two-code gate would apply (real code, live-ness unverified). | **UNVERIFIED** |

---

## D. Real HALT oracles, their consumers, and the coverage gap

### D.1 The complete consumer list (I re-ran this myself)

`master_halted()` — `opslib.py:28` = `HALT_SURVIVAL_LOOP=1` **or** `~/ofn/HALT-ALL`
(`opslib.py:20`), fail-closed — is consulted by **exactly five production modules**:

| Consumer | `path:line` |
|---|---|
| `capability_token.py:87` | re-check in `request_send_token` |
| `followup_worker.py:38` | + campaign flag |
| `outbound_worker.py:214,451` | the SMTP arc's first guard |
| `quote_pipeline.py:79` | + campaign flag |
| `release_pipeline.py:106,184` | the Lane G pipeline |

That is the whole list. Every other HALT convention:
`ofn/adapters/run_gate.py:35` takes a **caller-supplied path** (no production
constructor); `node.py` telegram publish uses the **in-process** `self.killed`
(`node.py:3760`/`:3770`), which **resets on process restart**; the rest use none.

### D.2 ⚠ D-9 — egress that fires with NO halt-file check (new finding)

Arming `~/ofn/HALT-ALL` does **not** stop the following. Verified from the code:

| # | Egress | `path:line` | Live trigger | What stops it instead |
|---|---|---|---|---|
| 1 | **Telegram publish (real send)** | `platforms/telegram_channel.py:65` | owner panel → `node.py:3615-3637`, inside the live `ofn.service` | **only** the in-process `self.killed` (resets on restart) + owner two-step + release gate. **`HALT-ALL` is never read on this path** (I read `node.py:3600-3616` directly: `kill_switch_active=self.killed`). |
| 2 | **Hosted-model spend** | `adapters/remote_brain.py:88` | `ofn.service` → worker thread (`run.py:587,626`) → `router.ask` | key presence, tenant quota, CallBudget. `kernel/callbudget.py:28` says so itself: **"HALT is not a parameter. Layer 3 stops STARTS"**; `:80` — "HALT is not consulted — this is not a start gate." |
| 3 | **Owner notifications** | `agents/owner_notify.py:62` | `octopus-heartbeat.timer` (hourly), `octopus-digest.timer` (21:00), imap alerts | token/chat-id presence only |
| 4 | **IMAP poll** | `agents/imap_listener.py:297` | `octopus-imap.timer` every 15 min | credentials only. **No halt, no wire flag.** |
| 5 | **`git pull origin main`** | `deploy/systemd/ofn-sync.service` ExecStart | `ofn-sync.timer` | no in-repo guard at all |
| 6 | **Shopify OAuth token exchange** | `adapters/shopify_oauth.py:225` | unauthenticated inbound route `http_api.py:412` | HMAC state + shop allowlist |
| 7 | **Crash alert** | `adapters/alert.py:77` | `ofn-alert.service` (OnFailure) | `OFN_ALERT_TELEGRAM=1` — deliberately unhalted (it must fire when the node is dead) |

**Why this matters more than the path fragmentation.** D-3 (fragmented paths) is about
*mis-spelling* the switch. D-9 is about *coverage*: even with the right file armed,
the highest-consequence egress — a real Telegram publish and paid model spend — keeps
running. The strongest mitigation today is not the halt file; it is the **absence of
any automated sender** (§0). That is a design property, not a control, and it would
evaporate the moment someone wires `RunGate` or `release_pipeline` to a timer.

**Mitigating context (`INFERRED`, not a gate):** items 3–7 are read/notify/pull
paths, not third-party sends. Item 1 is the one that matters.

Also verified: `install_systemd.sh:19` pre-sets `OCTOPUS_WIRE_LEAD_OUTBOUND=1` in the
environment of every `octopus-*` service — so the one wire flag several senders consult
is already "1" the moment the installer runs.

### D.3 Harvester / egress module verdicts (P2, `[delegated]`)

All seven fetchers — `h1_harvest.py:66`, `h3_strata.py:191`, `seek_harvest.py:46`,
`nsw_ocp_harvest.py:59`, `demand_harvest.py:101`, `source_registry.py:322`, and
`ziman_tender_harvest.py:119` (Selenium) — have **NO_ENTRYPOINT_FOUND**: no systemd
unit, script, or dynamic import reaches them. Several are labelled DEAD SOURCE in-file.
`ziman_tender_harvest` and `trend_sources` have *real* gates
(`owner_approval=True` + `OFN_WIRE_HARVEST=='1'`, `:64-75`; `sends_saba_data` refusal,
`trend_sources.py:113-114`) but the gates sit on dead paths.

Verdicts: harvesters **TESTED_ONLY**; `shopify.py`, `onlyfans.py` (triple-lock),
`bluesky.py`, `email_ses.py` **TESTED_ONLY / DOC_ONLY**; `external_witness`,
`owner_absence`, `brainport`, `glass_runner` **TESTED_ONLY**.
The previously-`UNVERIFIED` P-6 in the safety map is now **TESTED_ONLY** — i.e. real
egress code, no live trigger. That closes the one `UNVERIFIED` gap the first report left.

---

## E. Exact proposal for OD-1 (no patch applied)

The owner chose **Option B**. Based on §D, one amendment is needed, because the
owner's clause 4 asks the doctor to report "the exact halt path each process really
resolves" — and §D.2 shows that for the two highest-consequence egresses the answer is
**"none."**

**E.1 — Canonical oracle (decided, NOT executed).** Declare `~/ofn/HALT-ALL` the
single canonical oracle (it already is, in `opslib.py:20` and `opslib.py:6`'s own
words: «نه kill-فایل‌های دیگر»), and correct every document, runbook, agent prompt,
and tool that names a different path — including `AGENTS.md` GOV-V7's
`F:\ofn-node\HALT`, which does not exist.

**E.2 — No silent compatibility path.** `ops/ign1_telegram_ignite.py:28`'s
`<root>/HALT` becomes either a mechanically-proven alias to the canonical oracle or a
DEPRECATED path whose presence produces a loud warning + receipt.

**E.3 — The doctor must report COVERAGE, not only RESOLUTION.** This is the amendment.
Per service it must emit the owner's clause-4 fields (identity, commit, resolved path,
file state, predicate state, legacy files, mismatches, verdict) **and** a coverage row:
*does this consumer consult the canonical oracle at all?* Consumers in §D.2 must
surface as `UNVERIFIED` coverage with a named severity, not as an absent row. Without
this, the doctor would certify a system whose halt coverage is partial.

**E.4 — Build split (respects clause 6).**
- **Laptop-side, offline, buildable now (no authorization needed beyond read-only):**
  enumerate every halt-reading site, compute the path each module resolves for a
  declared `HOME`, and diff that against the documented path. Fully static.
- **On-node, requires a separate authorized plan:** file state
  (absent/present/malformed/unreadable/symlink), per-service predicate state, and
  legacy-file discovery. **There must be no create/delete/arm**, per clause 6.

**E.5 — Fail-loud.** Append-only JSONL receipt per mismatch with severity, exact
reason, paths involved, and `owner_action_required` set when a runtime or governance
change would be needed.

**No patch is applied by this lane. This section is a proposal only.**

---

## F. Limits and honesty

1. **`[delegated]` items** — §D.3 (harvester verdicts) and the §B link table come from
   exploration passes; I re-ran §0, §D.1, §D.2 and the release-context read myself.
2. **Deployed environment is unknowable from here.** No secrets file was read (none is
   committed). Several `WIRED` paths are "wired if env". Marked, not assumed.
3. **The "double confirmation" is weaker than the docstrings imply.** At both owner
   routes the second confirmation is a boolean in the **same HTTP body** as the
   action (`http_api.py:1452-1459`, `:1508`). The genuinely separate human steps are
   two distinct routes plus host/session separation — not two independent codes. The
   strict two-code design exists only in the unreachable `release_pipeline` path.
   **Reported, not dramatized: it is not a bypass, but the "two-step" rhetoric
   overstates the Node layer.**
4. **A stale docstring, same family as D-3:** `release_switch.py:122` says "No sender
   exists yet, and none may be built without Ari's approval" — while
   `publish_to_telegram` (`node.py:3615`) is a live caller of it. Another
   document-vs-runtime divergence.
5. `ofn/node.py` (~4,300 lines) and `http_api.py` (~1,900) were read at every
   egress-relevant segment, not line-by-line in full.
6. Two deploy units (`ofn-digest`, `ofn-sync`) still carry "ASSUMPTION — verify before
   deploy" comments naming user `dietpi`/`~/ofn` while the others use `ari` —
   deployment consistency **UNVERIFIED**.

---

## G. Effect on the safety map

| Item | Before | After |
|---|---|---|
| **D-1** `_gate_enqueue` bypass | MEDIUM–HIGH, "rests on an assumption" | **DOWNGRADED** — no bypass exists; the downstream-approval claim is correct. Remaining risk is to *reasoning*, not to safety. Evidence-to-prove gap. |
| **P-6** harvesters | **UNVERIFIED** | **TESTED_ONLY** — real egress code, no live entry point |
| **D-9** halt coverage | (not listed) | **NEW, severity HIGH** — real Telegram publish and paid model spend continue with `HALT-ALL` armed; `callbudget.py` disclaims HALT by design |
| **P-2** telegram publish | SOLID | SOLID, with the caveat that its stop is the **in-process** flag, not the documented file |
| **D-2/D-3/D-4/D-6/D-7** | unchanged | unchanged |
| New: `D27_*` caps | (scored as control) | **DOC_ONLY** — no enforcement reads them; the registry overstates the code |

**No patch, no deploy, no live-node contact, no HALT file touched.**
