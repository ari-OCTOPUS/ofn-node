---
type: design
project: "[[03 - Projects/VibeGuard/PROJECT]]"
status: draft
tags: [vibeguard, spec, chat-ingest]
created: 2026-08-17
updated: 2026-08-17
created_by: agent
source: chat-chunk-5-of-5
---

# CLI / API / CI / Invariants (تکهٔ ۵ از ۵ — پایانی، از گفتگو)

> ورود 2026-08-17 از چت مالک. کنار [[01-spec-chunk-1]] و [[02-security-engine]] و [[../Project-Specification]].
> تکه‌های ۳ و ۴ در این گفتگو نرسیدند — پوشش‌شان در Downloads spec است: [[GAP-chunks-3-4]].

## CLI

```text
vg [GLOBAL] <command> [ARGS] [FLAGS]

GLOBAL:
  --config PATH            explicit config file (highest precedence)
  --format {text,json,ndjson,sarif}   default: text on TTY, json otherwise
  --output DIR             artifact directory (default .vg/out)
  --offline / --no-offline default: --offline
  --profile {quick,standard,deep}
  --log-level {debug,info,warn,error}
  --quiet                  suppress stderr logs (never suppresses exit codes)
  --no-color               disable ANSI (honors NO_COLOR)
  --sandbox {bwrap,gvisor,seatbelt,none}   'none' needs --i-accept-no-sandbox; refused in CI
  --timeout SECONDS        overrides budgets.total (may only lower it)
  --version | -V           --help | -h
```

| Command | Purpose | Key flags | stdout (machine mode) |
|---|---|---|---|
| `vg scan <path\|url>` | Full pipeline S0–S5,S7,S9 | `--diff BASE..HEAD`, `--languages`, `--max-findings N`, `--fail-on`, `--gate {advisory,block}`, `--no-trust`, `--ai/--no-ai`, `--baseline FILE` | findings JSON (or SARIF) |
| `vg trust <path>` | S0–S1 only: injection/agent-hijack triage | `--tiers 1,2,3,4`, `--include-decoded`, `--index-out FILE` | trust report JSON |
| `vg sbom <path>` | S2 SBOM only | `--format {cyclonedx,spdx}` | SBOM document |
| `vg deps <path>` | provenance/hallucination verdicts | `--online`, `--ecosystem` | dependency verdicts |
| `vg explain <finding_id>` | explanation with citations | `--run RUN_ID`, `--ai` | explanation JSON |
| `vg fix propose <finding_id>` | candidate diff (never applied) | `--strategy {codemod,llm,auto}`, `--max-diff-lines` | patch JSON incl. diff |
| `vg fix verify <patch_id>` | verification gate | `--run-tests/--no-run-tests`, `--timeout` | verdict JSON |
| `vg fix list` | patches for a run | `--run` | array |
| `vg report` | render from a stored run | `--run`, `--format {md,html,sarif,json}` | document |
| `vg baseline create\|show` | baseline of current findings | `--run`, `--out FILE` | baseline JSON |
| `vg suppress add\|list\|verify` | signed suppressions | `--fingerprint`, `--cwe`, `--path-glob`, `--reason`, `--expires`, `--approver`, `--sign-key` | suppression JSON |
| `vg audit verify\|export` | audit-chain integrity | `--file`, `--from-seq` | verification JSON / NDJSON |
| `vg bench --suite NAME` | benchmark harness | `--out DIR`, `--limit N` | metrics JSON |
| `vg rules lint\|list\|test` | rule hygiene (CWE/VIBE metadata required) | `--dir` | lint report JSON |
| `vg doctor` | environment readiness | `--json` | readiness JSON |
| `vg mcp serve` | start MCP server | `--transport {stdio,http}`, `--port`, `--allow-write`, `--allowed-root` | protocol on stdio only |
| `vg hook` | evaluate one hook event from stdin | `--index FILE`, `--event PreToolUse` | decision JSON |
| `vg clean` | remove `.vg/out`, `.vg/cache` | `--all` | summary |
| `vg completion <shell>` | shell completion | — | script |

**stdout/stderr contract (mandatory):**

