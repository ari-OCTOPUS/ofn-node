# Second Brain Super-Governor — Phased Build Plan (v0.2)

> **Status: PLAN ONLY. Nothing here is built yet.** Each phase starts only on the
> owner's explicit GO. Governed by [`SELF_IMPROVEMENT_DOCTRINE.md`](SELF_IMPROVEMENT_DOCTRINE.md)
> (IMPROVE, DON'T REWRITE), [`CLAUDE.md`](../CLAUDE.md) STRICT SAFETY RULES, and the
> architecture in [`SECOND-BRAIN-SUPERGOVERNOR-v0.2.md`](SECOND-BRAIN-SUPERGOVERNOR-v0.2.md).

## Prime directives for this build

1. **Reuse B6, never rebuild it.** The existing NBB Control Plane (171 tests green,
   hardened) *is* component **B6**. Every brain and every Second-Brain feature rides on
   B6's primitives (below). We extend and inherit; we do not replace.
2. **Data-safety spine.** Nothing touches real private data — `09 - People`,
   `03 - Projects/Crypto - etoro`, `10 - Telegram`, Accounting, OnlyFans — without
   **(a)** a per-phase owner approval, **and (b)** passing through B6 as
   `ActionProposal → gate → human verdict → ledger`. Reads of restricted folders are
   opt-in per folder. Secrets never enter repo/ledger/cassette (CLAUDE.md rule 6).
3. **Shadow-first.** Every runtime phase runs in `Mode.SHADOW` (simulate + ledger, never
   execute) until the owner promotes a *specific* action class to live. Live is unreachable
   until the SPEC §6 / Phase-6 gate — the same gate NBB-CP already documents.
4. **Every phase declares Current / Delta / Preserved / Rollback** before work starts, and
   ships its tests in the same commit (CLAUDE.md rule 8). No refactoring the previous phase.

## What B6 already gives us (reuse map)

| Second Brain concept (spec) | Existing NBB-CP primitive — reuse, don't rebuild |
|---|---|
| `ActionProposal` (§8) | `submit_proposal` → `Proposal` + gate decision, ledgered |
| Policy Engine ALLOW/REVIEW/DENY (§8, §14) | `budget_gate` / `spawn_gate` / `effector_gate` (the one choke point, INV-4) |
| Approval Queue + human sign-off | `record_verdict` + `effector_gate` (INV-2), now with **approval TTL** |
| Evidence-Card / Approval-Packet (§6) | **`EvidencePack`** on a proposal (added this session) |
| Kill switch (§4 B6, §8) | `record_kill`/`resume` → engaged switch halts every effector gate (INV-3) |
| Run Ledger / Trace / provenance (§3 `_ops`) | append-only hash-chained ledger (the genome, INV-5) + `rebuild_projections` |
| Replay Package | L2 cassette replay (deterministic) |
| Incident / Unknown tracker | `INCIDENT` events + `run_audit()` (7 invariant checks) |
| Memory promotion gate (§15) | proposal + **evidence-gated** verdict (`no_canonical_without_evidence`) |
| Budget / cost governance | global cap + 3-bucket spend + per-organ fitness |

New brains are **config + prompt + a thin adapter**, not new control logic.

## Risk ladder (applies to every action, per spec §4/§14)

`low → medium → high → critical`. Gated action classes that are **never** executed
directly by any brain (always `ActionProposal`): external message · canonical write ·
script execution · file deletion · financial action · architecture mutation · memory
promotion. These map 1:1 onto B6's `irreversible`/verdict path.

---

## Phase 0 — Foundation (DONE, no work)

NBB-CP / B6 is built and hardened: ledger, gates, verdicts, evidence pack, approval TTL,
kill switch, audit, replay, 171 green. This is the control spine every later phase reuses.
**Exit: already met.**

## Phase 1 — Vault standardization · docs/prompts only · ZERO vault mutation · ZERO private data

- **Deliverables** (spec §6/§7/§9–11): `SUPERBRAIN-GOVERNOR.md`; `B1..B8` prompt files;
  `agents.yaml` (Fugu, `use_ultra: false`); templates (Brain-State, Handoff-Packet,
  Project-Card, **Evidence-Card**, Decision-Record, **Approval-Packet**, Memory-Write);
  frontmatter standard; empty `CHANNEL_MAP.md` scaffold.
- **Nature:** pure authoring of text files. No agent runs. No vault reads or writes.
- **Preserved:** everything. **Rollback:** delete the files.
- **Owner checkpoint:** review the 9 prompts + `agents.yaml` + templates.
- **Exit:** owner approves the prompt/config set. *(This phase is safe to start immediately.)*

## Phase 2 — Read-only vault scanner + hidden-channel discovery · READ-ONLY

- **Deliverable:** a scanner (new `adapters/vault/…`, kernel stays pure — CLAUDE.md rule 2)
  that parses markdown, extracts frontmatter/links/tags, builds a graph, detects
  orphans/bridges (spec §13), and emits `CHANNEL_MAP.md` **as a proposal through B6**, not a
  direct write.
- **Safety:** read-only. Restricted folders (`09 - People`, `Crypto - etoro`, `10 - Telegram`)
  are **excluded by default**; the owner opts in per folder. Content never leaves the machine;
  secrets scrubbed. The map write is a B6 proposal the owner approves.
- **Reuses:** proposals + evidence + verdict for the map write; ledger for trace.
- **Owner checkpoints:** which folders may be scanned; approve the `CHANNEL_MAP` write.
- **Rollback:** scanner writes nothing on its own; delete `CHANNEL_MAP.md`.

## Phase 3 — SuperBrain runtime (Fugu API) · SHADOW ONLY

- **Deliverable:** the SuperBrain router as a Fugu adapter **behind `LLMPort` in
  `adapters/llm/`** (rule 2). It classifies intent, routes to brain(s), builds Handoff Packets
  and `ActionProposal`s, and stores the run trace in the ledger. Runs in `Mode.SHADOW`:
  brain actions are simulated and ledgered; nothing executes for real.
- **Safety:** needs a Fugu API key (owner-supplied; never committed). Shadow-only ⇒ no real
  writes, comms, or financial actions. Brains only *propose* (INV-4). External text is
  quarantined (INV-9). Cassette-miss = error, never a mock fallback (rule 4).
- **Reuses:** the entire control plane — proposals/gates/verdicts/kill/audit/ledger/replay.
- **Owner checkpoints:** supply Fugu key; approve shadow runtime.
- **Rollback:** disable the runtime; the ledger + replay preserve every run.

## Phase 4 — Vault governance & memory promotion · proposal-only writes

- **Deliverable:** encode the vault policies (spec §14) as B6 gate checks, and wire the
  memory-promotion pipeline (spec §15: raw→episodic→semantic→canonical-candidate→approval→
  canonical) as **evidence-gated** proposals + verdicts. Approval Queue + provenance.
- **Safety:** this is where a write *path* could first exist — but every write is
  proposal→owner-verdict. No direct canonical writes, external messages, or financial
  actions. `vault_mass_update` degrades to safe mode. Exactly what B6's gates/verdicts/
  evidence/TTL already enforce.
- **Reuses:** policy engine = gates; approval queue = proposals+verdicts; provenance = ledger;
  evidence-gated promotion = the `EvidencePack` added this session.
- **Owner checkpoints:** approve the policy set; approve enabling any real write path, per class.
- **Rollback:** policies are additive gates; keep write-execution off (stay shadow).

## Phase 5 — Human dashboard · read-only

- **Deliverable:** a read-only view (spec §12/§16): active runs, brain status, project
  status, pending approvals, unknowns, hidden channels, risk heatmap — the "evidence pack →
  fast decision" reviewer surface. Reads the ledger/projections; extends `api/http.py`
  additively.
- **Safety:** read-only; renders proposals + evidence for approve/deny. No new authority.
- **Rollback:** it's a view; remove it.

## Phase 6+ — Live actions on real private data · HARD-GATED, one action-class at a time

Only after Phases 1–5 are green **and** the owner promotes NBB-CP to live via the existing
SPEC §6 gate. Each sensitive class — write to People, act on Crypto-eToro, send Telegram,
publish content, touch Accounting — is enabled **individually**, each with its own owner
verdict + evidence + TTL + kill-switch coverage + audit. Default stays deny/shadow.

---

## What I will NOT do without explicit, per-item approval

- Read or write any restricted folder (People / Crypto-eToro / Telegram / Accounting).
- Send any message, publish anything, or perform any financial action.
- Mutate the vault en masse, execute scripts against it, or write `canonical` memory.
- Add or weaken any NBB invariant (INV-11); a phase that conflicts with an invariant stops.

## Open questions for the owner (needed before Phase 2+)

1. **Fugu API** — is there an API key/endpoint available, and how should it be supplied
   (never in repo)? *(blocks Phase 3)*
2. **Vault path** — where does the Obsidian vault live on disk? *(blocks Phase 2)*
3. **Scannable folders** — for Phase 2, which folders may be read? (default: exclude the
   four restricted ones.)
4. **Start Phase 1 now?** It is docs/prompts only — zero vault access, zero private data,
   fully reversible.
