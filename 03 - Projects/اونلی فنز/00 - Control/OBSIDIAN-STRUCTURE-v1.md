# 🗂️ Project-F — Obsidian Structure v1 (migration map, proposal-only)

> Created 2026-07-11. **No files moved yet.** This maps current scattered files into the
> new numbered folders. Moves happen only with owner verdict (PF-STRUCT verdict below).

---

## Target structure

```
اونلی فنز/
├── HOME.md                     ← dashboard (created)
├── PROJECT.md                  ← canonical live context (stays root)
├── README.md / INDEX.md        ← navigation (stays root)
├── PROJECT-F-CONTROL-MANIFEST.json ← golden contract (stays root)
├── 00 - Control/
├── 01 - Strategy/
├── 02 - Research/
├── 03 - Experiments/
├── 04 - Content Studio/
├── 05 - Acquisition/
├── 06 - Ops & Runtime/
├── 07 - Compliance & Privacy/
├── 08 - Partner (PII)/         ← 🔒 sensitive, local only
└── 09 - Archive/
```

---

## Proposed mapping (current → target)

| current | target folder |
|---|---|
| AGENT-CONTROL-INTERFACE.md | 00 - Control |
| CLAUDE.md | 00 - Control |
| RUNBOOK.md / REGISTRY.md / VERDICT_QUEUE.md | 00 - Control (or keep root + link) |
| project-master-reference.md | 01 - Strategy |
| docs/PROJECT-F-FULL-REPORT-2026-07-09.md | 01 - Strategy |
| research/DECISION-MATRIX-M2-2026-07-10.md | 01 - Strategy |
| research/THREAD-CLOSURE-D-2026-07-10.md | 01 - Strategy |
| research/ (rest) | 02 - Research |
| research-results/ (P1–P13) | 02 - Research |
| external-research-2026-07-05/ | 02 - Research |
| Knowledge_Base_Memory_Synthesis.md | 02 - Research |
| STATE-REPORT / integration rounds | 02 - Research |
| (new experiment logs) | 03 - Experiments |
| studio/ | 04 - Content Studio |
| drafts-awaiting-gate/ | 04 - Content Studio |
| docs/TELEGRAM-CONTENT-STUDIO-v1/v2 | 04 - Content Studio |
| docs/30-Faceless-Clips-ReadyToFilm.md | 04 - Content Studio |
| research/ACQUISITION-ENGINE-2026-07-05.md | 05 - Acquisition |
| research-results/P1,P2,P3,P5,P6,P7,P8,P9 | 05 - Acquisition |
| brain/ | 06 - Ops & Runtime |
| langar/ | 06 - Ops & Runtime |
| orchestrator.py | 06 - Ops & Runtime |
| external-research/06-opsec-legal.md | 07 - Compliance & Privacy |
| research/COMPLIANT-PLAYBOOK-M3 | 07 - Compliance & Privacy |
| پرسشنامه پارتنر - پاسخ‌های صبا.md | 08 - Partner (PII) |
| اونلی فنز.md (telegram log) | 08 - Partner (PII) |
| docs/architecture-blueprint-2026-07-04.md (older) | 09 - Archive (if superseded) |

---

## Safety notes

- Moving `.py` files can break imports (orchestrator, brain, studio, langar). Prefer:
  - keep code where it is, OR
  - move as a deliberate refactor with import fixes + tests.
- `08 - Partner (PII)` must never be summarized into root graph.
- Nothing here changes runtime behavior; it is filing only.

---

## Verdict needed

```yaml
PF-STRUCT-V1:
  question: "آیا اجازه انتقال واقعی فایل‌ها طبق این نقشه هست؟"
  options: [yes-all, yes-docs-only-not-code, no-keep-flat, later]
  default: later
  effect: "reorganize project into numbered Obsidian folders"
```

پیشنهاد امن: `yes-docs-only-not-code` — اول فقط سندها منتقل شوند، کد سرجایش بماند تا refactor جدا.
