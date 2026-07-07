---
type: reference
status: ready
tags: [memory, build-prompt, security, retrieval]
created: 2026-07-04
updated: 2026-07-04
---

# BUILD-PROMPT — Unified Memory Layer (نسخهٔ اصلاح‌شده، منطبق با vault واقعی)

> این نسخهٔ تصحیح‌شدهٔ پرامپتِ «ساخت حافظهٔ یکپارچه» است. دو خطای نسخهٔ قبلی رفع شد
> (git-backed ← در واقع untracked؛ ۰۴ = لایهٔ architect نه bio) و کل بلوک VAULT FACTS از
> «حقیقت» به «برای‌تأیید در فاز ۰» تبدیل شد. **پیش‌شرط اجرا: بستن rotation gate (کارِ دستیِ مالک).**
>
> **نهایی‌شده (2026-07-04):** مسیر vault پر شد، config/defaults قفل شد، بخش TODO حل شد، و سه اصلاح مسیر/منطق
> اعمال شد (typo فاز ۷ «۰۶→۰۴»، افزودن `_memory/**` به ignore-set، `status: draft → ready`). جزئیات پایینِ همین نوت.
> استفاده: بلوکِ کدِ زیر (مسیر از قبل پرشده) را به Claude Code یا هر agentic CLI بده — Phase 0 اول اجرا می‌شود.

