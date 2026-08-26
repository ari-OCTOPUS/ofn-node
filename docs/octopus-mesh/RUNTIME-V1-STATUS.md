# OCTOPUS Persistent Autonomy — Runtime V1 (138)

وضعیت استقرار سامانهٔ سه‌بردی OCTOPUS طبق سند مالک
`US-PERSISTENT-AUTONOMY-THREE-BOARD-V1` (مجوز 2026-08-26، sha256 `a49347b4…`).

## معماری

- **138** — commander / router / reconciler / executor / ledger-owner
- **180** — quality-brain (cognitive, may_authorize=false)
- **182** — lab-witness (independent, read-only, may_authorize=false)

## Gate 0 — بسته شد (2026-08-26)

| مورد | نتیجه |
|---|---|
| V1 receipt از 180 (task `7a8bdd38`) | **exact match** — sha256 `7af92537…`، 43764 bytes |
| Witness verdict 182 (`16dc715f`) | **disputed** — ۲ اختلاف → task اصلاحی `4f61da18` |
| کالیبراسیون | anatomy cycle: score 0.35 (۲ ادعای جعلی فاش‌شده) |

## Gate 1 — runtime ساخته شد (روی 138)

- state machine مشترک: 19 state، transition append-only، hops≤3، retries≤2، reconcile≤1،
  idempotent replay، terminal no re-exec
- ۹ دیمون: supervisor، router، scheduler، cycle-settler، control-router، telegram-bridge،
  executor، budget، owner-control (+ heartbeat)
- ۵ کانفیگ: autonomy_policy، action_tiers، model_routes، token_budget، telegram_policy
- هر دیمون: `--once` / `--dry-run` / `--foreground`
- OWNER_PAUSE gate: agent حق حذف ندارد؛ resume فقط با owner identity verified
- Telegram: adapter=fake، mode=shadow، `TELEGRAM_BLOCKED_CONFIG` (envها نصب نیستند؛
  فقط نام env در config ثبت می‌شود، هرگز مقدار)
- budget: NORMAL/CONSERVE/SAFE_HOLD، per-task/run/daily cap

## تست‌ها

- **71/71 PASS** (25 bridge + 8 calibration + 38 runtime/Gate-2 simulation)
- Gate 2: clock injection، duplicate delivery، expired lease، owner pause، budget
  exhaustion، telegram fake adapter، malformed policy

## Gate 4 — systemd (بدون enable)

- ۱۱ unit در `octopus-mesh/runtime/systemd/` — همه `systemd-analyze verify` OK
- hardening: NoNewPrivileges، PrivateTmp، ProtectSystem=strict، UMask=0077
- **هیچ unit ای enable نشده** — تا PASS مستقل 180/182 (canary Gate 4) و 24h GREEN (Gate 5)

## Taskهای استقرار در راه (از transport رسمی)

| برد | task | وضعیت |
|---|---|---|
| 180 | `c7c5bdf1` DEPLOY-PERSISTENT-OCTOPUS-180 | ACK — در حال اجرا |
| 182 | `7b36cf1e` DEPLOY-PERSISTENT-OCTOPUS-182 | ACK — در حال اجرا |
| 180 | `4f61da18` CORRECT-180-ANATOMY-DISPUTES | ACK — در حال اجرا |

## شمارنده‌های امنیتی

- EXTERNAL_ACTIONS=0
- NEW_LAN_LISTENERS=0
- MAY_AUTHORIZE=false
- push بدون PR/merge/force-push (طبق قوانین مالک)

_به‌روزرسانی: 2026-08-26 — گزارش PERSISTENT_138_RESULT (STATUS=PARTIAL، منتظر ۳ پاسخ)._
