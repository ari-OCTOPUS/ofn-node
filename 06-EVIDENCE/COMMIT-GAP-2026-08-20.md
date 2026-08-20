# COMMIT GAP — ac8b3d9 overclaimed cap30 source

created: 2026-08-20T12:15+10:00
related: ac8b3d9
this_commit_message: `agent-checkpoint: cap30 source files (follow-up to ac8b3d9)`

## Claim vs contents

`ac8b3d9` message: `agent-checkpoint: B1 signed-after-the-fact + cap30 restart verified + C-042`

`git show --stat ac8b3d9` (17 files): HANDOFF, CONTRADICTIONS, B1 signing card/payload/sig, K9 pre-reg, PROJECT.md, C-042 note, restart baseline, genome ledger tip, phase-gates. **نه** `budgets.yaml`، **نه** `_ops/heart/life_currency.py`، **نه** `_ops/tests/test_life_currency_units_safety.py`.

پس پیام «cap30 restart verified» روی سورسِ cap30 در git دروغ است. تاریخ بازنویسی نشد (no amend / no rebase). این follow-up فقط leftover را اضافه می‌کند.

## کدام فایل در کدام کامیت

| فایل | ac8b3d9 | این follow-up |
|---|---|---|
| `_ops/budget/budgets.yaml` (`life_currency_daily_cap: 30.0`) | غایب | همین کامیت |
| `_ops/heart/life_currency.py` (`UNIT` / `credits_to_aud` / `money_path`) | غایب | همین کامیت |
| `_ops/tests/test_life_currency_units_safety.py` | غایب (untracked) | همین کامیت |
| `06-EVIDENCE/COMMIT-GAP-2026-08-20.md` | غایب | همین کامیت |
| C-042 note / CONTRADICTIONS C-042 | **داخل ac8b3d9** (نسخهٔ پیش از ERRATA مالک #۲) | نه اینجا |
| restart baseline / B1 card | داخل ac8b3d9 | نه اینجا |

## بازرسی قبل از add

- `git diff budgets.yaml`: فقط `1000.0` → `30.0` + سه خط کامنت UNIT=life_credit. کلید تازه نیست. فیلد از-قبل-موجود `gmail_client_secret: ''` در HEAD خالی است و در این diff نیست.
- `git diff life_currency.py`: `UNIT`/`MONEY_PATH`/`credits_to_aud` fail-closed + دو کلید در `plan()`. secret نیست.
- تست: فقط allocate_beat / import-graph. `tokens` اینجا فیلد سهم است نه API token.

ABORT نشد.

## عمداً در این کامیت نیست

شواهد T7/T8/T10/T11/T12 و تست کف آفلاین و HANDOFF این نشست — کامیت دوم `agent-checkpoint:` بعد از T12.