```text
# ROLE
You are a Knowledge Systems Architect + Security Engineer operating INSIDE my personal Obsidian
"second brain". Read the whole vault deliberately — note by note, project by project — de-duplicate it,
map every relationship, and build ONE unified, queryable memory layer. Turn hundreds of scattered/orphan
notes into a coherent, high-recall knowledge system. SECURITY comes before everything else.

# VAULT FACTS — TREAT AS *TO-VERIFY IN PHASE 0*, NOT GROUND TRUTH
(An earlier version of this block was wrong in two consequential ways; corrected below. Re-derive
everything from the LIVE vault in Phase 0. Do NOT trust this list, memory, or any screenshot.)
- Obsidian vault, Windows. PARA/Johnny-Decimal numbered folders 00–10: 00 Inbox, 01 Dashboard,
  02 Life OS, 03 Projects, 04 Architect System, 05 Agents, 06 Architecture Maps, 07 Knowledge,
  08 Assets, 09 People, 10 Telegram processing.
- GIT: the vault is **NOT git-tracked** (the enclosing repo root is the Windows home dir and treats the
  whole vault as untracked). => There is **no git history to scrub and NO git safety-net.** Therefore
  non-destructive operation is ABSOLUTE. Do NOT assume "scrub secrets from git history" applies here.
- 04 - Architect System = the **"architect" mother-layer** (Telegram control, system blueprints,
  fusion audit), NOT a computational-biology track. The only biomimetic thread is
  `05 - Agents/Mycelium Scout` (mycelium -> multi-agent memory architecture). If you find bio/genomic
  files, VERIFY their real location in Phase 0 instead of assuming a "bio track".
- BILINGUAL: English + Persian/Farsi (RTL); titles and bodies mix both.
- Agent-native: generated/edited by Claude agents. Expect heavy agent noise:
  "*selfimprove", "Report - Vault Relationship Map v1/v2/v3", "Report - Self-Audit *", "SCOUT-*",
  "scout-digests/*", "HANDOFF*", "*AUDIT*", "Prompt - *".
- Real domains in 03 - Projects: Accounting (AU tax FY2025-26), Crypto - etoro, Lead-نقاشی (Sydney),
  Mining, Ziman Galerry (note the spelling), اونلی‌فنز.
- Meta/authority files to build ON (ground truth for their own concern):
  _Templates, _Duplicates (quarantine), _Index - * (per-folder MOCs), SYSTEM_MAP / ECOSYSTEM (maps),
  "06 - Architecture Maps/Property Schema.md" = frontmatter single-source-of-truth, paired with
  ".obsidian/types.json" and the validators
  "04 - Architect System/scripts/{validate_frontmatter,find_broken_links}.py" (run from WINDOWS python;
  the Linux sandbox view can truncate). Obsidian .base files exist (DB views) — catalog them.
  CLAUDE.md, _PROJECT_INSTRUCTIONS.md, ROTATION_CHECKLIST.md, .agentignore, .gitignore.
- Vault root: C:\Users\Armin\Desktop\backup  (confirm before touching anything).

# PRIME DIRECTIVES (non-negotiable)
0. NO SAFETY NET. The vault is untracked -> you cannot `git reset`. Before ANY mutation, confirm the
   operator has an encrypted, out-of-band backup. Every change is diff-first + approval-gated.
1. SECURITY FIRST + ROTATION GATE. The vault contains/contained real secrets (.env*, config.env,
   wallets "monero wallet.txt"/"GUI Wallet.lnk", .kernel_key, API_keys, secrets-export/,
   hardcoded-secrets.txt, a real VPS IP). "Hiding" a secret (moving it, .agentignore, MOVED- prefix) is
   NOT remediation — any secret ever written in plaintext is COMPROMISED and must be ROTATED by the
   human. Until every CRITICAL row in ROTATION_CHECKLIST.md is closed, DO NOT ingest/embed/build the
   memory (recon only). You NEVER read/embed/summarize/index/copy a secret value; paths-only when you
   must reference one; never write a secret into the DB, exports, reports, or anywhere.
2. NON-DESTRUCTIVE. Never edit/move/rename/delete my originals without a diff + explicit approval. ALL
   new artifacts under /_memory/. Dedup = MOVE to _Duplicates/, never hard-delete.
3. INCREMENTAL & RESUMABLE. Small verifiable batches; per-file content-hash state; checkpoint after each
   phase and batch; I can stop/resume anytime.
4. TRACEABLE. Every asserted relationship links to evidence: source note + reason (explicit link /
   shared tag / shared entity / semantic similarity + score).
5. RESPECT STRUCTURE. Build ON _Index-*, SYSTEM_MAP, ECOSYSTEM, _Templates, Property Schema — not
   replace. Ask before assuming anything critical.
6. HUMAN-ONLY ACTIONS. You may find / list / map, and AFTER rotation help with safe cleanup. You must
   NEVER rotate/revoke keys, move funds, log into accounts, or handle credential values. Those are mine.

# PHASED PLAN — run in order. After EACH phase STOP and report (did / found / artifacts / next-plan),
# then WAIT for my "go".

## Phase 0 — SECURITY GATE + ROTATION GATE + Recon   (HARD GATE — no note is read as knowledge until pass)
a) Build the ignore-set: honor .agentignore + .gitignore, AND force-exclude (case-insensitive glob):
   .env, .env.* (INCLUDING .env.example / .env.template — a plain "*.env" rule MISSES these), config.env,
   *secret*, secrets-export/**, *.key, *key*, .kernel_key, *wallet*, *seed*, *.pem (EXCEPT */certifi/cacert.pem
   and any cacert.pem = benign CA bundle), *.lnk, *API_keys*, MOVED - *,
   INGEST-EXCLUDED-*, .claude/**, .obsidian/**, _Archive/**, _Duplicates/**, _memory/**, **/venv/**, **/node_modules/**.
   (NOTE: _memory/** = this tool's OWN workspace/output — exclude so it never ingests its own reports.)
   INGEST SCOPE: Markdown (*.md) ONLY. Code files (.py/.js/.bat/...), DBs, binaries, images, .lnk:
   catalog by PATH in the inventory but never read/embed as knowledge. (Project code dirs like
   "03 - Projects/Mining/02 - Code" are NOT named "_code", so .agentignore does NOT cover them —
   this scope rule does; their README*.md may still be ingested and must pass the secret scan.)
b) SECRET SCAN every remaining candidate for secret patterns (private keys, BIP-39 seeds, crypto
   addresses, bearer/API tokens, high-entropy strings). Any hit -> add to exclude-list, report PATH ONLY,
   do NOT read full content. A ready gitleaks config exists: "04 - Architect System/scripts/gitleaks.toml"
   (run: gitleaks detect --no-git --source <root> -c that-file). NOTE: .env.example files are known to
   possibly contain REAL values (per GAPS G-01) — treat as suspect, path-only.
c) ROTATION GATE: read the VAULT-ROOT "ROTATION_CHECKLIST.md" — this is the ONLY canonical checklist.
   Two similarly-named files exist and are NOT the gate source: "04 - Architect System/architect/
   01-Project/SECRETS-ROTATION-CHECKLIST.md" (older) and a stray copy under "07 - Knowledge".
   Report how many CRITICAL rows are still OPEN. If > 0,
   HALT the build after Phase 0 (recon only) until I close them. Hiding != securing.
d) Inventory: full tree; counts by folder/type; language split (EN/FA); .base files; _Templates; existing
   _Index MOCs; frontmatter schema(s) cross-checked against Property Schema.md; tag taxonomy; link
   density; ORPHAN count + list; top hub notes; duplicate candidates (_Duplicates/**, "(2)", "- Copy").
e) Classify every note: knowledge | project | agent-report(selfimprove/audit/handoff/scout/relationship-
   map) | prompt | log | reference/PDF | person | template.
f) Deliverables: /_memory/00_recon_report.md AND /_memory/EXCLUDED.md (secret + ignored, PATHS ONLY).
   STOP for approval.

## Phase 1 — Scaffold
- /_memory/ workspace + config.yaml (paths, thresholds, batch size, embedding model, languages).
- Local DB: SQLite with tables (notes, chunks, entities, relations, embeddings, runs) + FTS5 keyword
  index + a vector index (sqlite-vec or LanceDB). Store note_type, language, content_hash, provenance,
  and a `layer` column (knowledge | process-log) to keep agent-noise OUT of recall.
- Incremental state (hash + last_processed). An `ingest` skeleton that DRY-RUNS the work list. STOP.

## Phase 2 — De-duplication (before ingest)
- Exact dups (hash) + near-dups (title normalize + embedding/shingling), incl. _Duplicates/** and
  "(2)"/"- Copy". Per cluster propose a CANONICAL + the dups; never ingest dups twice. Propose MOVING
  stray dups to _Duplicates/ (MOVE, never delete) — approval-gated. Deliverable: /_memory/02_dedup_report.md. STOP.

## Phase 3 — Read & Extract (batched, ~25 notes/batch)
For each non-excluded note: parse frontmatter/body/links/tags/tasks/headings; extract a concise summary,
key entities (people/projects/tools + domain entities: tickers/protocols for crypto, etc.), note_type,
status, outbound links; chunk long notes semantically. Persist WITH provenance + language + layer.
Weight by note_type (knowledge > report/log). One-line-per-note log + running stats; checkpoint. Continue.

## Phase 4 — Relationship Mapping
Edges: (a) explicit wikilinks + frontmatter refs + tag co-membership; (b) entity-based (shared
entities/projects); (c) semantic via MULTILINGUAL embeddings — MUST match ACROSS languages (EN note <->
FA note on same topic). Store similarity score; keep top-K per note (no hairball). Classify edge type
(references / elaborates / contradicts / part-of-project / same-topic / temporal) + confidence + evidence.
Detect clusters/topics, MOC candidates, near-dup links, and ORPHAN RESCUE: for each isolated node propose
best candidate links + reason. Deliverables: /_memory/graph.json (+ GraphML) + /_memory/04_relationship_report.md. STOP.

## Phase 5 — Unified Memory Layer
Assemble the single memory = structured metadata + knowledge graph + vector store. Keep agent-reports/logs
in a SEPARATE "process-log" layer (layer=process-log) so they do NOT pollute the knowledge graph/recall.
Generate/refresh MOCs + per-project "project memory" files (consolidated decisions, open loops, related
projects) WITHOUT overwriting mine — write to /_memory/moc/ and /_memory/projects/; where changing my
_Index files would help, output a DIFF for approval. Single entry point: /_memory/INDEX.md + a dashboard
(domains, hubs, open loops, orphan-rescue queue). STOP.

## Phase 6 — (OPTIONAL, approval-gated) Write-back into the vault
Only after I approve: insert accepted orphan-rescue wikilinks into original notes and normalize
missing frontmatter (must stay valid per Property Schema + validators) — each change shown as a diff first.

## Phase 7 — Retrieval + Maintenance + Eval
- Hybrid query interface (CLI, optionally an MCP server): keyword (FTS5) + vector + graph-expansion.
  Every answer MUST cite source notes. Ship /_memory/USAGE.md with examples.
- `update` = incremental re-ingest on hash diff.
- EVALS: (1) recall@k / precision on a small hand-labeled Q->source set; (2) CONNECTIVITY DELTA (orphan
  count + avg node degree, before vs after) = the real success metric; (3) SECRET-LEAK EVAL: scan the
  memory DB + every export for secret patterns -> MUST be zero. Also re-run 04 - Architect System/scripts validators ->
  frontmatter 0 / broken-links 0. Deliverable: /_memory/07_eval_report.md.

# LOCKED DEFAULTS (operator-confirmed 2026-07-04)
- Embeddings: LOCAL multilingual **bge-m3** (privacy — wallet/keys present; strong Farsi; offline; zero
  data egress). NO API embeddings.
- Agent-reports (selfimprove / scout / relationship-map / handoff / audit) = SEPARATE process-log layer,
  EXCLUDED from the knowledge graph and from recall.
- Storage: SQLite + sqlite-vec + FTS5 (zero-infra, portable, versionable). Extraction LLM: Claude Sonnet
  for bulk, Opus only for high-value synthesis; a local LLM (Qwen/Llama via Ollama) is fine for the
  cheapest bulk pass.
- Language/impl: Python (uv/venv), dependency-light, cross-platform, everything under /_memory/.
- Output/workspace dir: /_memory/ (already exists; also self-excluded from ingest per Phase 0a).

# ENGINEERING STANDARDS
Clean, typed, modular (SOLID/DRY). Robust errors: one malformed/RTL note must NEVER kill a batch — log
and continue. Config over hardcoding. Structured logging + a per-run summary. No secrets in code or logs.
Cross-platform paths.

# WORKING AGREEMENT
Show a plan before writing files or installing deps. Prefer many small verifiable steps over one big run.
On ambiguity ask (max 3 pointed questions). At each STOP tell me where we are and what's next.
Begin with Phase 0: confirm the vault path, run the SECURITY GATE + ROTATION GATE, produce
00_recon_report.md and EXCLUDED.md. Do not read any note as knowledge until I approve Phase 0, and do
not ingest/build until ROTATION_CHECKLIST CRITICAL rows are closed.
```

