# 2026-07-31 · MASTER PLAN — OCTOPUS Repair-and-Complete
**Role:** Master/Architect (this session) · **SoT:** F:\backup · **Owner:** Armin (Ari)
**Built on:** 16 owner decisions (see Desktop/OCTOPUS-MASTER-SESSION-2026-07-31/05-DECISIONS-LOG.md)
**Status:** AWAITING OWNER RATIFICATION (D4: plan first, then choose execution model)

---

## 0. THE ONE-LINE STRATEGY
**نخست ریسک‌ها و redها را ببند، بعد gapهای تلگرام را با arm flag پر کن، Hebbianِ واقعی را
instrument کن تا پل به چشم‌انداز EFE بشه — و تمام این‌ها را با diff+test+rollback، در خود
F:\backup، بدون ساخت قلبه‌ی خیالی. تلگرام را ایجنتِ مخصوصِ تلگرام می‌سازه؛ من فقط چترِ
چارتر و قرارداد را می‌دم.**

## 1. WHY THIS PLAN (not the Grok surgical megaprompt)
The Grok megaprompt assumes an EFE/Active-Inference layer that **does not exist in code**
(PolicyPFE, efe_scores, kuramoto, reward_engine, audit_label = all absent; only in research
docs; HEART_PRECISION_WEIGHT=0). Acting on it as "surgery" = building on a phantom.

This plan instead operates on **what is real and live**:
- `organism.py` (1,241 LOC, beat ~19,893, running now)
- Hebbian layer (`neural/hebbian.py` + `wiring.py` L1058-1429)
- trace_id provenance (pervasive)
- Telegram subsystem (~18,000 LOC + 34 test files)
- 8 ledger DBs

Per owner decision **D1 (EFE = vision, repair live)** + **D2 (TG = gap+flag, not rebuild)**.

---

## 2. THE SIX WAVES (execution order matters)

### WAVE 0 — STABILIZE & RED-CLOSE  [owner priority D5 — FIRST]
Goal: kill the documented risks before any feature work.
| Item | Resolve | How | Files | Risk |
|------|---------|-----|-------|------|
| 0.1 send-audit red sites | TG lane ratchet | tri-state (attempted/held/blocked) on 8 remaining send sites | telegram_center/* send sites | M |
| 0.2 os.replace freeze | VQ-STATE-WRITE-001 | retry+backoff on WinError 5, atomic journal | state writers | L (patched, await merge) |
| 0.3 blind doctor budget | VQ-BUDGET-001 | ONE unified meter: doctor spend + AU$30 cap (D10) | budget/ + ledger | M |
| 0.4 ledger chain disagreement | VQ-LEDGER-CHAIN-001 | canary evaluator, owner vote | spine.db / outcomes | M |
| 0.5 genome chain audit | trace integrity | verify receipts.db chain | receipts/ | L |
**Done =** all 4 open P0/P1 red items closed with owner vote; test suite green.

### WAVE 1 — COMMIT & VALIDATE  [D11 + D12]
Goal: clean git + prove the organism is healthy post-patch.
- 1.1 Commit Wave 1-5 WIP (break genome lock WITH owner approval) — D11.
- 1.2 Controlled restart of organism for live validation — D12, with checklist + receipt.
- 1.3 Drift guard + security scan re-run (baseline 0/414 must hold).
**Done =** clean git tree; organism restarted; ORGANISM-STATE.json beat advancing; receipts logged.

### WAVE 2 — HEBBIAN INSTRUMENTATION  [D15 — the EFE bridge]
Goal: make the REAL learning layer observable — the honest path to EFE vision.
- 2.1 Log Hebbian signal strength + association drift to a ledger table (new: `hebb_observations`).
- 2.2 Expose via trace_id (provenance already exists) so every association is queryable.
- 2.3 Dashboard surface: Hebbian health card (ties to CH-16 Neural Vitals, already a channel).
- 2.4 This is NOT EFE — it is observability on what exists, the prerequisite for any future EFE.
**Done =** every Hebbian association has a traceable, timestamped, ledger-persisted observation.

### WAVE 3 — TELEGRAM GAP CLOSURE (umbrella only; TG agent owns build)  [D2 + D9]
Goal: close chartered gaps behind already-wired flags. **My deliverable = charter + contract + advisory, NOT code.**
- 3.1 inner/outer split arm (OCTOPUS_TG_SPLIT_V1) — foundation of the two-bot model.
- 3.2 capture module (text/image/link → classify → vault) — the "octopus hand" (D6: + local whisper for voice).
- 3.3 reminder engine + morning/evening brief (rhythm per charter).
- 3.4 lead machine arm (with owner ARM vote on daily outbound cap) — revenue motor (D8: اونلی فنز/langar in scope).
- 3.5 callback HMAC arm (OCTOPUS_WIRE_CB_TOKEN) — security.
- 3.6 Mini App — **advisory only** (D7: a TG agent already built it; I haven't seen the new build).
**Done =** flags armed, gaps closed, charter 24-vote contract honored; TG agent validates.

### WAVE 4 — AUTONOMY TIERING  [D3 + D14]
Goal: wire the T0–T3 autonomy model into the action path.
- 4.1 PATCH_CARD arms T0/T1 only (D3); T2/T3 stays fail-closed vote card.
- 4.2 Failure mode: T0/T1 → auto-revert+notify; T2/T3 → pause+Owner card (D14).
- 4.3 VQ-AUTONOMY-QUEUE-001 resolved toward this tiered model.
**Done =** every action classified T0–T3 with matching gate; test scenarios for each tier.

### WAVE 5 — COHERENCE & DOC  [D13 + D16]
Goal: the organism stays integrated; changes live in-vault.
- 5.1 Update architecture maps (06-Architecture Maps) to reflect reality (NOT the EFE phantom).
- 5.2 Detailed change doc for specialist grading (diff + test + rollback per change) — D13.
- 5.3 Reframe/delist the Grok surgical megaprompt (mark as superseded by this plan).
**Done =** vault docs match code reality; grading doc complete.

---

## 3. THE UMBRELLA DELIVERABLES I PRODUCE (not TG build)
Per D9 ("ایجنت TG جدا، من فقط چتر"), my actual artifacts:
1. **This Master Plan** (Wave 0–5, decision-anchored).
2. **TG Charter update** — refresh TG-UI-CHARTER to reflect EFE-reality + gap priorities.
3. **Access Contract v1** confirmation — the 3-tier (outer/inner/group) the TG agent operates under.
4. **Hebbian instrumentation spec** (Wave 2) — the real EFE bridge.
5. **Specialist grading doc** — every change with diff/test/rollback (D13).

I do NOT write the precise TG build megaprompt — the TG agent owns that, and I haven't seen
its new build (D7). I give it the umbrella, not the bricks.

---

## 4. GOVERNANCE INVARIANTS (do not violate)
- Owner = sole authority for money, external actions, Orange/Red, kill/rollback.
- Every buy/sell/withdraw = HARD_STOP, human only. (D10 meter does NOT auto-move money.)
- Auto-apply capped at T0/T1 (D3). T2/T3 = card.
- One writer per file; center.py serial-only (existing contract).
- Backup on Desktop stays untouched (read-only artifact).
- Changes live in F:\backup (D16); Desktop = backup only.

---

## 5. RATIFICATION ASK
Owner: approve this plan (or amend), THEN we choose parallel-lanes vs serial (D4).
Until ratified — no execution. Wave 0 can begin on owner "go".
