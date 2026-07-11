---
type: control
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: idea
created: 2026-07-12
updated: 2026-07-12
created_by: agent
sources:
  - "[[00 - Control/CARTOGRAPHY-2026-07-12|CARTOGRAPHY-2026-07-12]]"
  - "[[00 - Control/SOURCE-OF-TRUTH-MATRIX|SOURCE-OF-TRUTH-MATRIX]]"
  - "[[00 - Control/OBSIDIAN-STRUCTURE-v1|OBSIDIAN-STRUCTURE-v1]]"
tags: [project-f, migration, obsidian, control]
aliases: ["Project-F Migration Map"]
---

# MIGRATION-MAP — Project-F (staged — ⛔ اجرا نشده)

> نقشهٔ اجراییِ یک‌کلیکه. **اجرا فقط بعد از verdict ‏`PF-STRUCT-V2` (پایین).** جایگزین دقیق‌ترِ OBSIDIAN-STRUCTURE-v1 است (آن سند dedup را نمی‌دید). طرح پوشه: **همان `00–09` موجود** — canonical اعلام شد.

## قیود سخت (از code deep-read)

1. **پوشهٔ پروژه rename/جابه‌جا نشود** — `orchestrator.py` عمق مسیر `…/03 - Projects/<project>/` را hardcode-فرض می‌کند.
2. **کد جابه‌جا نشود:** `brain/` · `langar/` · `studio/` · `orchestrator.py` سرجایشان می‌مانند (انتقال = refactor جدا با اصلاح import + تست).
3. حذف مطلقاً ممنوع — فقط انتقال (`_Duplicates` / `09 - Archive`).
4. هر batch با `git mv`؛ قبل از شروع `agent-checkpoint:` commit؛ بعد از هر فاز هر دو validator.

## فاز ۱ — retire آینه‌ها (کم‌ریسک‌ترین، بیشترین سود)

```text
# ۱۳ فایل byte-identical → _Duplicates (با حفظ مسیر) + ثبت در «_گزارش تکراری‌ها.txt»
docs/PROJECT-F-BRAIN-SPEC.md
docs/PROJECT-F-FULL-REPORT-2026-07-09.md
docs/TELEGRAM-CONTENT-STUDIO-v1.md
docs/TELEGRAM-CONTENT-STUDIO-v2.md
research/ACQUISITION-ENGINE-2026-07-05.md
research/COMPLIANT-PLAYBOOK-M3-2026-07-10.md
research/DECISION-MATRIX-M2-2026-07-10.md
research/DECISIONLOG-ENTRIES-M4-2026-07-10.md
research/PROMPTS-2026-07-05.md
research/RESEARCH-INTEGRATION-round1.md
research/RESEARCH-INTEGRATION-round2-2026-07-10.md
research/STATE-REPORT-2026-07-05.md
research/THREAD-CLOSURE-D-2026-07-10.md

# ۹ snapshot کهنه/encoding → 09 - Archive/mirrors-2026-07/
docs/MASTER-BUILD-2026-07-04.md
docs/Feet-Content-Business-Master-Playbook.md
docs/MONETIZATION-EXPANSION-2026-07-04.md
docs/architecture-blueprint-2026-07-04.md
docs/Fable5-Build-Spec.md
docs/Content-Topics-Trends-2027.md
docs/30-Faceless-Clips-ReadyToFilm.md
research/research-prompts-lead-generation.md
research/research-track-BC-2026-07-04.md

# سپس پوشه‌های خالی docs/ و research/ حذفِ پوشه (خالی) — فایل حذف نمی‌شود
```

## فاز ۲ — بایگانی کد مرده (پس از grep نهایی «هیچ importer»)

```text
brain/dual_brain.py            → 09 - Archive/code-2026-07/
studio/studio_telegram.py      → 09 - Archive/code-2026-07/
studio/studio_telegram_v3.py   → 09 - Archive/code-2026-07/   # spec آن را fallback می‌داند — اگر مالک fallback بخواهد، بماند
studio/drafts.json.bak         → 09 - Archive/state-2026-07/
# project_f_brain.py فعلاً می‌ماند (spec-canonical) — سرنوشتش تصمیم معماری است، نه filing
```

