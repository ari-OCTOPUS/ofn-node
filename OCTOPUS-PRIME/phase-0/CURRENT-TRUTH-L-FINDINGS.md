# CURRENT-TRUTH — architect live findings L-01..L-08 (verified against the INDEPENDENT repo)

هر مورد مستقل علیه `F:\octopus-phase0-isolated` (candidate) با file:line تأیید شد.
منبع = بازبینی مستقیم source توسط writer (نه پذیرش گزارش subagent).

| # | یافته | تأیید علیه candidate | وضعیت | اقدام |
|---|---|---|---|---|
| L-01 | `test_durable_journal.py` تستِ معتبر **SCRIPT_STYLE** است، نه phantom | `run_all.py:215-217` صراحتاً «دیگر phantom/قرمز نیست ... ثبت شد (direct-run)» | ✅ CONFIRMED | quarantine نکن؛ subprocess direct-run |
| L-02 | `run_all.py` runnerِ ناهمگنِ موجود دارد | `run_all.py`: `TESTS` (direct-run) · `PYTEST_TESTS`(6، خط 284) · `EXTRA_TESTS`(خط 279) · هر فایل subprocess+timeout=300 | ✅ CONFIRMED | manifest از همین بساز، نه pytest-collect-all |
| L-03 | `harness.py` به live وابسته است (داده) | `harness.py:21` REAL_VAULT پیش‌فرض `F:\backup`؛ کپی از live: `ledger.py`(89)، prompts(91-94)، studio config(83)، `SCRIPTS_DIR`→live(108). **اما** کدِ تحتِ تست از candidate می‌آید (SELF_OPS، 116-121) | ✅ CONFIRMED | **REAL_VAULT را به candidate اشاره بده** (clone کاملِ live است) → داده هم از candidate؛ barrier backstopِ نوشتن |
| L-04 | `test_phase0_safety_net.py` source زنده می‌خواند | `:22` `_OPS = harness.REAL_VAULT / "_ops"`؛ `:118,127` `doctor.py`/`b4_fusion.py` از آن می‌خواند | ✅ CONFIRMED | با REAL_VAULT=candidate خودکار حل می‌شود؛ + تستِ import-root |
| L-05 | کدِ **زندهٔ** `F:\backup` هنوز آسیب‌پذیر است | candidate patchها (`8b61aa0`,`88d07f2`) merge نشده‌اند | ✅ CONFIRMED | production اصلاح‌نشده — merge NOT AUTHORIZED |
| L-06 | `test_stop_contract` مسیرِ STOP را canonical assert نمی‌کند | `:32-33` فقط نامِ «HALT-ALL»/«STOP-ORGANISM» را چک می‌کند؛ `:52` `getattr(opslib,"STOP",None)` | ✅ CONFIRMED | تست باید `opslib.STOP_ARCHITECT` را assert کند |
| L-07 | Memory/Outcome components از قبل هستند | `run_all.py`: `test_memory_gate`,`test_outcome_spine`,`test_decision_receipt`,`test_event_spine`,`test_verdict_outcome` + `_ops/memory/gate.py` | ✅ CONFIRMED | ممیزی/consolidate، نه بازنویسی از صفر |
| L-08 | Memory Gate trust escalation (claimant-controlled) | `_ops/memory/gate.py:121` `if candidate.get("external_graded") is True:` — bool<br>ادعاکننده trust را ارتقا می‌دهد (نه grader مستقل) | ✅ CONFIRMED **CRITICAL** | candidate-fix: `external_graded` بولینِ ادعاکننده را reject کن؛ GRADED فقط با receipt مستقل؛ + تست‌های security |

## جمع‌بندی معماریِ کلید (writer)

مسیرِ ایزوله‌سازی **ساده‌تر و قوی‌تر از fixture-از-صفر** است:
1. `REAL_VAULT = F:\octopus-phase0-isolated` (candidate) — harness داده را از candidate می‌کشد نه live.
2. `ORG_ROOT/OPS_DIR/STATE_DIR/...` → sandbox temp per-run.
3. **barrier sitecustomize** = backstopِ سختِ نوشتن (هر write زیر `F:\backup` بلاک + ثبت).
4. secretها scrub؛ شبکه بلاک؛ subprocess-per-file (احترام به قراردادِ pytest-vs-direct در `run_all.py`).

این هر دو L-03 و L-04 را می‌بندد بدون بازنویسیِ داده‌ها، چون candidate یک clone کاملِ tracked است.
