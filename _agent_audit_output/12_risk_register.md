# 12 — رجیستریِ ریسک (P0–P4)

> برای هر P0/P1: مهارِ فوری + اصلاحِ دائمی + تأییدِ صحت.

## [P1] R-01 — No dependency manifest/lockfile for the 68.8k-LOC / 326-file _ops organism; numpy + PyYAML (core money gate) undeclared — environment is unreproducible and a silent version bump can break the money gate.
- **مهار:** Snapshot the current working interpreter's pip freeze into a note; pin PyYAML/numpy versions manually on the one live machine.
- **اصلاحِ دائمی:** Add pyproject.toml + pinned requirements.txt + lockfile; CI a clean-env install + byte-compile.
- **تأیید:** Fresh venv install from lockfile → run_all.py green + organism boots.

## [P1] R-02 — Flat namespace via 562 runtime sys.path inserts (136 in-function, unguarded) causes unbounded sys.path growth on the always-on loop AND a real module-name collision (_ops/events.py vs 4d_system/brain/events.py shadow each other), silently breaking dual-emit.
- **مهار:** Guard in-function inserts against duplicates; rename one events.py import site.
- **اصلاحِ دائمی:** Convert _ops to a proper package with __init__.py; replace bare sibling imports with package-qualified imports; remove sys.path hacking.
- **تأیید:** grep sys.path.insert → 0 in hot factories; import-time stable over a 6h run; both events emitters callable in one process.

## [P1] R-03 — No versioned adversarial eval dataset for a live, money-adjacent, self-modifying agent — injection coverage is 3 single-case asserts; poisoning, stale-memory, and tool-failure matrices do not exist.
- **مهار:** Freeze the 3 existing adversarial asserts as a named smoke set; block any autonomy flag flip until a dataset exists.
- **اصلاحِ دائمی:** Create _ops/tests/eval_dataset/ with versioned injection/poisoning/tool-failure/stale-memory cases + scored pass-bars that gate the suite.
- **تأیید:** phase_gate consults the eval set; a deliberately poisoned case fails the gate.

## [P1] R-04 — 12 orphan test files never execute (incl. 4 green-lie-shaped: registering one as a direct-run entry yields silent green); ≥1 known-RED test (test_durable_journal) hidden from the suite; run_all.py carries a factually FALSE removal justification — coverage-claimed ≠ coverage-executed.
- **مهار:** Add a suite self-check that fails if any test_*.py on disk is unregistered.
- **اصلاحِ دائمی:** Register-or-delete all 12; route pytest-style files through PYTEST_TESTS; un-hide test_durable_journal; correct the false comment; report TESTS+EXTRA count.
- **تأیید:** disk test_*.py count == executed count; hidden RED now visibly fails or is fixed.

## [P1] R-05 — Special-category PII (DNA/EEG/HRV + partner personal data) is protected by prose policy only: no code read-guard, '08 - Partner (PII)' absent from .agentignore, depth_guard is shadow-only (never blocks), and constitution forbids deletion so there is no erasure path — a foreign/new consumer bypasses all protection.
- **مهار:** Add Partner/PII + hypnosis DNA/EEG paths to .agentignore immediately; owner-manual quarantine of the raw genetic files.
- **اصلاحِ دائمی:** Implement a real deny-read guard for those folders; define a lawful erasure/redaction procedure for special-category data; correct the 'PHI deny-by-default' overclaim.
- **تأیید:** Agent read of a Partner/PII path is denied by code; erasure procedure demonstrated on a test record.

## [P2] R-06 — Denial-of-wallet: the paid LLM gate is OPEN now — paid_gate() bypasses the 2026-07-21 date shield because BOTH ACTIVATION-RESEARCH-EARLY.flag and ACTIVATION-CORTEX-PAID.flag are present. Bounded by AU30 cap + organ_gate fail-closed, but not date-locked.
- **مهار:** Remove one activation flag to re-arm the date shield; confirm month spend alarm.
- **اصلاحِ دائمی:** Decide policy explicitly (open vs shielded) and encode it; alarm on any nonzero paid spend.
- **تأیید:** paid_gate returns closed pre-2026-07-21 unless a documented owner decision keeps it open.