## فاز ۳ — filing اسناد root به پوشه‌های شماره‌دار (git mv + آپدیت لینک)

```text
00 - Control/    ← AGENT-CONTROL-INTERFACE.md · RUNBOOK.md · REGISTRY.md · VERDICT_QUEUE.md
                   · DecisionLog.md · OpenQuestions.md
                   (PROJECT.md، CLAUDE.md، HOME.md، INDEX.md، README.md، MANIFEST.json در root می‌مانند — entry point)
01 - Strategy/   ← project-master-reference.md · MASTER-BUILD-2026-07-04.md
                   · architecture-blueprint-2026-07-04.md · MONETIZATION-EXPANSION-2026-07-04.md
                   · DECISION-MATRIX-M2-2026-07-10.md · THREAD-CLOSURE-D-2026-07-10.md
                   · Feet-Content-Business-Master-Playbook.md
02 - Research/   ← research-results/ · external-research-2026-07-05/ · RESEARCH-INTEGRATION-round1.md
                   · RESEARCH-INTEGRATION-round2-2026-07-10.md · STATE-REPORT-2026-07-05.md
                   · research-prompts-lead-generation.md · research-track-BC-2026-07-04.md
                   · Knowledge_Base_Memory_Synthesis.md (frontmatter → status: archived، stale)
03 - Experiments/← Fable5-Build-Spec.md · drafts-awaiting-gate/kpi-dashboard-spec.md
04 - Content Studio/ ← drafts-awaiting-gate/ (بقیه) · Content-Topics-Trends-2027.md
                   · 30-Faceless-Clips-ReadyToFilm.md · TELEGRAM-CONTENT-STUDIO-v1.md (تاریخی) · v2.md
05 - Acquisition/← ACQUISITION-ENGINE-2026-07-05.md · COMPLIANT-PLAYBOOK-M3-2026-07-10.md
                   · PROMPTS-2026-07-05.md · DECISIONLOG-ENTRIES-M4-2026-07-10.md
06 - Ops & Runtime/ ← brain/BRAIN-BENCHMARK-2026-07-10.md (فقط سند) · PROJECT-F-BRAIN-SPEC.md
                   · PROJECT-F-FULL-REPORT-2026-07-09.md — کد سرجایش + یادداشت لینک
07 - Compliance & Privacy/ ← external-research-2026-07-05/06-opsec-legal.md
                   + سند جدید OPSEC-ITEMS.md (دو گاف: نامِ C در شناسه‌های سورس؛ blocklist خالی)
08 - Partner (PII)/ 🔒 ← «پرسشنامه پارتنر - پاسخ‌های صبا.md» · «اونلی فنز.md» → rename «TELEGRAM-LOG.md»
                   · test/*.jpg (۸ عکس) → 08 - Partner (PII)/media/
خارج پروژه       ← _inbox-other-projects/Ziman_DM_Bot_Package.docx → «03 - Projects/Ziman Galerry/» (inbox)
                   · _inbox-other-projects/self-improvement-root-map.md → «00 - Inbox» vault
```

## فاز ۴ — پس از هر فاز

```text
python "04 - Architect System/scripts/validate_frontmatter.py"
python "04 - Architect System/scripts/find_broken_links.py"
# آپدیت INDEX.md/HOME.md/_INDEX.mdها به مسیرهای جدید · commit «agent-checkpoint: PF migration phase N»
```

## جدا (verdict مستقل — ORANGE)

```yaml
PF-STATE-RESET-V1:
  question: "reset «studio/drafts.json» به [] ؟ (۲۴۴ ردیف ۱۰۰٪ fixture تستی؛ bak=۶۰۸ آرشیو می‌شود)"
  options: [yes, no, later]
  default: later
```

## ▶️ بلوک اجراییِ آماده (Phase 1+2 + reset + foreign) — کپی/اجرا پس از approve

> این بلوک reversible است (فقط انتقال، هیچ حذف). ایجنت در auto-mode اجازهٔ اجرای دسته‌ایِ mv را نگرفت؛ مالک یا ایجنتِ دارای اجازهٔ Bash اجرا کند. **کد جابه‌جا نمی‌شود جز ۳ فایلِ مردهٔ تأییدشده (zero importer).**