1. In `--format json|ndjson|sarif`, stdout contains only the machine document — no banners, progress or color; logs go to stderr.
2. In stdio MCP mode, stdout is exclusively the JSON-RPC stream.
3. `--format ndjson` emits a `{"type":"run"}` header, `{"type":"finding"}` objects, then a `{"type":"summary"}` trailer.
4. Machine output is written atomically (temp + rename) with `--output`; a partial streamed run still emits a valid summary trailer with `"complete": false`.
5. RFC 3339 UTC timestamps, repo-root-relative POSIX paths, lowercase hex hashes.
6. `--quiet` never changes stdout.

| Exit | Meaning | Notes |
|---|---|---|
| 0 | Completed; no gate-blocking finding (or advisory mode) | findings may still exist |
| 1 | Completed; gate-blocking finding present and `gate.mode: block` | the only "findings failed the build" code |
| 2 | Usage error (bad flags/config/schema) | also the `vg hook` deny signal per host contract |
| 3 | Target error (path missing, clone failed, unsupported OS) | |
| 4 | Integrity failure (digest mismatch, correlation failure, audit chain broken, SARIF write failure) | never treated as "clean" |
| 5 | Degraded run with ≥1 abstention when `--fail-on-abstain` set | abstentions don't change exit code by default |
| 6 | Stopped early by `trust.stop_on_hostile` | artifacts still written |
| 7 | Budget exceeded (time, tokens, `ai.budget_usd`) | partial artifacts |
| 130 | SIGINT | partial artifacts + audit entry |

Exit code 2 is deliberately overloaded: for `vg hook`, exit 2 is the documented block signal in both Claude Code and Cursor, so `vg hook` uses **64** for usage errors instead.

Env vars: `VG_CONFIG`, `VG_OFFLINE`, `VG_LOG_LEVEL`, `VG_OUTPUT_DIR`, `VG_CACHE_DIR`, `VG_SANDBOX`, `VG_AI_PROVIDER`, `VG_AI_BASE_URL`, `VG_AI_API_KEY`, `VG_GITHUB_TOKEN`, `VG_CI`, `NO_COLOR`. Env beats config files but never beats `TIGHTEN_ONLY`.

## API

