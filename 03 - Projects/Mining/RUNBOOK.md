# ⛏️ Mining RUNBOOK — اجرای امن research/fleet

> وضعیت: INFORM-only / no wallet / no rig execution.

---

## اصول سخت

- هیچ agent به wallet/seed/private key دسترسی ندارد.
- هیچ buy/sell/withdraw/deploy/SSH مستقیم.
- mining فقط اگر برق <$0.05/kWh یا solar و verdict مالک.
- یک experiment فعال در هر node-group.
- profit numbers تا داده واقعی `[To measure]`.

---

## Graph search قبل از کار

1. Load `PROJECT.md`, `MANIFEST.yaml`, `contracts/adapter.yaml`, `Hardware Registry & Runbook.md`, `Coin Scouting Framework.md`.
2. Follow `Mining → Accounting` and `Mining ↔ Crypto-eToro` shared organs.
3. Check `RISK-LADDER.md`: INFORM-only.
4. If action needs wallet/rig/deploy → verdict request, stop.

---

## مجاز

- hardware inventory draft
- coin scouting report
- electricity feasibility table
- risk report
- accounting touchpoint draft

## ممنوع

- wallet access
- mining start/stop
- SSH/deploy
- exchange action
- changing rig config

---

## Hardware registry minimum

```yaml
node_id:
device_type:
status: offline/available/running/broken/unknown
location_code:
power_source:
notes_safe:
```
