# D6 — ابزار سنجش canonical · 2026-08-20T00:28+10:00

> **ERRATA 2026-08-20:** ادعای STABLE در §K=9 زنده باطل است. حکم جاری `BETWEEN_RUN_VARIANCE` — [[D6-BETWEEN-RUN-VARIANCE-2026-08-20]]. ابزار canonical همین فایل است؛ D6 علمی بسته نیست.

R16/R17 · MEGA-DISCOVERY-v1 · paid re-run: none

## حکم

**منبع اجرایی تنها:** `_ops/measure/swap_consistency.py`

هر import / classify / ReliabilityGate برای سنجش جایگاه باید از همین مسیر بیاید.

## شواهد وجود (LAW-23)

| فایل | size | sha256 | نقش |
|---|---:|---|---|
| `_ops/measure/swap_consistency.py` | 10636 | `8c2f76dccd6ca38715c4f4e1667dbd8042c03a04f15186a37579a8b590851944` | **CANONICAL** |
| `_ops/tests/test_swap_consistency.py` | 3711 | `db3cdbff63113e23ede44486eefa7d68bd617cdf2f5580b9e9153ee912ab7bee` | تست · نه ابزار دوم |
| `F:/backup-island/teams/B-daemon-loop/swap_consistency.py` | 5764 | `deef9961cbb8fd1b1ec3ea5593ad21ab5217dc84b4fe0c86cf6ba122d76c9a6b` | **RETIRED** (آستانه متفاوت) |
| نسخهٔ پنل (ادعای تاریخی) | — | — | **NEVER_ON_DISK** |

git blob (canonical): `4eb15ea3c17d1198289fd3b422aa3d1443f93d69`
commit معرفی: `568016ed1dcc32b5ec51efcf5602c4f22dd32378` (2026-08-19 23:58 +10)
HEAD at GATE-0: `5a1c22de8e6b89049e9ca4c79b8ebc4eb53d36e3`

pytest: `_ops/tests/test_swap_consistency.py` → **12 passed** in 1.06s · 2026-08-20T00:26+10 · grade VERIFIED_BY_TESTS (نه VERIFIED علمی).

آستانه‌های منجمد canonical (`SwapConfig` frozen): `rs_min=0.9` · `alpha=0.005` → `min_k_for_alpha=9` · Wilson z=1.96.

آستانه‌های جزیره (رقیب، بازنشسته): `rs_min=0.8` · `alpha=0.05` · `k_min=9` هاردکد — **همان ابزار نیست.**

## runner پولی ≠ ابزار دوم

`_ops/measure/judge_pilot.py` طبقه‌بند نیست؛ `from measure.swap_consistency import classify_swap` می‌کند. R17 را نقض نمی‌کند اگر فقط همین classify صدا شود.

## K=9 زنده (از قبلِ این سشن — تکرار نشد)

path: `_ops/state/pipeline/pilot-k9-result-20260820T001141.json`
method: judge_pilot --run · seed `k9-pilot-20260819` · 20 calls · model deepseek-v4-flash
result: verdict CONSISTENT · RS_AB=1.0 · RS_BA=1.0 · voids 0 · grade MEASURED
budget: `_ops/state/pipeline/pilot-k9-budget.json` cap AU$1 · max_calls 30

**جنازهٔ روش:** ۹ فراخوان AB همه `text_sha=8fbedba22667454c`؛ ۹ فراخوان BA همه `text_sha=7c071c875fae5ac6`. یعنی K=9 مستقل نیست — دو پاسخِ قطعی (temp=0 + prompt ثابت) ۹ بار کپی شده. Wilson 9/9 = [0.7008, 1.0]؛ کران پایین < rs_min=0.9. گیت نقطهٔ 1.0 را STABLE می‌گذارد. کالیبراسیون ادعا نمی‌شود.

## بازنشستگی (حذف نشد — R6)

جنازه: `_ops/state/measure/retired-instruments.jsonl` + بنر روی فایل جزیره.
