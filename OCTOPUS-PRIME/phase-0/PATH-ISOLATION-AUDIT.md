# PATH-ISOLATION-AUDIT — candidate tests/production vs live coupling

writer-verified (F-B agent failed schema; findings produced directly from source).

## اصل
CODE UNDER TEST = candidate repo فقط · TEST DATA = candidate/synthetic · LIVE = هرگز import، هرگز write.

## یافته‌ها (file:line)
| # | محل | coupling | resolve به live؟ | فیکس |
|---|---|---|---|---|
| 1 | `_ops/tests/harness.py:21` | `REAL_VAULT` پیش‌فرض `F:\backup` | بله (اگر env ست نشود) | runner همیشه `REAL_VAULT=candidate` می‌گذارد |
| 2 | `harness.py:83,89,91` | کپیِ studio config / ledger.py / prompts از `REAL_VAULT` | با REAL_VAULT=candidate → از candidate | حل‌شده (candidate کلونِ کاملِ tracked است) |
| 3 | `harness.py:108` | `SCRIPTS_DIR = REAL_VAULT/04.../scripts` | با REAL_VAULT=candidate → candidate | حل‌شده |
| 4 | `harness.py:116-121` | کدِ تحتِ تست از `SELF_OPS` (candidate) | **نه — درست است** | بدون تغییر |
| 5 | `test_phase0_safety_net.py:22` | `_OPS = harness.REAL_VAULT / "_ops"` → می‌خواند doctor.py/b4_fusion.py | با REAL_VAULT=candidate → candidate | حل‌شده via env؛ کاندیدای `test_import_roots` |
| 6 | config-reader tests (organ_table→budgets.yaml) | ORG_ROOT خالی → fallback به live budgets.yaml | آشکارشده در sandbox | runner یک `budgets.yaml` سنتتیک seed می‌کند |

## اثباتِ اجرا
full suite (۲۴۹/۲۴۹) با `REAL_VAULT=candidate` + `ORG_ROOT=sandbox` + barrier:
**suite_attempted_live_writes=0** (barrier معتبر، ۲۶۳ child). هیچ importِ production از `F:\backup`.

## توصیه (باقی، non-blocking)
افزودن `test_test_authority_import_roots.py`: assert هر production module `__file__` زیر
`F:\octopus-phase0-isolated` است، نه `F:\backup`. (candidate-safe، تستِ رگرسیونِ ایزوله.)
