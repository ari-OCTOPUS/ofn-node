# 10 — Threat Model (بالاترین‌اثرها)

> OWASP-Agentic + STRIDE. هر مورد: کنترلِ موجود + شکاف.

- Denial-of-wallet — CONTROL: AU30 monthly + AU20 per-action caps, organ_gate fail-closes on every unknown path, paid double-lock. GAP: paid gate is currently OPEN (date shield bypassed by two present ACTIVATION flags) and dollar telemetry reads all-zero (blind vs proven-$0).

- Special-category PII exposure (DNA/EEG/HRV + partner data) — CONTROL: prose policy + 4 hand-coded guards + data-locality intent. GAP: no code read-guard, absent from .agentignore, depth_guard shadow-only, langar egress scrubber FAIL-OPEN with partner name in outbound headers, no erasure path.

- False confidence from testing/evaluation — CONTROL: 151 genuine registered tests + fail-closed fingerprinted capability marker. GAP: no versioned adversarial eval dataset, 12 orphan/green-lie-shaped tests, hidden RED test, stdout-grep held-out oracle, dormant anti-metric-hacking check, no e2e lead-pipeline eval.

- Observability blindness / un-reconstructable runs — CONTROL: fresh per-beat telemetry + excellent fail-closed per-beat isolation + PII-clean logs. GAP: correlation_id is per-emit noise, structlog sink dark, checkpoint() no-ops, tracer orphaned, ledger governance-only-sparse.

- Excessive-agency / self-modification — CONTROL: code_autonomy 7-gated + INACTIVE (flag absent), auto-knob limited to 3 reversible cadence timers, deny-regex on money/schema/kill/merge. GAP: self-referential guard edit latent (deny-list omits code_autonomy.py + sibling fuses), OCTOPUS_WIRE_APPLY_MERGE defaults on, 'merged' state can read as falsely 'applied'.

- Indirect prompt-injection / RAG poisoning — CONTROL: Telegram whitelist on from.id, keyword-only lead parse (no LLM), topic sanitize+wrap+GUARD_SENTENCE, GET-only web research with no second-order fetch. GAP: untrusted web-result title reaches the owner-facing Persian notification verbatim after cosmetic clean only.

- Systemic maintainability collapse — CONTROL: locally careful hot path, atomic writes, byte-compiles. GAP: zero dependency manifest, flat sys.path namespace with a real module collision + unbounded growth, God-loop + 2069-line monolith, single-machine hardcoded paths.

