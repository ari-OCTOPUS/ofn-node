# 07-TEST-REPORT — Cognitive Runtime (2026-08-12)

## تست‌های نو

| suite | تست | نتیجه |
|-------|------|-------|
| `test_cognitive_events.py` | 10 تست (uniqueness, sequence, redaction, may_authorize, terminal, summary, idempotent) | **10/10** ✅ |
| `test_chatbox_unified.py` | 13 تست (P×3, Q×4, S×3, intent×3) | **13/13** ✅ |
| `test_phase_jn.py` | 13 تست (J×3, K×2, L×3, N×5) | **13/13** ✅ |
| `test_verify_math_atlas.py` (pytest) | 41 تست | **41/41** ✅ |
| `test_neural_apply_evidence.py` (pytest) | 122 تست | **122/122** ✅ |

## Regression کامل (26 suite)

| suite | نتیجه |
|-------|-------|
| test_cognitive_events | ✅ |
| test_chatbox_unified | ✅ |
| test_awareness_ask_bridge | ✅ |
| test_memory_ask_recall | ✅ |
| test_miniapp_gateway | ✅ |
| test_phase_jn | ✅ |
| test_owner_verdicts | ✅ |
| test_profile_w3 | ✅ |
| test_relationships_wired | ✅ |
| test_pulse_arbiter | ✅ |
| test_rhythm | ✅ |
| test_spectral | ✅ |
| test_spectral_definitions | ✅ |
| test_signals_registry_schema | ✅ |
| test_registry_semantic_validator | ✅ |
| test_adr033_control_plane | ✅ |
| test_adr034_neural_demote | ✅ |
| test_adr035_neural_rearm | ✅ |
| test_neural_loop_close | ✅ |
| test_organism_protective | ✅ |
| test_frontier | ✅ |
| test_identity_equations | ✅ |
| test_heart_math | ✅ |
| test_cardiac_allometry | ✅ |
| test_chrono_heartbeat | ✅ |
| test_cognitive_unify | ✅ |

**مجموع: 26/26 suite + 163 pytest = صفر شکست**

## Validators

- `validate_signals_registry.py` → ok=true, errors=0 ✅
- `verify_math_atlas.py` → exit 0 ✅
- `node --check app.js` → OK ✅

## 10-conversation Acceptance (U)

همگی درست route شدند: memory · selfmap · architecture · equation · evidence · memory-proposal · limitations
همگی: run_id موجود · external_effect=False · may_authorize=False

## Security Invariants (تأییدشده)

- may_authorize=false در همهٔ event/claim/facts ✅
- applied=false بدون EXECUTION_RECEIPT ✅
- external_effect=false در همهٔ پاسخ‌ها ✅
- redaction خودکار (text/prompt/content فیلتر) ✅
- secret scan در ماژول‌های جدید: صفر ✅
- unauth → 403 ✅
- فایل‌های قفل‌شده: flags.cmd + ledger CLEAN ✅