Python library (stable, semver'd):

```python
from vg import Engine, ScanOptions, Finding

eng = Engine.from_config(path=".vibeguard.yml")     # validates + freezes config
run = eng.scan("/repo", ScanOptions(offline=True, profile="standard"))
run.findings          # list[Finding] (pydantic, JSON-schema-backed)
run.trust.label       # clean_of_known_signals | suspicious | hostile | abstain
run.abstentions
run.to_sarif()        # SARIF 2.1.0, caps enforced
run.to_cyclonedx()
patch   = eng.propose_fix(run, finding_id)          # never applies
verdict = eng.verify_fix(patch)                     # sandboxed
eng.close()                                         # tear down jails, flush audit
```

No global state; side-effect-free except writes under `output.dir` and `.vg/`; all exceptions derive from `vg.errors.VgError` with `.code` matching CLI exit codes.

HTTP API (GitHub App / self-hosted, OpenAPI 3.1 at `/openapi.json`; App installation tokens or scoped bearer; `application/problem+json` errors):

| Method | Path | Purpose | Notes |
|---|---|---|---|
| POST | `/v1/scans` | enqueue a scan | 202 + `{scan_id}` |
| GET | `/v1/scans/{id}` | status + summary | `queued\|running\|done\|failed\|abstained` |
| GET | `/v1/scans/{id}/findings` | paged findings | `?cursor=&limit=&min_severity=` |
| GET | `/v1/scans/{id}/sarif` | SARIF 2.1.0 | gzip; ≤10 MB |
| GET | `/v1/scans/{id}/sbom` | CycloneDX 1.7 | |
| GET | `/v1/scans/{id}/evidence` | evidence bundle (tar.zst) | signed manifest |
| POST | `/v1/scans/{id}/fixes` | propose a fix | write-classified |
| POST | `/v1/fixes/{id}/verify` | verification gate | write-classified |
| POST | `/v1/fixes/{id}/approve` | human approval → PR | audit-logged |
| POST | `/v1/webhooks/github` | webhook receiver | verifies `X-Hub-Signature-256` |
| GET | `/v1/healthz` `/v1/readyz` | liveness/readiness | no data exposure |
| GET | `/v1/limits` | rate-limit/quota state | mirrors GitHub headers |

Platform-derived constraints: SARIF upload capped at 1,000 requests/hour per installation and 10 MB gzipped per file; Checks annotations 50 per request (repeated PATCH appends), with Actions surfacing only 10 warnings + 10 errors per step; installation tokens 5,000–12,500 req/hour. The queue MUST implement per-installation token buckets and backoff on `x-ratelimit-remaining: 0`.

## CI/CD Integration

```yaml
name: VibeGuard
on:
  pull_request:
  push: { branches: [main] }
permissions:
  contents: read              # minimum; write nothing by default
  security-events: write      # only if uploading SARIF (requires GHAS)
  pull-requests: write        # only if commenting
jobs:
  vibeguard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@<FULL_COMMIT_SHA>     # SHA-pinned: tags are movable
        with: { fetch-depth: 0, persist-credentials: false }
      - name: VibeGuard scan
        uses: <org>/vibeguard-action@<FULL_COMMIT_SHA>
        with:
          profile: standard
          offline: 'true'
          gate: advisory                # 'block' honors gate_blocking findings only
          formats: 'json,sarif,sbom,md'
          sarif-category: vibeguard     # unique per analysis
      - name: Upload SARIF
        if: always()
        uses: github/codeql-action/upload-sarif@<FULL_COMMIT_SHA>
        with: { sarif_file: .vg/out/vibeguard.sarif, category: vibeguard }
```

Hard CI rules:

1. Third-party actions pinned to full commit SHA — a compromised action reads all repo secrets and `GITHUB_TOKEN` and can write to the repo, and tags move.
2. Never interpolate untrusted context into `run:` blocks — `pull_request.title`, `.body`, `head_ref`, `label`, `message`, `name`, `page_name`, `ref` are untrusted, and `zzz";echo${IFS}"hello";#` is a valid branch name.
3. `.github/workflows` in CODEOWNERS.
4. Fork PRs get no secrets, so forks run offline-only with a check summary, not a comment.
5. Commits made with the default `GITHUB_TOKEN` do not trigger workflows — use the App if fix PRs must trigger CI.
6. Scheduled workflows run only from the default branch and are disabled after 60 days of inactivity in public repos, so the App's cron is authoritative.
7. `GITHUB_TOKEN` is 1,000 req/hour per repo with ≤6 h lifetime — anything API-heavy uses an installation token.
8. Any user with write access can read all repo secrets and log redaction is not guaranteed, so VibeGuard MUST NOT echo secret-like values at all.

GitHub App: subscribes to `pull_request`, `push`, `installation`, `check_run.rerequested`; creates a Check Run and updates `conclusion` ∈ `success|neutral|failure|action_required`; uploads SARIF (`POST /repos/{owner}/{repo}/code-scanning/sarifs` with `commit_sha`, `ref`, base64 gzip) and falls back to Checks annotations on 403 when GHAS is absent. PR alerts appear only when all lines identified by an alert exist in the diff, so diff-aware mode also drives what gets annotated.

Other CI (GitLab, Jenkins, pre-commit): run the OCI image with `--format sarif`. The pre-commit variant runs `vg trust --tiers 1 --format json` only (fast, near-zero FP) and blocks on critical Tier-1 signals.

## Claude Code Integration

Distribution is a plugin; enforcement is a hook; capability is MCP. The engine never depends on it.

```json
{"name":"vibeguard","description":"Security triage for AI-generated repositories: deterministic scanning, agent-hijack detection, verification-first fix proposals.","version":"1.0.0","author":{"name":"VibeGuard"},"homepage":"https://vibeguard.dev","repository":"https://github.com/<org>/vibeguard","license":"Apache-2.0"}
```

Skill (`skills/vibeguard-review/SKILL.md`) — guidance only:

```yaml
---
name: vibeguard-review
description: Run a VibeGuard security review of the current repository and triage findings.
when_to_use: When the user asks for a security review, audit, or vulnerability check of this repo.
license: Apache-2.0
---
```

Constraints (SR-17, enforced by `t-plugin-lint`): no `` !`cmd` `` and no ` ```! ` blocks (dynamic-context execution runs before content reaches the model); no `allowed-tools` (it grants tools without prompting, flagged as a security warning even in `-p` in untrusted folders); body <500 lines; `description` + `when_to_use` ≤1,536 chars. The skill body instructs the model to call `mcp__vibeguard__vg.repo_trust` before reading `CLAUDE.md`/`AGENTS.md`/`README.md` in an unfamiliar repo.

Hooks (`hooks/hooks.json`) — the only surface that can actually block a tool call:

```json
{"hooks":{
  "SessionStart":[{"hooks":[{"type":"command","command":"${CLAUDE_PLUGIN_ROOT}/bin/vg trust . --tiers 1,2,4 --index-out .vg/trust-index.json --format json --quiet","timeout":45}]}],
  "PreToolUse":[{"matcher":"Read|Grep|Glob|Bash|WebFetch|Edit|Write","hooks":[{"type":"command","command":"${CLAUDE_PLUGIN_ROOT}/bin/vg hook --index .vg/trust-index.json","timeout":5}]}],
  "ConfigChange":[{"hooks":[{"type":"command","command":"${CLAUDE_PLUGIN_ROOT}/bin/vg hook --event ConfigChange --index .vg/trust-index.json","timeout":5}]}]
}}
```

```json
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny",
  "permissionDecisionReason":"VibeGuard: CLAUDE.md contains a Tier-1 hidden-instruction payload (VIBE-31, critical). Read blocked until quarantined. See .vg/out/report.md#vgf_41ab77cc."}}