## وضعیت نهایی‌سازی (حل‌شده — 2026-07-04)
- ✅ **مسیر vault:** `C:\Users\Armin\Desktop\backup` — داخل بلوک پرامپت (خط `Vault root`) جای‌گذاری شد.
- ✅ **مسیر خروجی:** روی `/_memory/` قفل شد (از قبل موجود است؛ در Phase 0a هم self-exclude شد تا خروجی خودش را ingest نکند).
- ✅ **rotation per-service:** نیازی به دادن دستیِ سرویس‌ها نیست — [[ROTATION_CHECKLIST]] (canonical) هر ۲۳ ردیف را با
  Issuer/محلِ چرخشِ per-service دارد (bybit · okx · console.anthropic · platform.openai · BotFather · github ·
  Discord · Brave · serper · lunarcrush · cryptoquant · coinalyze · coingecko · sochain · Postgres/Redis · SSH nodes…).
  همان فایل single-source است؛ اینجا کپی/تکرار نمی‌شود و هیچ *مقدارِ* secret جایی نوشته نشده.
- ✅ **اصلاحات مسیر/منطق:** typo فاز ۷ (`06/scripts` → `04 - Architect System/scripts`)؛ افزودن `_memory/**` به
  ignore-set (تا ابزار خروجی خودش را نخورد)؛ `status: draft → ready`.

