---
type: design
project: "[[03 - Projects/VibeGuard/PROJECT]]"
status: draft
tags: [vibeguard, spec, chat-ingest]
created: 2026-08-17
updated: 2026-08-17
created_by: agent
source: chat-chunk-1-of-5
---

# Project Specification (تکهٔ ۱ از ۵ — از گفتگو)

> ورود 2026-08-17 از چت مالک. کنار [[../Project-Specification]] (نسخهٔ Downloads). این تکه تا Technology Stack است؛ بقیه با «ادامه».

**Product:** VibeGuard (`vg`) — an AI security-engineering engine for AI-generated / "vibe-coded" repositories.
**Spec version:** 1.0. **Spec date:** 2026-08-17.
**Audience:** an autonomous coding agent (Claude Code) + human maintainers. This document is the single source of truth.
**Branding constraint:** the engine MUST NOT depend on Anthropic model access to function, MUST NOT brand itself "Claude Code", and MUST NOT offer claude.ai login or rate limits to third parties — the Agent SDK terms prohibit all three ([Agent SDK overview](https://docs.claude.com/en/docs/claude-code/sdk/sdk-overview)).
**Honesty constraint:** no artifact, string, doc page or report may claim a repository is "secure", "100% safe", or "clean". Permitted vocabulary: risk reduction, residual risk, confidence, abstain, unverified.

Requirement IDs are stable and testable: `SR-n` (security), `FR-n` (functional), `NFR-n` (non-functional), `INV-n` (invariants), `AC-n` (acceptance). MUST / MUST NOT / SHOULD / MAY are RFC-2119.

## Product Goal

Build a **local-first, offline-capable, open-core security engine** that a developer or an agent can point at an untrusted repository and get back: (1) ranked, evidence-linked, deduplicated findings normalized to SARIF 2.1.0 + CWE, (2) an **agent-hijack / prompt-injection triage report** for repository content that AI coding agents auto-load, (3) a machine-verifiable SBOM and dependency-provenance verdict including hallucinated-package detection, and (4) optional **verification-first** fix proposals that are never auto-applied and never claimed safe without machine verification.

Primary deliverables, in dependency order:

1. `vg` — standalone deterministic engine + CLI (Python 3.12). **This is the product.** Runs fully offline.
2. `vg-mcp` — MCP server, read-only by default, primary agent-facing surface; MCP is the only surface natively consumable by Claude Code, Cursor, Copilot Chat, Codex and Cline ([Claude Code MCP](https://docs.claude.com/en/docs/claude-code/mcp), [Cursor MCP](https://cursor.com/docs/context/mcp), [Codex config](https://developers.openai.com/codex/local-config), [Copilot MCP](https://docs.github.com/en/copilot/how-tos/provide-context/use-mcp/extend-copilot-chat-with-mcp)).
3. `vg-hook` — stdio hook binary using the exit-code-2 / `permissionDecision: deny` contract. Hooks are the only Claude Code surface that can actually block a tool call ([hooks](https://docs.claude.com/en/docs/claude-code/hooks)); Cursor documents exit-2 deny as Claude-Code-compatible ([Cursor hooks](https://cursor.com/docs/agent/hooks)).
4. `vg-plugin` — Claude Code plugin as packaging/distribution wrapper (skill + subagent + hooks + `.mcp.json` + `bin/`).
5. `vg-app` — GitHub App (Checks write is App-only; installation tokens get 5,000–12,500 req/hr vs 1,000/hr for `GITHUB_TOKEN` — [Checks runs](https://docs.github.com/en/rest/checks/runs), [rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)), plus an Action fallback for air-gapped CI.

### Non-Goals

VibeGuard v1 MUST NOT ship: IDE plugins; DAST at scale / running the target app; cloud multi-tenant scanning of customer source; CI gating on SAST or LLM findings (best single tool detected **12.7%** of 165 real CVEs, seven tools combined missed **70.9%** — [Li et al., ESEC/FSE '23](https://sen-chen.github.io/img_cs/pdf/fse2023-sast.pdf); a Lund replication on 462 CVEs found file-level TP rates of **1.7–5.3%** — [Ansgariusson & Ståhl](https://lup.lub.lu.se/luur/download?func=downloadFile&recordOId=9189955&fileOId=9189961)); auto-applying patches or touching default branches, CI/CD, secrets or lockfile pins without explicit opt-in; claiming prompt-injection immunity (Anthropic: prompt injection "is far from a solved problem", 1% ASR "still represents meaningful risk" — [Anthropic](https://www.anthropic.com/news/prompt-injection-defenses)); live secret verification (also AGPL-3.0 in TruffleHog — [license](https://api.github.com/repos/trufflesecurity/trufflehog)).

## Problem Statement

1. **AI code fails security at a rate conventional SAST does not see.** On BaxBench, "62% of the solutions generated even by the best model are either incorrect or contain a security vulnerability" ([BaxBench](https://baxbench.com/)); a verified-patching corpus cites AI code as 61% functionally correct but only 10.5% secure ([arXiv:2512.03262](https://arxiv.org/abs/2512.03262), via [muence-ai/vibesec](https://github.com/muence-ai/vibesec)).
2. **SAST recall on real vulnerabilities is very low** (12.7% best single tool; 70.9% combined miss — [Li et al.](https://sen-chen.github.io/img_cs/pdf/fse2023-sast.pdf)); coarse file-level matching inflates apparent recall 3–6× ([Charoenwet et al.](https://arxiv.org/html/2407.12241v1)).
3. **Repositories are an active prompt-injection delivery channel, in the wild.** Unit 42 documents **22 distinct** indirect-injection techniques ([Unit 42](https://unit42.paloaltonetworks.com/ai-agent-prompt-injection/)); Snyk found injection in **36%** of 3,984 scanned agent skills ([ToxicSkills](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/)) and **392 confirmed injections in MCP tool descriptions** across ~10,000 developer environments ([Snyk](https://snyk.io/blog/agentic-development-security-ai-coding-risk/)). Rules-file backdoors were declared not-vulnerabilities by vendors ([Pillar](https://www.pillar.security/blog/new-vulnerability-in-github-copilot-and-cursor-how-hackers-can-weaponize-code-agents)).
4. **The leading AI reviewer is explicitly not hardened**: "This action is not hardened against prompt injection attacks and should only be used to review trusted PRs" ([claude-code-security-review](https://github.com/anthropics/claude-code-security-review)).
5. **Auto-fix claims are unreliable.** AutoPatchBench-Lite: ~60% generation success collapses to **5–11% post-verification**; Google's AI patching reported a **15% fix rate** ([Meta](https://engineering.fb.com/2025/04/29/ai-research/autopatchbench-benchmark-ai-powered-security-fixes/)).
6. **Dependency metadata is adversarially manipulable.** Against 11 obfuscation scenarios, Grype, OSV-Scanner, Dependabot and Snyk each failed **11/11**; Dependency-Check 6/11 ([Ivanova et al., ISC '24](https://cyberlab.usask.ca/papers/SCA_Tools_analysis__ISC24.pdf)). Nine SCA tools on one project reported between **17 and 332** vulnerable Maven deps ([Imtiaz et al.](https://arxiv.org/abs/2108.12078)).
7. **Licensing blocks the obvious build.** CodeQL CLI is restricted to OSS/academic use without paid GitHub Code Security ([LICENSE.md](https://github.com/github/codeql-cli-binaries/blob/main/LICENSE.md)); Semgrep *rules* may only be used internally and not redistributed ([rules license](https://semgrep.dev/legal/rules-license)). Hence Opengrep engine + first-party rules.
8. **Scanners in this space are bypassable.** Trail of Bits bypassed every tested agent-skill scanner via ~100,000-newline whitespace inflation, `.pyc` bytecode, DOCX-as-ZIP indirection, and prompt-injecting the LLM scanner itself ([CSA note](https://labs.cloudsecurityalliance.org/research/csa-research-note-ai-agent-skill-scanner-bypass-20260610-csa/)). These are mandatory test cases; our detectors are triage signals, not a security boundary.

## Threat Model

Assets: (A1) source code and secrets, (A2) operator model credentials and GitHub tokens, (A3) integrity of VibeGuard's outputs, (A4) host/CI runner, (A5) the user's agent session.

Trust boundaries: `untrusted repo content` → `Analyzer` (no network, no secrets) → `structured channel` → `Orchestrator` (secrets, allowlisted egress) → `host agent / GitHub`.

| ID | Adversary & entry point | Capability assumed | Primary mitigation |
|---|---|---|---|
| TM-1 | Malicious repo author via auto-loaded instruction files (`CLAUDE.md`, `AGENTS.md`, `.cursor/rules/*.mdc`, `.clinerules`, `.windsurfrules`, `copilot-instructions.md`, `SKILL.md` name/description, `.claude/settings.json`) | Text enters agent context before any user action ([CSA](https://labs.cloudsecurityalliance.org/research/csa-research-note-readme-instruction-injection-ai-coding-age/)) | S1 trust classification before any read-for-reasoning; T2 quarantine envelope; VIBE-30..34; hook deny |
| TM-2 | Same author via platform metadata (issue/PR bodies, HTML/invisible comments, titles, commit messages) | No write access needed; CamoLeak exfiltrated private code via PR description + GitHub's Camo proxy ([Legit](https://www.legitsecurity.com/blog/camoleak-critical-github-copilot-vulnerability-leaks-private-source-code)); GitLab Duo: "Every single one of these worked" ([Legit](https://www.legitsecurity.com/blog/remote-prompt-injection-in-gitlab-duo)) | Metadata is T2, never fetched into Analyzer; reported as findings |
| TM-3 | Concealment layer | Unicode Tags `U+E0000`–`U+E007F`, zero-width, bidi `U+202E`, homoglyphs, HTML comments/`data-*`/SVG CDATA, CSS hiding, KaTeX white text, multi-pass encodings, split payloads, ~100k-newline inflation ([Unit 42](https://unit42.paloaltonetworks.com/ai-agent-prompt-injection/), [CSA](https://labs.cloudsecurityalliance.org/research/csa-research-note-ai-agent-skill-scanner-bypass-20260610-csa/)) | Tier-1..3 detection with normalization + multi-pass decode + anti-truncation (INV-12) |
| TM-4 | Execution surfaces | `postinstall` credential theft ([GHSA-cxm3-wv7p-598c](https://github.com/nrwl/nx/security/advisories/GHSA-cxm3-wv7p-598c)); `pull_request_target` echoing PR title ([Nx postmortem](https://nx.dev/blog/s1ngularity-postmortem)); symlinks pulled by `gh pr checkout` at secret stores ([Orca](https://orca.security/resources/blog/roguepilot-github-copilot-vulnerability/)); git hooks; Docker socket | INV-3 no execution outside sandbox; INV-6 no git-hook execution; symlink refusal; zizmor/Checkov/Trivy |
| TM-5 | Attacker targeting VibeGuard's own agent | Analyzer output re-entering Orchestrator prompt as instructions; LLM scanners were downgraded by fake "corporate compliance policy" text ([CSA](https://labs.cloudsecurityalliance.org/research/csa-research-note-ai-agent-skill-scanner-bypass-20260610-csa/)) | T2/T3 envelope; LLM may never delete a deterministic finding nor approve a patch; AgentDojo/InjecAgent self-robustness gate |
| TM-6 | Exfiltration via allowlisted channels | DNS exfil through allowlisted `ping`/`dig` (CVE-2025-55284, [Embrace The Red](https://embracethered.com/blog/posts/2025/claude-code-exfiltration-via-dns-requests/)); domain fronting past TLS-blind proxies ([sandboxing](https://docs.claude.com/en/docs/claude-code/sandboxing)) | INV-1 Analyzer has no network namespace; default-deny TLS-terminating allowlist proxy in Orchestrator only |
| TM-7 | Argument injection into allowlisted binaries | Pre-approved commands with attacker-controlled args gave RCE in three production agents ([Trail of Bits](https://blog.trailofbits.com/2025/10/22/prompt-injection-to-rce-in-ai-agents/)); `sed` (CVE-2025-64755) and `$IFS` (CVE-2025-66032) bypasses in Claude Code | INV-4 argv-array-only, binary allowlist **and** per-binary argument allowlist, no shell interpolation |
| TM-8 | Sandbox escape via host-trusted components | Agent writes a file later executed by a trusted unsandboxed component (interpreter discovery, git fsmonitor, `.vscode` tasks, hook engines, Docker socket) ([Pillar](https://www.pillar.security/blog/the-week-of-sandbox-escapes)) | Read-only bind mount; no unix sockets; no Docker socket; deny-write to all agent-config paths |
| TM-9 | Supply chain of VibeGuard itself | Scanner DBs pulled from registries with 429 fallback ([Trivy DB](https://trivy.dev/docs/latest/configuration/db/)); tool renames follow redirects silently (`invariantlabs-ai/mcp-scan` → `snyk/agent-scan`); defensive tooling carries advisories (`sandbox-runtime` `GHSA-9gqj-5w7c-vx47`) | Digest-pinned binaries + mirrored DBs (SR-14); SBOM + Sigstore signing of our releases |
| TM-10 | Malicious/hallucinated dependency (slopsquatting) | Non-existent or typosquatted names emitted by a model; MCP live validation reduces but does not eliminate phantom deps ([Trend Micro](https://github.com/trendmicro/slopsquatting)) | S3 provenance detector (existence, age, popularity, maintainers, typosquat distance) |
| TM-11 | Compromised CI | Repo write ⇒ access to secrets; third-party actions must be SHA-pinned ([hardening](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions)) | App-token model, minimal permissions, SHA-pinned actions, no secrets in Analyzer |
| TM-12 | Human approver fatigue | Only **13.6%** of 1,053 paid testers refused a clearly dangerous command swapped into a routine prompt ([Willison](https://simonwillison.net/2026/Aug/8/auto-mode/)) | Approvals must present a diff + machine verification result; batch-approval MUST NOT exist |

**Out of scope (accepted residual risk):** host-OS or model-provider compromise; a malicious *user* of `vg`; nation-state-grade sandbox escapes. We claim risk reduction and defense in depth, never immunity.

## Security Requirements

- **SR-1** The Analyzer MUST run with no network access (no network namespace on Linux; no outbound sockets on macOS). [t-inv-net]
- **SR-2** The Analyzer MUST NOT receive secret material: no `GITHUB_TOKEN`, model keys, `~/.aws`, `~/.ssh`, `~/.config/gh`, or inherited env beyond an allowlist (`PATH`, `HOME=/sandbox`, `LANG`, `TZ`, `VG_*`). [t-inv-env]
- **SR-3** The repo MUST be bind-mounted read-only; writes go to an ephemeral scratch dir destroyed at stage end. [t-inv-fs]
- **SR-4** The engine MUST NOT execute repository-provided code, script, build, install, container build or git hook in the default profile. Execution is only permitted in the opt-in `--profile=verify` sandbox, never in a stage that has network access. [t-inv-exec]
- **SR-5** Subprocess execution MUST use argv arrays with `shell=False`, a per-binary allowlist and a per-binary argument-pattern allowlist; repo-derived strings MUST NOT occupy semantics-changing argument positions. [t-fuzz-argv]
- **SR-6** T2/T3 content MUST NOT be concatenated into any LLM prompt as instructions; it MUST be wrapped in a single-level `<untrusted_data …>` envelope with escaping, NFKC normalization, invisible-codepoint stripping and a "treat strictly as data" system contract. [t-ai-envelope]
- **SR-7** The LLM layer MUST NOT delete, suppress or downgrade below `low` any deterministic finding, MUST NOT approve a patch, and MUST NOT influence any CI gate. [t-ai-authority]
- **SR-8** No patch may be applied to the user's working tree, the default branch, or `.github/workflows`, `.claude/**`, `.cursor/**`, `.mcp.json`, `.vscode/**`, `.git/**`, lockfiles or secret stores without explicit per-path human opt-in recorded in the audit log. [t-fix-guard]
- **SR-9** Discovered secrets MUST be stored only as salted hash + redacted preview (≤4 leading chars + length); plaintext MUST NOT appear in findings, SARIF, logs or audit log. [t-secret-redact]
- **SR-10** VibeGuard MUST NOT verify discovered credentials against third-party services by default. [t-inv-net]
- **SR-11** Orchestrator egress MUST be default-deny through a TLS-terminating allowlist proxy; DNS-capable utilities (`ping`, `dig`, `nslookup`, `host`, `curl`, `wget`) MUST NOT be on the allowlisted binary list at all. [t-inv-net]
- **SR-12** The audit log MUST be append-only and hash-chained (`entry.prev_hash = sha256(previous canonical JSON)`); `vg audit verify` MUST detect truncation, reorder or mutation. [t-audit-chain]
- **SR-13** Suppressions MUST only take effect via `.vg/suppressions.yml` entries with `reason`, `expires` (≤180 days), `approver` and a detached signature; expired/unsigned entries MUST surface as `suppression_invalid` findings, never silently honored. [t-suppress]
- **SR-14** All external binaries and vuln DBs MUST be pinned by version **and** digest, mirrored locally and verified; digest mismatch MUST abort with exit 4. [t-supply-pin]
- **SR-15** MCP write-classified tools MUST be disabled unless `mcp.allow_write: true`; classification MUST appear in each tool description. [t-mcp-rw]
- **SR-16** `vg-mcp` MUST NOT return raw repository prose; T2/T3 excerpts MUST be neutralized (envelope + normalization + ≤2,000-char cap) and labelled `trust: T2|T3`. [t-mcp-neutralize]
- **SR-17** The shipped Skill MUST NOT contain `` !`cmd` `` or ```` ```! ```` execution blocks and MUST NOT request `allowed-tools` — dynamic-context execution runs before content reaches the model, and `allowed-tools` grants tools without prompting even in `-p` inside untrusted folders ([skills](https://docs.claude.com/en/docs/claude-code/skills)). [t-plugin-lint]
- **SR-18** All outputs MUST be reproducible from identical inputs and carry `tool_versions`, `rules_version`, `config_hash`, and for AI findings `model_id` + `prompt_hash`. [t-repro]
- **SR-19** Per-stage governors (wall-clock, CPU, RSS, max file size, total bytes, path depth, archive expansion ratio) MUST be enforced; a breach MUST produce `abstain`, never a silent pass. [t-governor]
- **SR-20** The engine MUST refuse to follow symlinks out of the repo root and MUST report them as VIBE-33. [t-symlink]
- **SR-21** No output may assert a repository is secure; a lint test MUST fail the build on forbidden phrases (`is secure`, `100% secure`, `no vulnerabilities`, `fully protected`, `guaranteed`). [t-honesty-lint]
- **SR-22** GitHub App permissions MUST be minimal (`Checks: write`, `Contents: read`, `Pull requests: write`, `Issues: read`, `Metadata: read`) — Apps have no permissions by default and changes re-prompt every installation ([choosing permissions](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/choosing-permissions-for-a-github-app)). [t-app-perms]
- **SR-23** Model I/O MUST be recorded as hashes plus redacted excerpts; raw source MUST NOT be persisted in telemetry or logs. [t-privacy]
- **SR-24** Detectors on decoded content MUST cap decode depth at 4 passes and expanded size at 8 MiB (decode bombs). [t-fuzz-decode]

## Functional Requirements

- **FR-1** `vg scan <path|url>` MUST run S0–S5, S7, S9 offline and emit findings JSON, SARIF 2.1.0, CycloneDX 1.7 SBOM and Markdown.
- **FR-2** JS/TS + Python in MVP; Go + Java in V2.
- **FR-3** `vg trust <path>` MUST produce instruction-file inventory, injection findings by tier, MCP config audit, lifecycle-script audit, workflow audit, symlink audit and `trust_label` ∈ `{clean_of_known_signals, suspicious, hostile, abstain}`.
- **FR-4** MUST detect hallucinated / non-existent / typosquatted dependencies via registry existence, first-publish age, download popularity, maintainer count and edit distance to popular names; offline mode uses a bundled popular-name index and marks verdicts `offline_partial`.
- **FR-5** MUST normalize every tool output to the internal Finding schema and SARIF 2.1.0, mapping each rule to ≥1 CWE and where applicable a VIBE-xx class.
- **FR-6** MUST correlate/deduplicate across tools, preserving every contributing tool in `evidence[]` (cluster, never discard).
- **FR-7** MUST compute the composite risk score and emit `risk_score`, `band`, plus separate `kev`, `epss_percentile`, `ssvc_decision`.
- **FR-8** MUST support `--diff <base>..<head>` with a content-addressed cache keyed on `(file_sha256, tool, tool_version, rules_version, config_hash)`.
- **FR-9** MUST support `--offline` with zero network syscalls, degrading explicitly (`offline_partial` / `abstain`), never silently.
- **FR-10** MUST emit `abstain` as a first-class outcome with machine-readable `abstain_reason`.
- **FR-11** `vg explain <finding_id>` MUST produce a file:line-cited explanation; AI-assisted output MUST be marked `source: ai`, `verification: unverified`.
- **FR-12** `vg fix propose <finding_id>` MUST produce a minimal unified diff in a sandboxed worktree, preferring deterministic codemods over LLM edits, and MUST NOT apply it.
- **FR-13** `vg fix verify <patch_id>` MUST run the verification gate (PoC flips, existing tests pass, rescan resolves the finding and introduces no new finding ≥ medium) and emit `verified: true|false|abstain` with evidence.
- **FR-14** `vg-mcp` MUST expose exactly the declared tools over stdio and streamable-HTTP.
- **FR-15** `vg-hook` MUST evaluate a `PreToolUse`-shaped JSON event on stdin and return deny/allow/ask (exit 2 = block) within 500 ms p95 using only the pre-computed trust index.
- **FR-16** `vg report` MUST render Markdown/HTML/SARIF from a stored run and MUST include "Limitations & residual risk" quoting measured detector performance.
- **FR-17** `vg baseline`/`vg suppress` MUST key signed suppressions on `(cwe, path_glob, fingerprint)` — never tool rule IDs, since Opengrep/Trivy/Checkov ship on 4–7-day cadences and renames would silently unsuppress.
- **FR-18** `vg bench` MUST run the benchmark harnesses and emit metrics JSON including abstention rate.
- **FR-19** `vg audit verify|export` MUST verify and export the hash-chained log.
- **FR-20** Action and App MUST upload SARIF (gzip+base64, ≤10 MB, unique `category`) and post a Checks summary; on GHAS-unavailable (403) fall back to Checks annotations in batches ≤50 ([code scanning API](https://docs.github.com/en/rest/code-scanning/code-scanning), [SARIF support](https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/sarif-support-for-code-scanning), [Checks runs](https://docs.github.com/en/rest/checks/runs)).
- **FR-21** Config from `.vibeguard.yml` (repo), `~/.config/vibeguard/config.yml` (user), `--config` (explicit); precedence explicit > repo > user > defaults; **repo config MUST NOT weaken any SR/INV control**.
- **FR-22** `vg doctor` MUST verify tool presence, versions, digests, DB freshness and sandbox capability.
- **FR-23** Every finding MUST have a stable fingerprint-derived `id`, reproducible across runs on unchanged code.
- **FR-24** Every human report MUST publish per-detector precision/recall/abstention from the last benchmark run (calibrated honesty).

## Non-Functional Requirements

- **NFR-1** `vg scan --offline` on a 50k-LoC JS/TS repo MUST complete in ≤180 s p50 on 4 vCPU / 8 GiB with S3 parallelized. (**Unverified** against third-party corpora — published per-tool runtime is `n.a.` for almost every tool.)
- **NFR-2** Peak RSS ≤4 GiB for repos ≤200 MiB; stream files, never load whole trees.
- **NFR-3** Single digest-pinned OCI image with all default scanners embedded, ≤1.5 GiB compressed.
- **NFR-4** `vg-mcp` stdio cold-start ≤1.5 s; tolerate client 5-min HTTP / 30-min stdio idle defaults and 5 reconnects ([MCP](https://docs.claude.com/en/docs/claude-code/mcp)).
- **NFR-5** SARIF stays under GitHub caps by construction: ≤10 MB gzipped, ≤25,000 results/run (top 5,000 effective), ≤1,000 locations/result, ≤20 runs/file; truncate deterministically by `risk_score` and record `truncated_count`.
- **NFR-6** No default-path dependency may be AGPL/GPL-linked in-process; GPL/LGPL tools are subprocess-only.
- **NFR-7** Deterministic: identical inputs+config ⇒ byte-identical findings JSON (excluding the timestamped `run` block).
- **NFR-8** Cache hit on an unchanged file MUST cut that file's scan cost ≥90%.
- **NFR-9** Python 3.12 only; no C-extension dependency lacking manylinux + macOS arm64 wheels.
- **NFR-10** ≥85% line / ≥75% branch coverage on `vg/core/**`; 100% of SR/INV assertions covered.
- **NFR-11** Structured JSON-lines logs with stable schema and `redaction_applied` flag.
- **NFR-12** Run unprivileged (no root, no setuid); bubblewrap in non-setuid/userns mode (setuid mode carries CVE-2026-41163 and CVE-2020-5291 — [advisories](https://api.github.com/repos/containers/bubblewrap/security-advisories)).
- **NFR-13** Semver on all public interfaces (Finding schema, CLI flags, MCP tool schemas, config schema).
- **NFR-14** All user-facing text English, ASCII-safe, never color-only severity.

## Architecture

Two processes, one DAG, strict layering. The **Rule of Two** is enforced structurally: never combine untrusted input + sensitive access + egress in one process ([Meta framing via Willison](https://simonwillison.net/2025/Nov/2/new-prompt-injection-papers/)).

```
                ┌────────────────────── ORCHESTRATOR (trusted side) ──────────────────────┐
                │ holds: model creds, GitHub token, egress via TLS-terminating proxy       │
                │ never reads repo files directly — only size-capped channel messages      │
 user/agent ──► │  CLI (vg) · MCP server (vg-mcp) · Hook (vg-hook) · App/Action adapters   │
                │  pipeline governor · correlation · risk engine · report/evidence writer  │
                │  AI layer (LLM calls; input = neutralized excerpts only)                 │
                └──────▲───────────────────────────────┬───────────────────────────────────┘
                       │ NDJSON over pipe (fd 3),      │ spawn (argv array, no shell)
                       │ 64 MiB cap, schema-validated  │ seccomp/landlock or bubblewrap/gVisor
                ┌──────┴───────────────────────────────▼───────────────────────────────────┐
                │ ANALYZER (untrusted side): NO network ns · NO secrets · repo RO mount     │
                │ scratch tmpfs · CPU/mem/time caps · runs scanner subprocesses             │
                │ S0 acquire · S1 trust · S2 inventory · S3 fan-out · S5 context build      │
                └──────────────────────────────────────────────────────────────────────────┘
```

Pipeline DAG (corrected from a linear pipeline: trust classification must precede any read of repo instructions; scanners fan out in parallel; execution and network never share a stage; fix is gated; budgets and abstain are explicit):

```
S0 Acquire ──► S1 Repo Trust & Agent-Hijack ──► S2 Inventory ──┬─► S3a Opengrep SAST ─┐
  (shallow clone, no hooks,      (must run first)   (+ Syft SBOM) ├─► S3b Gitleaks      │
   no submodule exec, caps)                                      ├─► S3c osv-scanner   │
                                                                 ├─► S3d Trivy         ├─► S4 Correlate/Dedup ─► S5 Context build
                                                                 ├─► S3e Checkov       │        │
                                                                 ├─► S3f zizmor        │        └────► S6 AI Analysis (optional, neutralized)
                                                                 ├─► S3g Scorecard*    │                    │
                                                                 └─► S3h Provenance    ┘                    ▼
                                                                                          S7 Risk engine ──► S8 Fix pipeline (opt-in, sandboxed)
                                                                                                                  │
                                                                                          S9 Report + evidence bundle + audit log
* Scorecard needs a token/network → skipped in --offline, emits abstain.
```

Layer split: deterministic-only decisions are secrets, dependency vulns, IaC/Actions misconfig, invisible-character detection, package existence, license, SBOM, fingerprints, and **all gating decisions**. AI-assisted (never authoritative): business logic, authz/tenancy, architecture, cross-file data-flow hypotheses, intent mismatch, FP triage, fix authoring, explanation.

## Components

| Component | Path | Responsibility | Trust side |
|---|---|---|---|
| `vg` CLI | `vg/cli/` | Args, config resolution, run lifecycle, exit codes, output writers | Orchestrator |
| Pipeline governor | `vg/core/pipeline.py` | DAG scheduling, budgets, cancellation, abstain propagation, caching | Orchestrator |
| Sandbox launcher | `vg/core/sandbox/` | Analyzer jail (bubblewrap/landlock/seccomp, macOS Seatbelt), mounts, env scrubbing, rlimits | Orchestrator |
| Analyzer runtime | `vg/analyzer/` | Runs S0,S1,S2,S3,S5 in-jail; emits NDJSON | Analyzer |
| Scanner adapters | `vg/scanners/<tool>.py` | Invoke, parse, normalize, CWE/VIBE map, timeout, offline behavior | Analyzer |
| Trust engine | `vg/trust/` | Instruction inventory, normalization, decoders, Tier1–4, MCP audit, labeling | Analyzer |
| Provenance engine | `vg/provenance/` | Registry existence/age/popularity/typosquat, malicious-package heuristics | Analyzer (offline) / Orchestrator (online) |
| Correlation engine | `vg/core/correlate.py` | Fingerprints, purl+alias joins, clustering, agreement scoring | Orchestrator |
| Risk engine | `vg/core/risk.py` | Composite score, bands, KEV/EPSS/SSVC | Orchestrator |
| AI layer | `vg/ai/` | Envelope prompts, provider abstraction (BYO/local), schema-constrained output, authority limits | Orchestrator |
| Fix engine | `vg/fix/` | Codemods, LLM patch authoring, worktrees, verification gate, state machine | Orchestrator + sandbox |
| Report/evidence | `vg/report/` | SARIF, CycloneDX, MD/HTML, evidence bundle, Sigstore signing | Orchestrator |
| Audit log | `vg/audit/` | Hash-chained JSONL, redaction, verify/export | Orchestrator |
| `vg-mcp` | `vg/mcp/` | MCP server (stdio + HTTP), schemas, read-only default | Orchestrator |
| `vg-hook` | `vg/hook/` | PreToolUse decision binary; trust index only | Orchestrator |
| GitHub App | `services/app/` | Webhooks, Checks, SARIF upload, PR comments, tokens | Orchestrator |
| Action | `integrations/action/` | Thin wrapper over the OCI image | Orchestrator |
| Plugin | `integrations/claude-plugin/` | Skill (no exec), subagent, hooks.json, `.mcp.json`, `bin/vg` | Distribution only |
| Rules corpus | `rules/` | First-party Opengrep rules + VIBE detectors (no `semgrep-rules`) | Data |
| Benchmarks | `bench/` | Harnesses + metrics | Dev only |

## Repository Structure

```
vibeguard/
├── pyproject.toml                # Python 3.12, hatchling, strict mypy/ruff
├── README.md                     # measured-performance table + honesty statement
├── LICENSE  NOTICE  SECURITY.md  # Apache-2.0 own code; LGPL/GPL subprocess notices
├── .vibeguard.yml                # we dogfood our own config
├── docs/{architecture,threat-model,finding-schema,cli,mcp,invariants,limitations}.md
├── vg/
│   ├── cli/{main,cmd_scan,cmd_trust,cmd_explain,cmd_fix,cmd_report,cmd_sbom,
│   │        cmd_baseline,cmd_suppress,cmd_audit,cmd_bench,cmd_doctor,cmd_rules,
│   │        cmd_mcp,cmd_hook,output}.py
│   ├── core/
│   │   ├── pipeline.py stage.py budget.py cache.py errors.py
│   │   ├── correlate.py risk.py fingerprint.py taxonomy.py
│   │   ├── models.py config.py
│   │   └── sandbox/{launcher,linux_bwrap,linux_landlock,macos_seatbelt,limits,env}.py
│   ├── analyzer/{entry,s0_acquire,s1_trust,s2_inventory,s3_fanout,s5_context,channel}.py
│   ├── scanners/{base,opengrep,trivy,syft,osv_scanner,gitleaks,zizmor,checkov,
│   │             scorecard,gosec,bandit,hadolint,cargo_audit,sarif_in}.py
│   ├── trust/{inventory,normalize,decoders,tier1_signals,tier2_semantics,
│   │          tier3_markup,tier4_structural,mcp_config,label}.py
│   ├── provenance/{registry,typosquat,heuristics,offline_index}.py
│   ├── ai/{provider,envelope,prompts/,triage,authz_map,explain,authority}.py
│   ├── fix/{codemods/,author,worktree,statemachine,verify,poc}.py
│   ├── report/{sarif,cyclonedx,markdown,html,bundle,sign}.py
│   ├── audit/{log,verify,redact}.py
│   ├── mcp/{server,tools,schemas/,neutralize}.py
│   └── hook/{main,index,decision}.py
├── rules/{opengrep/{js,ts,python,go,java}/**.yaml, vibe/VIBE-*.yaml,
│          injection/{tier1,tier2,tier3}.yaml,
│          mappings/{cwe,owasp2025,llm_top10,agentic_top10}.yaml}
├── services/app/{main,webhooks,checks,sarif_upload,tokens,queue}.py
├── integrations/{action/{action.yml,entrypoint.sh},
│                claude-plugin/{.claude-plugin/plugin.json,
│                              skills/vibeguard-review/SKILL.md,
│                              agents/vg-triage.md, hooks/hooks.json, .mcp.json},
│                docker/{Dockerfile,tool-manifest.json}}
├── bench/{harness.py,cwe_bench_java/,ossf_cve_bench/,secllmholmes/,autopatchbench/,
│         agentdojo/,injection_corpus/,metrics.py}
├── tests/{unit,integration,e2e,fuzz,mutation,chaos}/ golden/sarif/** corpus/injection/**
│         invariants/test_inv_*.py
└── .github/workflows/{ci,release,selfscan}.yml   # all actions SHA-pinned
```

## Technology Stack

| Concern | Choice | Rationale / constraint |
|---|---|---|
| Language | Python 3.12 | scanner ecosystem is subprocess-based anyway |
| CLI | Typer + Rich (TTY only; never in `--format json`) | deterministic machine output |
| Models | pydantic v2 + generated JSON Schema | Finding schema is a published contract |
| Concurrency | `asyncio` + bounded process pool for S3 | governor needs cancellation |
| SAST engine | **Opengrep** LGPL-2.1, subprocess, `--sarif-output` | Semgrep *rules* license bars redistribution/service use ([rules license](https://semgrep.dev/legal/rules-license)); Opengrep is the LGPL fork ([repo](https://github.com/opengrep/opengrep), [InfoQ](https://www.infoq.com/news/2025/02/semgrep-forked-opengrep/)) |
| Rules | First-party corpus | MUST NOT vendor `semgrep-rules` |
| SCA/misconfig/containers | **Trivy** Apache-2.0 | one binary, 4 scanner classes, JSON+SARIF, documented air-gap path ([reporting](https://trivy.dev/docs/latest/configuration/reporting/), [air-gap](https://trivy.dev/docs/latest/advanced/air-gap/)) |
| SBOM | **Syft** Apache-2.0 | binary-level corroboration demanded by the SCA-evasion study |
| Vuln matching (2nd opinion) | **osv-scanner** Apache-2.0 | only tool with an explicit offline guarantee + native SARIF 2.1.0 ([output docs](https://google.github.io/osv-scanner/output/)) |
| Secrets | **Gitleaks** MIT | best measured F1 0.60 / recall 0.88 of nine tools ([Basak et al.](https://bradreaves.net/publication/bcrw23/bcrw23.pdf)) |
| Actions audit | **zizmor** MIT (`--format=json-v1`, we wrap to SARIF) | best-maintained Actions auditor; SARIF not documented ([usage](https://docs.zizmor.sh/usage/)) |
| IaC | **Checkov** Apache-2.0 (`-o sarif`) | broadest IaC coverage, complements Trivy misconfig |
| Repo posture | **OpenSSF Scorecard** Apache-2.0 | answers "should I trust this repo at all" |
| Tier-2 (opt-in) | gosec, Bandit (SARIF wrapper), hadolint (GPL-3.0 subprocess only), cargo-audit | per-language depth |
| Excluded | CodeQL CLI, semgrep-rules, Brakeman, SonarQube, TruffleHog (default), npm audit, Socket CLI, detect-secrets, Nosey Parker, Terrascan, tfsec, KICS, Grype, ZAP, sqlmap | license traps, archived/superseded, cloud-token/egress requirements, or full duplication |
| Sandbox | Linux: bubblewrap (non-setuid) + Landlock + seccomp, optional gVisor/microVM; macOS: `sandbox-exec` | mirrors the pattern of [`sandbox-runtime`](https://github.com/anthropic-experimental/sandbox-runtime); we do not depend on it as a library (its own `GHSA-9gqj-5w7c-vx47` network-escape advisory) |
| Egress proxy | TLS-terminating allowlist proxy, Orchestrator only | hostname-only TLS-blind proxies permit domain fronting ([sandboxing](https://docs.claude.com/en/docs/claude-code/sandboxing)) |
| Output formats | SARIF 2.1.0, CycloneDX 1.7 (ECMA-424), SPDX 3.0 alt, in-toto attestation, Sigstore | per standards research |
| Container | Debian slim, non-root UID 10001 | NFR-3/NFR-12 |
| CI | GitHub Actions, third-party actions pinned to full commit SHA | tags are movable ([hardening](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions)) |

---

پایان تکهٔ ۱ از ۵. تکهٔ ۲ با فرمان «ادامه».