## [P2] R-07 — Human-append anti-forgery is default-DISABLED passthrough — HumanAppendGuard returns (True,'guard-disabled-passthrough') unless HH_HUMAN_GUARD_STRICT=1, so is_human ledger appends are forgeable. Narrow blast radius (money/code approvals read owner-gated files, not this guard).
- **مهار:** Set HH_HUMAN_GUARD_STRICT=1 in the live env.
- **اصلاحِ دائمی:** Make strict-mode the default and fail-closed when no secret is configured.
- **تأیید:** An unsigned is_human append is rejected at runtime.

## [P2] R-08 — OnlyFans langar_bot does a live Telegram POST guarded by a FAIL-OPEN scrubber (empty blocklist → any surname/handle passes) and bakes the real partner name into source identifiers + the outbound User-Agent header — a genuine PII-egress vector.
- **مهار:** Populate the blocklist; disable langar send until scrubber is fail-closed.
- **اصلاحِ دائمی:** Make OpsecGuard fail-closed (deny on empty/unknown), strip name from class/env-var/User-Agent.
- **تأیید:** A crafted message containing the name/handle is redacted or blocked before egress.

## [P2] R-09 — Map/territory drift misleads the operator on the live spend/self-mod/send surface: architecture_extracted.md still asserts 'no send/pay/trade' while paid calls run and the gate is open; 'send structurally absent' is true only for _ops legs, not langar_bot.
- **مهار:** Add a caveat banner to the stale audit docs.
- **اصلاحِ دائمی:** Reconcile audit docs to running config each session; add a live-config-vs-doc drift check to weekly review.
- **تأیید:** Docs state the accurate scoped claim; drift check passes.

## [P2] R-10 — No schema/dataclass/pydantic validates any LLM output; debate/governor/synthesis rely on naive first/last-brace slicing + key-PRESENCE checks — an out-of-enum verdict or prose-brace reply silently mis-parses or aborts the debate. Blast radius contained (deterministic path is authoritative).
- **مهار:** Wrap extract_json to fail-soft to the deterministic path on any parse error.
- **اصلاحِ دائمی:** Add typed contracts (MuseIdea/ArchitectVerdict/GovernorAllocation/SynthesisProposal) validated at the parse boundary + provider JSON-schema/tool mode where available.
- **تأیید:** Malformed/garbage-enum outputs are rejected and fall back deterministically in a unit test.

## [P2] R-11 — Decorative memory/RAG stack presents a FALSE capability signal: R^32 latent persist file absent, 494/494 cycles null, 'embeddings' are non-semantic hash projections, BCM keys empty, school memory 7d stale — the advertised '6D manifold / shared latent memory' stores no knowledge.
- **مهار:** Label the layer decorative in all docs; do not rely on it for any decision.
- **اصلاحِ دائمی:** Either wire a real local embedding model + vector store and validate retrieval, or delete the latent/BCM/6D-manifold layer entirely.
- **تأیید:** Retrieval quality measured on a labeled set, OR the dead modules removed and suite still green.

## [P2] R-12 — A single run cannot be reconstructed input→output: correlation_id minted per-emit (same run → different ids), trace-propagating octopus_logger sink dark, checkpoint() no-ops (bus db=None), tracer.py orphaned — incident forensics and replay are effectively blind.
- **مهار:** Mint one correlation_id per RUN and thread it through beats.
- **اصلاحِ دائمی:** Activate structlog file sink; pass a db into make_unified_bus so checkpoint stops no-op'ing; wire or delete tracer.
- **تأیید:** A started/completed pair shares one correlation_id; a run replays from checkpoint.

## [P2] R-13 — ~1300 LOC of dead runtime-orphaned modules (approval_channel_merge, octopus_logger, phase_gate, durable_journal, watchdog_extension) — two have registered GREEN tests, masking the dead code (the 'green test ≠ used' trap).
- **مهار:** Annotate as dead; stop citing them as capabilities.
- **اصلاحِ دائمی:** Delete or wire each; move their tests accordingly.
- **تأیید:** grep non-test importers → 0 removed; suite green after deletion.

