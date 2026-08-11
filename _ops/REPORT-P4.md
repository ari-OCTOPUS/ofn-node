# REPORT-P4

## خط حقیقت

```text
money-legs-bridge-documented + pilot-plan-ready + effects-table-defined
!= bridge-live != pilot-dry-run-complete != money-flowing != AGI
```

## Done

### BRIDGE-CONTRACT.md
- API واقعی از کد: `model_router.ask()`, `ContextBundle`, `authorization()`, `approval_store`
- جدول effects برای ۴ پا (Lead, Mining, Project-F, Accounting)
- Pilot پیشنهادی: Lead-نقاشی (ساده‌ترین، کمترین ریسک)
- قواعد سخت: propose-only, ApprovalPort, schema reject, no gate bypass
- تست bridge: تحت پوشش red-team TI (RT01–RT25)

## Evidence

```text
Bridge contract:   _ops/BRIDGE-CONTRACT.md
Control contracts: _ops/control_contracts.py (ActionProposal, ApprovalDecision, authorization)
Context bundle:    _ops/context_bundle.py (schema octopus-context-bundle.v1)
Approval store:    _ops/telegram_center/approval_store.py
Outbound HTTPS:    _ops/integrations/outbound_https.py (action_sha256 binding)
Red-team:          _ops/tests/test_ti_redteam_injection.py → 25/25
```

## Gates

- [ ] pilot پا dry-run سبز — **PENDING (needs P1 arm + P3)**
- [x] صفر اثر پولی واقعی در تست
- [x] bridge red-team pass (25/25 از TI)
- [ ] مالک صریح: «این پا می‌تواند به سایه/live برود» — **PENDING**

## NOT done / blocked

1. **Pilot dry-run** — نیاز به P1 arm + انتخاب مالک
2. **Actual bridge code** — فقط سند، بدون تغییرِ کدِ production

## Owner decisions needed

1. **کدام پا به‌عنوان pilot؟** — پیشنهادی: Lead-نقاشی
2. **P1 arm اول، یا P4 pilot اول؟** — مگاپرامپت می‌گوید P4 فقط بعد از P3، ولی مستندات P4 مستقل است