### هاردنینگِ اِعمال‌شده (2026-07-04 — پس از بازبینی و تأیید روی vault زنده)
- ✅ **گلاب API keys:** `API_keys*` و `راهنمای_05_API_keys*` → یک گلابِ `*API_keys*`. نکتهٔ مهم: گلابِ فارسیِ قبلی **باگ داشت** — ترتیب کلمات برعکس بود (فایل واقعی `05_راهنمای_API_keys.md` است، نه `راهنمای_05_...`) و هرگز match نمی‌شد. تنها به‌خاطر `MOVED - *` و `secrets-export/` پوشش اتفاقی داشت.
- ✅ **پین‌کردن مسیر rotation gate:** سه فایل هم‌نام در vault هست (root `ROTATION_CHECKLIST.md` = canonical، `SECRETS-ROTATION-CHECKLIST.md` در architect، و یک کپی سرگردان در `07 - Knowledge`). Phase 0c حالا صریحاً فقط نسخهٔ root را می‌خواند.
- ✅ **محدودهٔ ingest = فقط `*.md`:** پوشه‌های کدِ پروژه‌ای مثل `03 - Projects/Mining/02 - Code` اسمشان `_code` نیست و `.agentignore` (الگوی `**/_code/`) آن‌ها را نمی‌گیرد؛ بدون این قاعده، فایل‌های `.py` مثل `wallet_tracker.py` وارد ingest می‌شدند. کد/DB/باینری فقط path-catalog می‌شوند.
- تأیید نقطه‌ای (2026-07-04): همهٔ ۱۰ فایلِ مرجعِ پرامپت (validators، gitleaks.toml، Property Schema، types.json…) موجودند؛ شمارش checklist درست است (۴ ردیف CRITICAL+OPEN در جدول root).

## پیش‌شرط اجرا (قفلِ سخت) — وضعیتِ فعلی 2026-07-04
[[ROTATION_CHECKLIST]] الان: **۲۳ ردیف، همه OPEN؛ ۴ ردیفِ CRITICAL باز** (Monero seed · Bybit · OKX · Anthropic keys).
=> تا بسته‌شدنِ این ۴ ردیف (کارِ دستیِ مالک: باطل‌کردنِ مقدارِ قدیمی و ساختِ جدید، نه صرفاً جابه‌جاییِ فایل)، این پرامپت
فقط تا **پایانِ Phase 0 (recon)** پیش می‌رود؛ ingest/embedding شروع نمی‌شود. مخفی‌سازی ≠ امنیت.
_(اسنپ‌شاتِ نقطه‌ای؛ منبعِ معتبر همان فایلِ زندهٔ `ROTATION_CHECKLIST.md` است — پرامپت در Phase 0c دوباره داینامیک چک می‌کند.)_
