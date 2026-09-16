---
type: proposal
status: OWNER_SIGNED_VIA_BUNDLE
tags: [octopus, shadow, signing, wave0]
created: 2026-08-20
updated: 2026-08-20
---

# کارت پذیرش Shadow vertical slice — UNSIGNED

decision_id: OWNER-VERDICT-SHADOW-VERTICAL-SLICE-2026-08-20
status: OWNER_SIGNED_VIA_BUNDLE
owner_verdict: ACCEPTED_FOR_SHADOW_WITH_CONDITIONS
authority: دستور مالک #۵ · امضا = عمل مالک · ایجنت کلید را لمس نمی‌کند
created: 2026-08-20
payload: `02-DECISIONS/OWNER-VERDICT-SHADOW-VERTICAL-SLICE-2026-08-20.json`
payload_sha256: `4c80264d2e3149e41c0600543be98d8cbd339364f360f13aca5318e29ff6a8a8`
canonicalization: UTF-8 no BOM · LF · `json.dumps(sort_keys=True, indent=2, ensure_ascii=True)` + trailing newline
package: `_ops/shadow_homeostasis`
commits: `a6ca994` (`a6ca9947a52034e06bdae61a05004da4864df4b4`) · `3eb2b95` (`3eb2b9560078e3000b22d81a9b804037f1cb645d`)
wave: WAVE0_OBSERVE_ONLY
autonomy: L2_ARMED
executable: false

> این کارت **SIGNED نیست.** `owner_vote` خالی است. پیش‌نویس WAVE0 (`06-EVIDENCE/HC-WM-MC-WAVE0-2026-08-20/OWNER-VERDICT-DRAFT.md`) امضا نیست — SoT امضا همین کارت + payload است.
> ایجنت کلید خصوصی را نمی‌خواند و `openssl pkeyutl -sign` را اجرا نمی‌کند.

## حکم قفل‌شده در payload (منتظر امضای مالک)

`owner_verdict`: **ACCEPTED_FOR_SHADOW_WITH_CONDITIONS**

### approved_scope

- `offline_and_readonly_laptop_shadow`
- `append_only_evidence_capture`
- `deterministic_replay`
- `advisory_homeostatic_assessment`
- `policy_free_world_model`
- `domain_skill_scores`

### prohibited_scope

- `live_spine_write_or_wiring`
- `organism_py_integration`
- `scheduler_or_daemon`
- `Orange_Pi_deployment`
- `planner_or_actuator_authority`
- `executable_true`
- `model_calls_during_soak`
- `AUD_spending_during_soak`
- `closing_GAP_001`

ثابت‌ها (قفل در JSON): GAP-001 OPEN · D6 BETWEEN_RUN_VARIANCE · live_spine NOT_VERIFIED_BITEMPORAL.

اگر SHA256 فایل با `4c80264d2e3149e41c0600543be98d8cbd339364f360f13aca5318e29ff6a8a8` نخواند: **امضا نکن.**

## فرمان مالک (یک‌بار، نه از سشن ایجنت)

ترجیح: wrapper هر دو کارت — `_ops/owner-runbook/SIGN-ALL-PENDING-2026-08-20.ps1`

تک‌کارت: `_ops/owner-runbook/SIGN-SHADOW-VERTICAL-SLICE-2026-08-20.ps1`

عمومی: `_ops/owner-signing/octopus-owner-ed25519-public.pem`  
خصوصی (فقط مالک، بیرون repo): `~\.octopus-signing\octopus-owner-ed25519-private.pem`

## رأی

- [ ] **امضا می‌کنم** — payload بالا، پس از verify سبز
- [ ] **رد** — soak شروع نشود
- [ ] **تصحیح scope:** ______

امضا: ________ · تاریخ: ________
