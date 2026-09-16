# 📈 Crypto-eToro RUNBOOK — اجرای امن alert-only

> وضعیت: critical / alert-only. هیچ BUY/SELL خودکار.

---

## اصول سخت

- BUY همیشه انسانی.
- SELL خودکار فقط اگر exit_rule از قبل ثبت و verdict فعال باشد؛ فعلاً disabled.
- exchange keys off-box; zero LLM access.
- no LLM in command path.
- output = alerts/reports only.

---

## Graph search قبل از کار

1. Load `PROJECT.md`, `MANIFEST.yaml`, `contracts/adapter.yaml`, `Portfolio Registry.md`, `Standing Rules.md`.
2. Follow `CryptoEtoro → Accounting` and shared Mining organs.
3. Check `RISK-LADDER.md`: critical/alert-only.
4. If action is trade/order/API-key → verdict request, stop.

---

## مجاز

- portfolio registry template
- thesis/exit_rule draft
- stale data report
- alert-only dashboard design
- bug ticket for EdgeClassifier

## ممنوع

- exchange login/API call
- BUY/SELL
- portfolio advice as final
- moving funds
- importing secrets

---

## Position registry minimum

```yaml
position_id:
asset:
venue:
status: open/closed/watchlist
thesis:
exit_rule:
risk_note:
action_mode: alert-only
```
