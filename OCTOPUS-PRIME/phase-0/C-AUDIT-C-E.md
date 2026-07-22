# C-AUDIT-C-E

## summary
Candidate _ops/chrono.py authorizes money/E4 releases by kind-string allowlist, NOT by the proven target binding H(effect_id, action_kind, target_ref, canonical_content_hash, effect_class, expiry) with single-use anti-replay. The gated_effect table (chrono.py:205-214) has ZERO binding columns (no content_hash, action_kind, target_ref, effect_class, expires_at, approval_id/approved_by, idempotency_key), so exact binding is structurally impossible today. release_gated_effects batch-releases every pending money kind {send,publish,sync,pay} on a single human-append with one shared release_ref (no per-effect binding, no expiry, no anti-replay); demo_run.py STEP 8 explicitly proves PAY->releasable this way and only claims the footgun 'closed' for lead_outbound. settle() re-verifies nothing but status=='releasable'+release_ref present. release_one() binds effect_id ONLY, no content/action/target/effect_class/expiry check and no single-use tracking. on_human_judgment falls back to the batch path whenever an approval lacks effect_id. proposal_id/mission_id are provenance-only (absent from candidate schema; in the prototype set at request but NEVER read in release_effect) — confirmed not authority. Porting the prototype (migrate_up + request_effect + release_effect, 13/13) requires adding binding columns, widening the status CHECK to include NEEDS_OWNER_REVIEW/LEGACY_UNBOUND, quarantining legacy unbound pending rows, disabling money batch release, and making every path below fail-closed for E4. Paths that must become fail-closed for E4: chrono.release_gated_effects (391-405), chrono.on_human_judgment batch fallback (521-527), chrono.release_one insufficient binding (407-424), chrono.settle final gate (443-452), and approval_channel _do_approve money settle (772-800).

## findings
- **[critical]** release_gated_effects batch-releases ALL pending money/E4 effects on ONE human-append with a single shared release_ref, bound to nothing per-effect (no effect_id/content_hash/action_kind/target_ref/effect_class/expiry, no anti-replay). Primary footgun. Port: adopt prototype release_gated_effects_money_DISABLED so money/E4 is never batch-releasable (return 0 / fail-closed); E4 releases only via per-effect binding-checked release_effect.
  - ev: `_ops/chrono.py:391-405`
  - port: 
- **[critical]** _BATCH_RELEASE_KINDS is a money/E4 allowlist {send,publish,sync,pay} matched by lower(trim(kind)); kind is a free string proxy and the row carries no effect_class, so the gate cannot actually tell an effect is E4 — it trusts the label. Port: store effect_class (outcomes/taxonomy.py EFFECT_CLASSES) on gated_effect and gate on it, not on kind-string.
  - ev: `_ops/chrono.py:346`
  - port: 
- **[critical]** settle() — the sole world-crossing point — authorizes on ONLY status=='releasable' AND release_ref non-empty. It does NOT re-verify the target binding, expiry, or single-use, so any effect a batch-release marked releasable passes through. Port: settle must re-verify H(effect_id,action_kind,target_ref,canonical_content_hash,effect_class,expiry), enforce expires_at>now, and consume a single-use approval before flipping to settled; fail-closed on mismatch.
  - ev: `_ops/chrono.py:443-452`
  - port: 
- **[critical]** release_one() binds by effect_id ONLY: checks approval hash non-empty and status=='pending', never checks content_hash/action_kind/target_ref/effect_class/expiry and has no anti-replay, so the same entry hash can release many different effects or be replayed. Port: replace with prototype release_effect (verify effect_id+content_hash+action_kind+target_ref+expires_at>now+unused approval_id via single-use table, all fail-closed).
  - ev: `_ops/chrono.py:407-424`
  - port: 
- **[high]** on_human_judgment falls back to the batch path whenever the approval judgment lacks effect_id; the inline comment admits this is the remaining open money-batch route. Port: an approval with no bound effect_id must release 0 E4 effects (fail-closed), never batch money.
  - ev: `_ops/chrono.py:521-527`
  - port: 
- **[high]** gated_effect table has NO binding columns (content_hash, action_kind, target_ref, effect_class, expires_at, approval_id, approved_by, idempotency_key, proposal_id, mission_id all absent) and the status CHECK only allows pending/releasable/settled/refused, so exact binding and legacy quarantine are structurally impossible. Port: run prototype migrate_up (table-recreate adds v2 columns, widens CHECK to include NEEDS_OWNER_REVIEW/LEGACY_UNBOUND, PRAGMA user_version=2, idempotent/additive, quarantine legacy pending rows lacking content_hash as NEEDS_OWNER_REVIEW).
  - ev: `_ops/chrono.py:205-214`
  - port: 
- **[high]** Live telegram money path _do_approve builds judgment WITH effect_id then calls _on_human_judgment (-> release_one, id-only bind) and settles via gate.settle directly, bypassing even the staleness bridge — E4 money settled on effect_id-only binding. Port: route through binding-checked release_effect+settle; the telegram approval must be verified against content_hash/action_kind/target_ref/effect_class/expiry and consume a single-use approval_id.
  - ev: `_ops/budget/approval_channel.py:772-800`
  - port: 
- **[high]** Demo claims the footgun 'closed' but STEP 8 explicitly proves PAY (money/E4) still becomes releasable via one release_gated_effects call; only lead_outbound (customer-send) is protected — money batch release is by design still open. Port: after the port, PAY must NOT become releasable from a bare batch human-append; update the proof so all E4 kinds require per-effect bound release.
  - ev: `_ops/discovery/2026-07-21_LEAD-SAFETY-C1-DEMO/demo_run.py:151-160`
  - port: 
- **[info]** proposal_id/mission_id are provenance-only, NOT authority: absent from candidate chrono schema (only named in a future-work comment at chrono.py:519), and in the proven prototype they are written at request_effect (prototype lines 70-85) but never read in release_effect's checks (prototype lines 91-115). Port: keep them as recorded provenance columns only; never gate release/settle on them — authorization comes solely from the verified binding + single-use approval.
  - ev: `_ops/chrono.py:519`
  - port: 
- **[medium]** sweep_stale_effects only auto-refuses status=='pending'; a releasable-but-unsettled money effect is never expired by chrono, and the effector_gate_bridge staleness guard exists ONLY on the lead path (effector_gate_bridge.py:99-165), not the money/telegram settle path. Port: enforce expires_at at settle for E4 so a stale releasable money effect fails closed regardless of caller.
  - ev: `_ops/chrono.py:454-470`
  - port: 