## [P2] R-14 — Safety-policy files (settings.json deny-list, _PROJECT_INSTRUCTIONS.md, budgets.yaml, .agentignore, genome/) are agent-Editable — protected only by system-prompt convention + a detective capability-revoke on money-file edits; the genome filesystem lock is only echoed, likely never applied.
- **مهار:** Owner applies the icacls read-only lock on genome/ and budgets.yaml.
- **اصلاحِ دائمی:** Add Write/Edit deny rules for policy files to settings.json; make the lock a real preventive control.
- **تأیید:** An attempted agent Edit of budgets.yaml/.agentignore is denied by the permission layer.

## [P2] R-15 — A ~1500-word auto-generated psychotherapeutic profile of the owner (trauma/attachment/shame) sits plaintext in OWNER-PROFILE.json, is NOT in the deny-read list, and is contained only by 4 hand-coded guards — any new consumer bypasses protection.
- **مهار:** Add OWNER-PROFILE.json to deny-read; scope the field back to the intended one-line answer.
- **اصلاحِ دائمی:** Quarantine the profile; require specialist oversight before generating psychological content.
- **تأیید:** Agent read of the profile is denied; regeneration path no longer emits an essay.

## [P2] R-16 — No human-specialist gate for a converged elevated-risk domain: the same 'langar' psychological-influence technique feeds monetized persuasion of adult-content customers; partner consent is incomplete (no signed two-party agreement; proposed 'body' expansion conflicts with stated consent; 18+/consent docs unchecked).
- **مهار:** Freeze any go-live of the persuasion/adult pipeline until consent + specialist review exist.
- **اصلاحِ دائمی:** Require psychologist/ethicist/legal sign-off for influence+adult content; complete two-party consent + 18+ docs.
- **تأیید:** Signed consent + specialist review recorded before Stage-8 send is buildable.

## [P2] R-17 — Human-oversight escalation channel had a ~5-day blind window (AGENT_QUESTIONS.md dry 07-11→07-16) with safety/money verdicts stranded on unmerged branches — the oversight loop can silently drop critical verdicts.
- **مهار:** Reconcile branch verdicts into the channel now (done this cycle).
- **اصلاحِ دائمی:** Auto-post owner-gated verdicts to the escalation channel + a freshness alarm.
- **تأیید:** A test verdict on a branch appears in the channel within one cycle.

## [P3] R-18 — Local control server (live/server.py, 127.0.0.1:8773) parses POST body regardless of Content-Type with no origin/token check — a simple-request CSRF or any local process can hit /api/action (restart/stop) and /api/ask. Bounded to nuisance/DoS (fixed .bat allowlist, no arbitrary exec).
- **مهار:** Bind is already localhost-only; document the exposure.
- **اصلاحِ دائمی:** Require an Origin check + CSRF token on do_POST.
- **تأیید:** A cross-origin simple-request POST is rejected.

## [P3] R-19 — Watchdog split-brain: a stale duplicate _ops/organism-watchdog.ps1 revives only port 8771 with no cortex awareness — if re-registered, cortex (8772) supervision silently disappears.
- **مهار:** Confirm the scheduled watchdog is the 04-Architect dual-port one.
- **اصلاحِ دائمی:** Delete the stale _ops duplicate + watchdog.py 8771-hardcode.
- **تأیید:** Only the dual-port watchdog exists; killing 8772 triggers revive.

## [P2] R-20 — Product success is undefined numerically and unmeasured despite the large build — KPIs are placeholders and no experiment has run, so there is no signal to justify continued autonomy investment or to detect regression.
- **مهار:** Record the current baseline (0 measured leads) explicitly.
- **اصلاحِ دائمی:** Define numeric KPIs + start experiment #1 + gate further build on a measured metric.
- **تأیید:** A dashboard shows leads/week + cost/lead moving against a target.

