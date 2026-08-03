# 01 — BASELINE TESTS · ۲۰۲۶-۰۷-۳۱

## اجرای کامل (پیش از هر ویرایش کد)

```text
command   python -X utf8 run_all.py
cwd       <worktree>\_ops\tests
env       ORG_ROOT/REAL_VAULT/OCTOPUS_VAULT_ROOT = worktree
          OCTOPUS_STATE_DIR/OPS_STATE_ROOT = worktree\_ops\state
          OCTOPUS_STATE_ROOT = worktree\_octopus\state
          GENOME_DIR = worktree\07 - Knowledge\genome-system   (پینِ اجباری — opslib:43)
          PYTHONIOENCODING = utf-8
tree      HEAD = f2fceee (ce35f61 + دو کامیتِ نجات؛ پیش از هر patch)
suites    399 (397 TESTS + 2 EXTRA)
result    exit 1 · 36 سوییت قرمز · 363 سبز
leakage   صفر — GENOME/STATE پین‌شده تأییدی (سطر اولِ لاگ)؛ فایلِ تازهٔ
          ledger ِ زنده نویسنده‌اش schedulerِ خودِ ارگانیسمِ در حالِ اجرا بود
artifact  scratchpad\baseline_run_all.log (3.5k+ خط)
```

نکته: پیش از نجاتِ ۴۳ تستِ بی‌گیت، baseline ‏۴۳ قرمزِ **ساختگی** (file-not-found)
اضافه می‌داشت؛ نجات قبل از baseline انجام شد تا شمارش حقیقت باشد.

## طبقه‌بندی ۳۶ قرمز (خودکار + راستی‌آزمایی نمونه‌ای)

### CONFLICTED — ۲۹ سوییت
تست یا سوژه‌اش نسخهٔ **کامیت‌نشدهٔ** درخت زنده را لازم دارد (جدول کامل:
`baseline-classification.json`). نمونه‌های راستی‌آزمایی‌شده با traceback:

- `test_goal_action_bridge` (۳ سنجه؛ ثبت‌نشده در TESTS ولی جدا اجرا شد):
  `pipeline.py` ِ tracked ‏`task_id` می‌فرستد که فقط `mission_contract` ِ dirty
  می‌پذیرد → در همین مأموریت با پذیرشِ v2 سبز شد.
- `test_control_contracts_v2` ‏(۹/۱۰): ‏`memory_store.search(tenant_id=…)` ِ v2
  فقط در نسخهٔ dirty — با پذیرشِ v2 سبز شد (۱۰/۱۰).
- `test_tg_callback_emitter_parity` ‏(۵/۷): verb ِ `tr` فقط در center.py ِ dirty.
- `test_capability_registry` ‏(۱۷/۱۸): سنجهٔ self_knowledge به
  `doctor/self_knowledge.py` ِ dirty وابسته (و کلِ سوییت ~۳ دقیقه می‌دود →
  در run_all با سقفِ ۳۰۰s مرزی است).

### HEAD-red (pre-existing) — ۷ سوییت
جفتِ tracked ولی روی HEAD قرمز — هیچ‌کدام با تغییراتِ این مأموریت مرتبط نیستند
و پیش از هر patch ثبت شدند:

```text
test_llm_fence_coverage (2/3) · test_tg_verdict_durable (3/13) ·
test_cb_token_legmiss (3/16) · test_d2_halt_coverage (گاردِ halt ِ ۱ beat غایب) ·
test_tg_instant_and_sendlog · test_surface_policy · test_hebbian_eventclock (16/18)
```

این ۷ تا مالِ لِین‌های دیگرند؛ این مأموریت لمس‌شان نکرد (فقط ثبت).

## سوییت‌های هدفِ این مأموریت — قبل از تغییر

| سوییت | نتیجه |
|---|---|
| test_goal_action_bridge | ۱۱/۱۴ (سه قرمزِ CONFLICTED بالا) |
| test_test_cycle_beat | ۱۴/۱۴ |
| unified_control/test_snapshot_staleness | ۱۰/۱۰ |
| S1-05_test_ap_binding | ۱۵/۱۵ |
| test_memory_gate | ۱۰/۱۰ |
| test_outcome_spine | ۱۰/۱۰ |
| test_channel_status | سبز |
| ۷× test_world_discovery_* | ۸۵ passed (pytest؛ **در TESTS ثبت نبودند**) |
| ۱۰× tg orphans | ۹ سبز + ۱ CONFLICTED (emitter_parity) |
