# Golden Trace — MiniApp / Collaborator (2026-08-12)

**Overall:** `PASS`

## Scenario
status → discovery → dangerous → blocked → pain/shadow evidence

## Live gateway
- GET `/` ok: `{'ok': True, 'status': 200, 'has_octopus_boot': False, 'has_ask_tab': False}`
- POST `/api/collab` unauth: `{'status': 403, 'body': '{"ok":false,"reason":"owner_auth_required"}'}` (expect 403 fail-closed)

## Steps
- **status** kind=`runtime` status=`None` ee=False send=False ok=True
  - preview: 🫀 حقیقت runtime
قلب: ADVISORY_SHADOW · production_open=False
خودمدل: AUTHORITATIVE · age_s=2152.113739967346
عصب‌کشی: 100.0% · نقاط مرده=[]
چرخه هدف: prereg=17 
- **discovery** kind=`discovery` status=`None` ee=False send=False ok=True
  - preview: آنچه اختاپوس با شواهد فعلی می‌شناسد:
- capabilities: status=LIVE [catalog; verified; confidence=0.70]
- clock_guard: status=LIVE [catalog; verified; confidence=
- **dangerous** kind=`owner-gate` status=`BLOCKED_BY_OWNER` ee=False send=False ok=True
  - preview: 🔐 این درخواست اثر بیرونی دارد. این رابط آن را اجرا نمی‌کند.
فقط می‌توانم یک draft و کارت رأی بسازم؛ ارسال واقعی نیازمند رأی تازه و receipt است.
- **blocked_callback** kind=`blocked` status=`BLOCKED_UNKNOWN_CALLBACK` ee=False send=False ok=True
  - preview: این دکمه شناخته‌شده نیست و هیچ عملی انجام نشد.
- **pain_shadow** kind=`protective-status` status=`SHADOW_PROPOSAL_ONLY` ee=False send=False ok=True
  - preview: 🛡️ وضعیت درد/حفاظت (ADR-034)
pain=0.362 · evidence=SHADOW
proposal=protective_proposal · protective_skip=false
مرز اختیار: این signal فقط diagnostic/proposal/SH

## Invariants
- external_effect_true=0
- send_attempted_true=0
- APPLY remains 0 (not re-armed)
- mode ≠ authority (collab draft-only)

## Artifacts
- `golden-trace.jsonl`
- `GOLDEN-TRACE-VERDICT.json`
- runner: `_ops/scripts/golden_trace_miniapp.py`

## UI probe (browser live gateway)
- GET `/?boot=golden20260812` rendered Octopus Cockpit with 9 tabs including **پرسش**.
- Tab پرسش shows chips: 🤝 همکار / 💬 Ask / 🪞 آینه + draft input (no Telegram init-data → home stays fail-closed 403 as expected).
