# TERRITORY-REPORT — 4D-Vault

findings: **10** · classes: OPEN_WORK 3 · DEBT_HIDDEN 3 · SEASON_LEFTOVER 2 · DOC_RUNTIME_DISCREPANCY 2

## top findings (rank order)

- **[4D-1] r7.0 SEASON_LEFTOVER** No recurring vault reindex: owner-only scheduling decision left open; chroma only manually touched since (2026-09-12, in
  - `4D-Vault/_RECONSTRUCTION-REPORT.txt` · `line 17: Not done, left as an owner decision: no recurring/scheduled reindex was`
- **[4D-3] r5.0 OPEN_WORK** MOC 'خودتنظیم‌گری و خودآگاهی' pinned status: seed - all 5 related notes (Governor/PulseCore/MycoCardium/Shadow Catalog/O
  - `4D-Vault/00-MOC/MOC-خودتنظیم‌گری-و-خودآگاهی.md` · `line 5: status: seed`
- **[4D-4] r5.0 OPEN_WORK** 46 broken wikilinks vault-wide; 22+ atomic notes of the 'SOG engineering grammar' (15 principles) wikified but never cre
  - `4D-Vault/07-تحلیل-پژوهش/سنتز-SOG-جامع.md` · `line 28: | [[shadow-observability]] | نشت حالت پنهان به مشاهدات |`
- **[4D-9] r5.0 DEBT_HIDDEN** Entire 4D-Vault is a chroma.sqlite3 reconstruction (last real content 2026-07-11/12); original Desktop vault never migra
  - `4D-Vault/_RECONSTRUCTION-REPORT.txt` · `line 4: 2026-08-06: reconstructed from 4d_system/outputs/chroma_db/chroma.sqlite3`
- **[4D-6] r4.8 DOC_RUNTIME_DISCREPANCY** Vault appendix provenance points to Desktop originals (4D/SOG-multiagent-handoff 2.md) that exist nowhere in F:/backup
  - `4D-Vault/09-پیوست‌ها/📄 متن-کامل-handoff.md` · `line 10: خلاصه‌ی ساختاریافته‌ی `4D/SOG-multiagent-handoff 2.md` (۴۰ کیلوبایت)`
- **[4D-10] r4.8 OPEN_WORK** MAS-Audit checklist promised a spec + implementation plan 'later' (بعداً) - never produced
  - `4D-Vault/07-تحلیل-پژوهش/MAS-Audit-Checklist.md` · `line 1: هم بعداً بشود از رویش spec و implementation plan ساخت`
- **[4D-5] r3.0 DOC_RUNTIME_DISCREPANCY** MOC-سیستم documents physical location as C:/Users/Armin/Desktop - stale; truth moved to F:/backup per PROJECT_STATE 2026
  - `4D-Vault/00-MOC/MOC-سیستم.md` · `line 62: C:/Users/Armin/Desktop/`
- **[4D-2] r2.8 SEASON_LEFTOVER** Uncommitted whitespace-only churn on 2 vault notes dated today (2026-09-15): half-finished season operation left dirty i
  - `4D-Vault/02-مدل-SOG/مدل-خطی-گاوسی.md` · `mtime 2026-09-15; git diff = 96 ins/96 del; empty with --ignore-cr-at-eol`
- **[4D-8] r2.8 DEBT_HIDDEN** Reconstruction corruption debt: 2,984 overlap trims left headers glued to math blocks (e.g. '$$## نمادها') throughout re
  - `4D-Vault/02-مدل-SOG/مدل-خطی-گاوسی.md` · `line 15: $$Y_t = b_t + \lambda \cdot s_t ...$$## نمادها`
- **[4D-15] r2.8 DEBT_HIDDEN** 97% of vault (2,975/3,055 files) is auto-generated 🔍 discovery dumps from daemon runs; curated atomic-vault vision burie
  - `4D-Vault/07-تحلیل-پژوهش/🔍-auto-physical-Damped-oscillator-20260711-085638.md` · `line 3: tags: ["کشف", "auto-generated", "physical:Damped-oscillator"]`

## coverage

- inventory files_total (md/json/txt ≤2MB): 3056
- read: 3012/3055 content-swept (98.6%)
- method: full regex sweep of all files (wikilinks, checkboxes, markers) + 16 deep reads
- excluded: 43 files (12 >2MB or malformed)
