---
type: base-data-report-addendum
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
created: 2026-07-12
updated: 2026-07-12
created_by: fugu-ultra
parent_report: "[[BASE-DATA-REPORT-2026-07-12]]"
tags: [project-f, base-data, addendum, obsidian, audit]
aliases: ["Project-F Base Data Addendum", "تکمله گزارش دیتای پایه Project-F"]
---

# BASE DATA REPORT ADDENDUM — Project-F / اونلی فنز

> تکملهٔ گزارش پایه پس از خواندن فایل‌های باقی‌مانده. این فایل باید همراه با [[BASE-DATA-REPORT-2026-07-12]] خوانده شود.

---

## 1. Additional Files Read After Main Report

```text
architecture-blueprint-2026-07-04.md
TELEGRAM-CONTENT-STUDIO-v1.md
TELEGRAM-CONTENT-STUDIO-v2.md
research-track-BC-2026-07-04.md
research-prompts-lead-generation.md
DECISIONLOG-ENTRIES-M4-2026-07-10.md
اونلی فنز.md
پرسشنامه پارتنر - پاسخ‌های صبا.md
external-research-2026-07-05/*
research/ACQUISITION-ENGINE-2026-07-05.md
research/RESEARCH-INTEGRATION-round2-2026-07-10.md
research/STATE-REPORT-2026-07-05.md
orchestrator.py
brain/archive.json
brain/hebb_orch.json
_inbox-other-projects/self-improvement-root-map.md
```

Binary / media / non-text:

```text
_inbox-other-projects/Ziman_DM_Bot_Package.docx — inventoried only, not parsed.
media/test files — not opened or interpreted.
```

---

## 2. Additional Findings

### 2.1 `architecture-blueprint-2026-07-04.md`

This is a key operational blueprint, not just a strategy note. It contains:

- GATE 0 logic and Branch A/B consequences.
- G0→G4 phased gating model.
- Day-Zero infrastructure checklist.
- Agreement/message templates.
- Clear warning that GATE 0 must close before any outward execution.

**OS implication:** It should be treated as one of the primary governance inputs, but still `draft/proposal` until human verdict.

### 2.2 Telegram Content Studio v1/v2

`TELEGRAM-CONTENT-STUDIO-v2.md` supersedes v1 and defines the creator-facing Studio surface:

- metadata-only workflow
- no raw media
- self-cert checklist
- two-key flow: creator submits → Ari approves
- separate token/chat-id from Langar
- scope/boundary halt

**OS implication:** v2 should be the canonical design for creator-facing Telegram UI. v1 should become historical/superseded.

### 2.3 `research-track-BC-2026-07-04.md`

Track B/C evidence says:

- payment/banking path is conditionally viable if compliant
- Track B = GO conditional
- Track C = GO limited
- DM automation inside OF is not the current automation target
- safest automation is content hygiene, scheduling, analytics

**OS implication:** automation should focus first on internal pipeline and measurement, not external messaging.

### 2.4 `DECISIONLOG-ENTRIES-M4-2026-07-10.md`

This is a ready-to-paste decision entry set and reportedly already applied to `DecisionLog.md`. It gives a structured source for:

- decision matrix rule
- compliant-only playbook
- balance-withdrawal proposal
- AI cost cap proposal
- EXT-04 pricing proposal

**OS implication:** convert this into a normalized `VerdictQueue` + `DecisionLog` schema.

### 2.5 Sensitive files

`پرسشنامه پارتنر - پاسخ‌های صبا.md` contains consent/boundary/self-report information and should remain internal. It must be used as an evidence pointer, not copied into cross-domain reports.

`اونلی فنز.md` is a historical Telegram log and includes financial-looking notes. It should remain internal and not be surfaced in general dashboards.

### 2.6 Runtime state issue: `studio/drafts.json`

Current `studio/drafts.json` contains many pending draft rows with test-like titles such as `title`, `t`, `draft-003`, `draft-004`, `عنوان`. Earlier docs claim a cleanup/reset happened, but the current file still contains many pending entries.

**OS implication:** treat current `studio/drafts.json` as polluted test state until owner approves:

```yaml
recommended_action: quarantine_or_reset_candidate
external_effect: none
approval_required: true
```

### 2.7 `orchestrator.py`

`orchestrator.py` is a full loop tying together:

```text
neural → brain → acquisition → hebbian → consolidation → comm → studio
```

It imports vault-level `_ops/neural` modules:

```text
neural_driver
hebbian
consolidation
sprint
hooks
circadian
```

**OS implication:** this is not standalone Project-F code; it depends on the larger OCTOPUS/vault runtime. Do not run unless full vault dependencies are verified.

---

## 3. Updated Canonical Priority Stack

Recommended load order for future Project-F OS agents:

```text
1. _memory/onlyfans-project-memory-2026-07-05.md
2. PROJECT-F-CONTROL-MANIFEST.json
3. CLAUDE.md
4. PROJECT.md
5. HOME.md
6. INDEX.md
7. AGENT-CONTROL-INTERFACE.md
8. architecture-blueprint-2026-07-04.md
9. ACQUISITION-ENGINE-2026-07-05.md
10. THREAD-CLOSURE-D-2026-07-10.md
11. DecisionLog.md
12. OpenQuestions.md
13. BASE-DATA-REPORT-2026-07-12.md
14. BASE-DATA-REPORT-ADDENDUM-2026-07-12.md
```

---

## 4. Updated Issues Register

| Issue | Severity | Evidence | Recommended handling |
|---|---:|---|---|
| Desktop path not directly accessible | Medium | allowed dir only `F:\backup` | user must confirm backup path is correct or expose Desktop path |
| GATE 0 still open | Critical | PROJECT/HOME/blueprint | no outward execution |
| `studio/drafts.json` test pollution | High | current JSON state | quarantine/reset after approval |
| Duplicate research/root/docs copies | Medium | folder tree/read pass | canonical map before moving |
| `orchestrator.py` external dependency | Medium | imports `_ops/neural` | do not run standalone |
| partner questionnaire sensitive | High | sensitive consent file | pointer-only in reports |
| historical Telegram log contains financial-looking notes | Medium | `اونلی فنز.md` | keep internal |

---

## 5. Updated Next Action

Before scaffold/migration, ask one decision:

```text
Is `F:\backup\03 - Projects\اونلی فنز` the correct synced copy of the Desktop octopus-puzzle / 03 project / onlyfans folder?
```

If yes: create `00-Control/` scaffold and move this report into it only after link validation and owner approval.

If no: connect Desktop or sync the Desktop folder into allowed directory first.