```

Exit 2 blocks. Host decision precedence is deny > defer > ask > allow (defer only in `-p`); hook output is capped at 10,000 chars, so reasons truncate to 2,000 with a pointer to the report.

| Event | Condition | Decision |
|---|---|---|
| PreToolUse Read/Grep/Glob | target has a critical VIBE-30/31/32 finding | deny with decoded-payload summary |
| PreToolUse Read | target has a high injection finding | ask |
| PreToolUse Bash | command matches a decoded payload from the index (fetch-and-exec, secret path read, DNS utility) | deny |
| PreToolUse Write/Edit | target ∈ `.claude/**`, `.mcp.json`, `.vscode/settings.json`, `.cursor/**`, `.github/workflows/**` | ask |
| PreToolUse WebFetch | URL appears in a T2/T3 injection finding | deny |
| ConfigChange | any change to hooks/permissions/MCP config mid-session | ask + audit entry |
| any | index missing or stale (>24 h or HEAD changed) | ask (`trust_index_stale`) — never silent allow |

Caveats the plugin README MUST state: hooks run with full user permissions; `if` filters fail open; async hooks cannot enforce; Anthropic recommends the permission system for hard allow/deny, so the shipped `settings.json` snippet is the primary control and `vg-hook` is defense in depth. `-p`/SDK sessions skip the trust dialog and treat the folder as trusted, so CI must rely on our own trust stage. Portability: the same hook binary works in Cursor (`.cursor/hooks.json`; command hooks are fail-open unless `failClosed: true`, which we document as required), and the same MCP server works in Cursor, Codex and Copilot Chat.

## Error Handling

All errors derive from `VgError(code, kind, retryable, remediation)`:

| Kind | Example | Exit | Retryable | Behavior |
|---|---|---|---|---|
| UsageError | unknown flag, invalid config | 2 | no | print schema path + expected type; no partial artifacts |
| TargetError | path missing, clone failed, Windows native | 3 | sometimes | no artifacts |
| SandboxUnavailable | no bubblewrap/userns, WSL1 | 3 | no | refuse to run; suggest container; MUST NOT silently downgrade |
| ToolMissing / ToolDigestMismatch | binary absent or digest mismatch | 4 | no | abort (integrity) |
| ToolTimeout / ToolCrash / ToolOutputInvalid | hang, exit 137, truncated JSON | 0/1 | yes (1 retry) | stage → abstain, run continues |
| BudgetExceeded | wall clock, tokens, USD | 7 | no | partial artifacts + `"complete": false` |
| AiUnavailable / AiSchemaViolation | provider 5xx, off-schema output | 0/1 | yes (2 retries, jittered) | S6 abstains; deterministic results unaffected |
| NetworkDenied | egress attempt in offline mode | 4 | no | treated as bug or attack: abort, log, audit |
| IntegrityError | audit chain broken, SARIF write failure | 4 | no | abort; never emit a "clean" report |
| PermissionDenied | write to a deny-listed path | 2 | no | refuse; audit entry |
| RateLimited | GitHub 403/429 | — | yes | token bucket + backoff honoring `x-ratelimit-reset` |

Rules: every message states what failed, what was skipped, what to do next; failure is never silent success (skipped analysis becomes a visible abstention, also in SARIF `invocation.toolExecutionNotifications`); retries bounded/jittered/idempotent; partial results always written before exits 5, 6, 7, 130; stack traces only at `--log-level debug`.

## Failure Modes

| # | Failure | Detection | Mitigation |
|---|---|---|---|
| FM-1 | Scanner hangs on a pathological file | per-tool deadline | timeouts + `max_file_bytes` + surfaced abstention |
| FM-2 | Vuln DB stale/unavailable (429 mirrors) | DB age check in doctor + S3 | mirrored OCI DBs; `db_age_days` in report; abstain past `db_max_age_days` |
| FM-3 | Tool upgrade renames rules ⇒ suppressions stop matching | `suppression_unmatched` warning | key suppressions on CWE + glob + fingerprint, never rule ids |
| FM-4 | Injection FP floods a legit repo | benign corpus, FP budget ≤0.02 | triple-signature requirement + allowlists + severity capping |
| FM-5 | Injection bypass (whitespace inflation, `.pyc`, DOCX, LLM-targeted) | red-team corpus regression | whole-file inspection, post-whitespace regions, archive/bytecode traversal, no LLM in the decision path |
| FM-6 | LLM hallucinates a finding or unsafe patch | `source: ai` + verification gate | AI cannot gate/delete/approve; codemod-first; canary fixtures measure slop rate |
| FM-7 | Sandbox unavailable | startup capability probe | container path; `--i-accept-no-sandbox` refused when `VG_CI=1` |
| FM-8 | Sandbox escape via host-trusted component | not runtime-detectable | no exec in default profile; RO mount; no unix/Docker sockets; allowlists |
| FM-9 | Exfiltration via allowlisted egress (DNS, domain fronting) | proxy logs; INV-1 | no network in Analyzer; TLS-terminating allowlist; DNS utilities never allowlisted |
| FM-10 | Over-dedup collapses distinct findings | mutation tests + goldens | cluster-not-discard; keep all evidence; never dedup on line alone |
| FM-11 | SARIF exceeds GitHub caps | pre-upload size computation | deterministic truncation by `risk_score` + `truncated_count`; full JSON kept locally |
| FM-12 | Same tool+category uploaded twice per run | App/Action guard | unique category per analysis, asserted in CI |
| FM-13 | GHAS absent ⇒ 403 | HTTP status | fall back to Checks annotations (≤50/request) + Markdown |
| FM-14 | Rate-limit exhaustion | response headers | installation tokens; per-installation buckets; backoff |
| FM-15 | Audit chain broken | `vg audit verify` | exit 4; keep divergent file for forensics; never rewrite |
| FM-16 | Non-determinism | determinism e2e test | canonical sort by `(path, start_line, rule_id, fingerprint)`; timestamps only in run |
| FM-17 | AI cost blowout | token/USD counters | hard `budget_usd`, `max_calls_per_run`, exit 7 |
| FM-18 | Provider output format change | schema validation | schema-constrained outputs; version-pinned adapters |
| FM-19 | Upstream tool license change | license-audit CI + quarterly review | pinned versions; per-adapter license; adapter disableable |
| FM-20 | Repo rename/transfer redirects a pinned URL | digest pinning + doctor provenance check | pin by digest, not name/tag |
| FM-21 | Approver fatigue merges a bad patch | approval requires diff + gate verdict | no batch approval; UNVERIFIED labelled in the PR body |
| FM-22 | Repo config tries to weaken controls | `TIGHTEN_ONLY` enforcement | rejected + `config_override_rejected` + audit entry |

## Security Invariants

Each MUST be enforced in code and covered by a named test in `tests/invariants/`.

- **INV-1** Analyzer has no network namespace access: `socket(AF_INET|AF_INET6|AF_UNIX,…)` MUST fail.
- **INV-2** Analyzer env contains no credential-shaped variable and no path to a credential store; env is allowlist-built, never inherited.
- **INV-3** No repo-provided code, script, hook, build, install or container build executes in the default profile.
- **INV-4** Every subprocess uses an argv array, `shell=False`, an allowlisted binary and allowlisted argument patterns; no repo-derived string may occupy a flag position.
- **INV-5** The repository mount is read-only in every stage.
- **INV-6** git runs with `core.hooksPath=/dev/null`, `--no-recurse-submodules`, `protocol.ext.allow=never`.
- **INV-7** No stage holds both network access and repo-code execution; asserted at import time.
- **INV-8** T2/T3 content never reaches an LLM outside a single-level `<untrusted_data>` envelope whose terminator cannot be forged.
- **INV-9** The AI layer cannot delete/hide a deterministic finding, nor set `gate_blocking: true`.
- **INV-10** No finding with `source != "deterministic"` may be `gate_blocking`.
- **INV-11** The trust stage cannot be disabled by repository-supplied configuration.
- **INV-12** Injection detection inspects the whole file plus every region after a >1,000-char whitespace run; no fixed inspection window.
- **INV-13** Decoding is bounded: ≤4 passes, ≤8 MiB expanded per artifact.
- **INV-14** Secret plaintext never appears in any artifact, log or audit entry.
- **INV-15** `vg` never writes inside the user's tree except under `output.dir` and `.vg/`.
- **INV-16** Patches apply only in an ephemeral git worktree, never to the default branch.
- **INV-17** A patch touching any `fix.deny_paths` entry is rejected before authoring completes.
- **INV-18** No patch reaches VERIFIED unless every gate is pass/na and `poc_flipped != "fail"`.
- **INV-19** No generated credential is ever committed in a patch.
- **INV-20** Suppressions require a valid signature, reason ≥20 chars and an unexpired date; otherwise the finding re-surfaces.
- **INV-21** The audit log is append-only and hash-chained; `vg audit verify` detects mutation, truncation or reorder.
- **INV-22** Every external binary and DB is digest-verified before use; mismatch aborts with exit 4.
- **INV-23** In `--offline`, zero network syscalls occur across all processes.
- **INV-24** MCP write-classified tools are not advertised unless `mcp.allow_write: true`.
- **INV-25** MCP responses contain no raw T2/T3 prose outside a neutralized envelope, and no field exceeds its cap.
- **INV-26** The shipped Skill contains no shell-execution block and no `allowed-tools` key.
- **INV-27** `vg hook` decides using only the pre-computed trust index — no LLM, no network, no repo read beyond the index.
- **INV-28** A stale or missing trust index yields ask, never allow.
- **INV-29** Two runs over identical inputs produce byte-identical findings JSON (excluding the run block).
- **INV-30** No artifact, template or doc asserts that a repository is secure.
- **INV-31** No AGPL/GPL code is imported into the `vg` process; such tools run only as subprocesses.
- **INV-32** Symlinks resolving outside the repo root are never followed and are always reported.
- **INV-33** Every stage that fails, times out or hits a cap produces an explicit abstention; no analysis is silently skipped.
- **INV-34** The process runs unprivileged (`euid ≠ 0`); bubblewrap is never used in setuid mode.

## Development Phases

**Phase 0 — Foundations (weeks 1–2).** Repo skeleton, config loader + schema, Finding model, sandbox launcher (bwrap/Landlock/seccomp + Seatbelt), NDJSON channel, audit log, structured logging, `vg doctor`, CI with the invariant harness, digest pinning + OCI image. Acceptance: INV-1..7, 21, 22, 34 pass; `vg doctor --json` shows all tools digest-verified; empty-repo e2e yields a valid empty document.

**Phase 1 — Deterministic core, JS/TS + Python (weeks 3–5).** S0, S2, S3a–S3f, S3h, S4, S7, S9; adapters for Opengrep (+rule corpus v1), Trivy, Syft, osv-scanner, Gitleaks, zizmor, Checkov; provenance detector with offline index; SARIF/CycloneDX/Markdown writers; caching + `--diff`; `vg scan|sbom|deps|report|baseline|suppress`. Acceptance: golden-SARIF green; determinism green; NFR-1/2 met; OpenSSF CVE Benchmark recall published; INV-23 passes.

**Phase 2 — Trust & agent-hijack engine (weeks 4–6, overlapping).** S1 in full: inventory, normalization, decoders, Tier 1–4, MCP-config audit + TOFU diffing, trust index, `vg trust`, VIBE-30..35. Acceptance: corpus targets met; zero cases where corpus text alters engine behavior; INV-11..13, 32 pass.

**Phase 3 — Agent surfaces (weeks 6–8).** `vg-mcp` (stdio + HTTP) with five read-only tools; `vg-hook`; Claude Code plugin; GitHub Action; `docs/limitations.md`. Acceptance: `claude plugin validate --strict` passes; INV-24..28 pass; hook p95 ≤500 ms; MCP cold start ≤1.5 s; scripted hostile-repo session shows `Read(CLAUDE.md)` denied with a decoded-payload reason.

**Phase 4 — MVP hardening & release (weeks 8–10).** Fuzz/mutation/chaos; format-contract tests; honesty + license lints; benchmark harness; explain-only fix suggestions; OCI + PyPI release with Sigstore signatures and SBOM. Acceptance: AC-1..14 pass; limitations page carries measured numbers; self-scan clean.

**Phase 5 — V2 (post-MVP, ~10 weeks).** S8 in full (codemods, PoC/security-test harness, fix sandbox, verification gate, state machine, PR flow); correlation v2; GitHub App + Checks + SARIF upload; benchmark expansion (CWE-Bench-Java, AutoPatchBench-Lite, SEC-bench, muence vibesec, SecLLMHolmes, AgentDojo); Go + Java. Acceptance: verified-fix rate published; INV-16..19 pass; GHAS-403 fallback exercised; no patch reaches VERIFIED without all gates.

**Phase 6 — V3.** Multi-repo/org posture, AI-provenance attribution, real-time agent-loop guardrails, policy-as-code, VEX, dashboards, air-gapped enterprise packaging. Must not regress any INV.

## MVP Definition

**In scope (Phases 0–4):** `vg scan` (S0–S5, S7, S9) for JS/TS + Python, fully offline, sandboxed; repo trust / agent-hijack scan with VIBE taxonomy v1 (all 35 classes defined; detectors for VIBE-01..05, 09, 11, 13..16, 18..25, 27, 28, 30..35); the deterministic stack (Opengrep + first-party rules, Trivy, Syft, osv-scanner, Gitleaks, zizmor, Checkov, provenance; Scorecard present but disabled offline); correlation/dedup, risk engine, abstentions, signed suppressions, baselines, diff-aware caching; outputs (findings JSON, SARIF 2.1.0, CycloneDX 1.7, Markdown, evidence bundle, hash-chained audit log); `vg-mcp` read-only tools; `vg-hook` + Claude Code plugin + GitHub Action + OCI + PyPI; fix as explain + suggested diff only, unapplied; published `docs/limitations.md`.

**Out of MVP:** verification-first auto-fix + PoC harness; GitHub App/Checks/SARIF service; Go/Java; correlation v2; AI beyond optional triage/explain (default off); DAST; multi-repo posture; VEX; dashboards.

## Acceptance Criteria

- **AC-1** `vg scan ./fixtures/nextjs-fastapi --offline --format json` exits 0 and writes findings JSON validating against `finding-1.0.json`, SARIF validating against 2.1.0 and GitHub's caps, a CycloneDX 1.7 SBOM, and a Markdown report containing "Limitations & residual risk".
- **AC-2** Two consecutive runs produce byte-identical findings JSON excluding the run block (INV-29).
- **AC-3** With `--offline`, a syscall-level probe records zero network syscalls across all child processes (INV-23), and the run still yields SAST, secrets, SCA (mirrored DB), IaC, Actions and trust results.
- **AC-4** On the hostile fixture, `vg trust` reports `trust_label: hostile`, emits the expected VIBE-30/31/32/33 findings with decoded payloads, and `vg hook` denies `Read(CLAUDE.md)` with exit 2 and a reason ≤2,000 chars.
- **AC-5** Red-team corpus meets published targets (Tier-1 recall ≥0.95 / FP ≤0.02; Tier-2 ≥0.75 / FP ≤0.10) and zero corpus cases alter engine behavior.
- **AC-6** All 34 invariant tests pass; release refuses to publish if any is skipped or xfailed.
- **AC-7** Every adapter has an integration test on recorded output, a timeout test producing an abstention, an offline test, and a normalization test asserting non-empty `cwe[]`.
- **AC-8** `vg rules lint` passes with 100% of first-party rules carrying `cwe`, `vibe`, `owasp` metadata and a confidence prior; no rule sourced from `semgrep-rules`.
- **AC-9** Fuzz targets run 30 min in CI with zero crashes/hangs and no expansion beyond 8 MiB; mutation score ≥70% on `correlate.py`, `risk.py`, `trust/*`.
- **AC-10** Chaos: for each of ≥12 injected faults the run terminates with a documented exit code and a valid artifact set; no fault omits affected analysis without an abstention (INV-33).
- **AC-11** p50 ≤180 s and peak RSS ≤4 GiB on the 50k-LoC fixture at 4 vCPU / 8 GiB.
- **AC-12** `vg bench --suite ossf-cve-benchmark` and `--suite vg-injection` write metrics JSON, and those numbers appear verbatim in `docs/limitations.md` and every human report.
- **AC-13** MCP conformance: all five read-only tools validate against their schemas; write tools absent unless enabled; no raw T2 prose in responses; `claude plugin validate --strict` passes.
- **AC-14** Hygiene gates green: honesty lint, license audit (no AGPL/GPL in-process), SHA-pinned actions check, `vg audit verify`, Sigstore signature + SBOM on release artifacts, and a self-scan with no unsuppressed critical/high deterministic findings.

V2 adds AC-15 no patch reaches VERIFIED unless every gate is pass/na; AC-16 published verified-fix rate from AutoPatchBench-Lite and muence-vibesec; AC-17 App Checks + SARIF path exercised including the GHAS-403 fallback; AC-18 AgentDojo/InjecAgent robustness results published.

## Future Roadmap

| Horizon | Item | Notes |
|---|---|---|
| V2 | Verification-first auto-fix with PoC harness + PR flow | the core differentiator; gated by the S8 sandbox and codemod library |
| V2 | GitHub App + Checks API + code-scanning upload | Checks write is App-only; rate-limit headroom |
| V2 | Correlation v2: cross-file reachability, call-graph-weighted confidence | risk is scan time — two studies abandoned cross-file modes over runtime |
| V2 | Go + Java support | Java measured against CWE-Bench-Java |
| V2 | Public leaderboard of our own numbers | calibrated-honesty commitment |
| V2 | Cursor/Codex/Cline packaging of the same hook + MCP server | portability already designed in |
| V3 | Multi-repo/org posture + dashboards | needs a service tier and retention policy |
| V3 | AI-provenance attribution | research-stage; ship only with a measured accuracy number, else Unverified |
| V3 | Real-time agent-loop guardrails: egress proxy + signed action receipts | modeled on agent-firewall receipt patterns |
| V3 | Policy-as-code (CEL/Cedar-style) for gates and suppressions | mirrors mature SCA policy engines |
| V3 | VEX output + optional Dependency-Track backend | Dependency-Track is a server, not a scanner |
| V3 | Air-gapped enterprise packaging: mirrored DB bundles, signed update channel | Trivy/OSV already support the offline paths we rely on |
| Research | CaMeL-style capability-tracking dual-LLM execution | the paper's own limits apply; adopt only with measured utility cost |
| Research | Deterministic PoC synthesis for SQLi/XSS/SSRF to raise verified-fix rate | current post-verification rates are 5–15% |
| Not planned | DAST, exploitation tooling, default cloud scanning of customer source, IDE plugins | see Non-Goals |

**Residual-risk statement (reproduce in the README).** VibeGuard reduces risk; it does not eliminate it. Its scanners have measured recall far below 100% on real vulnerabilities, its injection detectors are triage signals that published research has repeatedly bypassed, its sandbox is a strong boundary but not a complete one, and its AI layer is non-robust under perturbation. Every finding carries a confidence and verification state, every skipped analysis is reported as an abstention, and every fix is labelled verified, candidate (unverified) or abstained.