```bash
cd "F:/backup"
P="03 - Projects/اونلی فنز"
DUP="_Duplicates/03 - Projects/اونلی فنز"; ARC="_Archive/Projects/اونلی فنز/mirrors-2026-07-12"
ST="_Archive/Projects/اونلی فنز/state-2026-07-12"; CODE="_Archive/Projects/اونلی فنز/dead-code-2026-07-12"
mkdir -p "$DUP/docs" "$DUP/research" "$ARC/docs" "$ARC/research" "$ST" "$CODE" "03 - Projects/Ziman Galerry/_inbox"

# Group A — 13 byte-identical → _Duplicates
for f in docs/PROJECT-F-BRAIN-SPEC.md docs/PROJECT-F-FULL-REPORT-2026-07-09.md docs/TELEGRAM-CONTENT-STUDIO-v1.md docs/TELEGRAM-CONTENT-STUDIO-v2.md \
  research/ACQUISITION-ENGINE-2026-07-05.md research/COMPLIANT-PLAYBOOK-M3-2026-07-10.md research/DECISION-MATRIX-M2-2026-07-10.md \
  research/DECISIONLOG-ENTRIES-M4-2026-07-10.md research/PROMPTS-2026-07-05.md research/RESEARCH-INTEGRATION-round1.md \
  research/RESEARCH-INTEGRATION-round2-2026-07-10.md research/STATE-REPORT-2026-07-05.md research/THREAD-CLOSURE-D-2026-07-10.md; do
  git mv "$P/$f" "$DUP/$f" 2>/dev/null || mv "$P/$f" "$DUP/$f"; done

# Group B — 9 stale/encoding mirrors → _Archive
for f in docs/MASTER-BUILD-2026-07-04.md docs/Feet-Content-Business-Master-Playbook.md docs/MONETIZATION-EXPANSION-2026-07-04.md \
  docs/architecture-blueprint-2026-07-04.md docs/Fable5-Build-Spec.md docs/Content-Topics-Trends-2027.md docs/30-Faceless-Clips-ReadyToFilm.md \
  research/research-prompts-lead-generation.md research/research-track-BC-2026-07-04.md; do
  git mv "$P/$f" "$ARC/$f" 2>/dev/null || mv "$P/$f" "$ARC/$f"; done

# Dead code (zero importers verified) → _Archive
for f in brain/dual_brain.py studio/studio_telegram.py studio/studio_telegram_v3.py; do
  git mv "$P/$f" "$CODE/$(basename $f)" 2>/dev/null || mv "$P/$f" "$CODE/$(basename $f)"; done

# Polluted runtime state → archive + reset (drafts.json is a JSON list)
mv "$P/studio/drafts.json" "$ST/drafts-2026-07-12.json"; mv "$P/studio/drafts.json.bak" "$ST/drafts-2026-07-12.json.bak"
printf '[]' > "$P/studio/drafts.json"

# Foreign files out of Project-F
mv "$P/_inbox-other-projects/Ziman_DM_Bot_Package.docx" "03 - Projects/Ziman Galerry/_inbox/"
mv "$P/_inbox-other-projects/self-improvement-root-map.md" "00 - Inbox/"

# remove now-empty dirs (only if empty)
for d in "$P/docs" "$P/research" "$P/_inbox-other-projects"; do [ -z "$(ls -A "$d" 2>/dev/null)" ] && rmdir "$d"; done

# validate
python "04 - Architect System/scripts/validate_frontmatter.py" | tail -3
python "04 - Architect System/scripts/find_broken_links.py" | tail -3
```

**رول‌بک:** `git status` → هر انتقال با `git mv <dest> <src>` برمی‌گردد؛ drafts با بازگرداندن `$ST/drafts-2026-07-12.json`.

## Verdict این نقشه

```yaml
PF-STRUCT-V2:
  supersedes: PF-STRUCT-V1
  question: "اجرای این MIGRATION-MAP (فقط اسناد؛ کد سرجایش)؟"
  options: [yes-phase1-only, yes-phases-1-2, yes-all-doc-phases, no, later]
  default: later
  rollback: "git revert کامیت‌های agent-checkpoint هر فاز"
```
