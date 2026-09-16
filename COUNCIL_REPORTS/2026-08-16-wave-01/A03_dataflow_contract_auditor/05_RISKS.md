# 05_RISKS — A03 (2026-08-16)

Ranked by (likelihood × impact) within A03's dataflow/contract scope.

## R-1 · Owner-console blast radius: `/sh` (MEDIUM)
Authenticated owner text → arbitrary shell, no double-confirm, no action receipt. Any
compromise of the owner Telegram account (session hijack, malicious client, forwarded
device) converts directly into host-level execution on the organism machine. Containment is
a single factor (chat_id). → BP-01.

## R-2 · Memory poisoning of the research brain (MEDIUM)
`generate_hypothesis` persists raw LLM output into the ungated 4d store; that store feeds
future prompts and dedup decisions (`automation.py`). A polluted or injected corpus can
steer hypotheses and waste cycles; it cannot reach execution authority, but it corrupts the
epistemic base the owner relies on ("memory is evidence" — evidence can be forged here).
→ BP-08, F-18.

## R-3 · Parallel external-effect lane drift (MEDIUM)
The lead-email lane is safe by its own gate stack today, but it validates the *pattern* of
building A4-class executors outside action_bridge. Each new lane (email now; others later)
must re-implement authorization/expiry/idempotency/staleness correctly; the species of bug
action_bridge was built to make impossible (e.g., replay, stale approval) must now be
prevented per-lane. `OCTOPUS_LEAD_DAILY_SEND_CAP<=0` already removes the numeric cap by
owner instruction, leaving consent/authorization/STOP as the only belts. → F-13.

## R-4 · Bitemporal overclaim (MEDIUM, epistemic)
Self-model and dashboards may reason from "bitemporal ledger" capability that does not
exist in operation (single `ts`; occurred/recorded always equal). Any future audit, replay,
or dispute resolution that assumes event-time/record-time separation will be wrong.
→ C-1, F-14, F-15.

## R-5 · Timestamp ambiguity across stores (MEDIUM)
Naive local strings (receipts, 4d events), UTC ISO with offset (genome, spine), epoch
floats (missions, agi2027), and one timestamp-less ledger (c6 research). Cross-ledger
correlation (e.g., "was this approval granted before this action?") is guesswork near DST
boundaries or clock skew; `control_contracts` staleness checks compare mixed formats today.
→ F-29.

## R-6 · Flag-snapshot vs live-env divergence (LOW-MEDIUM)
Evidence for "armed" is a snapshot (`flags-loaded-cortex.json`, AEB bundles, flags.cmd) —
not the live process environment. If runtime env differs (partial boot, stale cmd file),
lines like "bridge live" could be wrong in either direction. Requires A02 runtime probe.
→ F-31.

## R-7 · Two policy vocabularies (LOW-MEDIUM)
4d `ACTION_POLICY` levels 0-5 vs action_bridge A0-A6 vs telegram risk tiers
(read/low/medium/high) vs autonomy_level 0-5. Cross-referencing docs to code is
error-prone; a future change could satisfy one ladder while violating another.
→ C-6, F-19.

## R-8 · Repair-rewritable state ledgers (LOW-MEDIUM)
state_guard can rewrite unchained JSONL "ledgers" (quarantine pattern). Not an integrity
break today (no chains on those files), but any consumer starting to treat them as
tamper-evident evidence inherits a silent-edit hazard. → F-26.

## R-9 · Afferent fiction risk (LOW)
The "sensory" channel is internally generated aggregates. The afferent-ratio alarm is
designed to detect dreaming, but the diet is self-observation — fine while understood,
risky if docs keep saying "Sensorium active" and future work assumes real-world grounding.
→ F-10.

## R-10 · Deprecated-but-present second poller (LOW)
4d telegram_bot would 409-collide with the live center if ever revived without the
documented owner check; guard is fail-closed opt-in (good), the residual risk is social
(someone sets the env var to "fix" a silent bot). → F-30.
