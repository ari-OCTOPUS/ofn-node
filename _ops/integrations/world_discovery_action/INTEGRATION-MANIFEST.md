---
type: integration-manifest
project: OCTOPUS
component: world_discovery_action
status: INTEGRATED_IN_SANDBOX
created: 2026-07-30
updated: 2026-07-30
---

# مانیفستِ اتصالِ آینده — مرزِ کشف ↔ عمل

> امروز هیچ‌چیز وصل نیست. پایین دقیقاً نوشته شده برای وصل‌شدن چه لازم است.

## ۱. وضعیتِ سه‌گانه

| اندام | وضعیت | صداکنندهٔ runtime |
|---|---|---|
| `world_discovery` (GLM) | `IMPLEMENTED_NOT_INTEGRATED` | صفر |
| `action_bridge` (ارشد) | `IMPLEMENTED_NOT_INTEGRATED` | صفر |
| `world_discovery_action` (مرز) | `INTEGRATED_IN_SANDBOX` | صفر |
| Telegram draft | `READY_FOR_OWNER_GATE` | — |
| Telegram send | `BLOCKED_BY_OWNER` | — |

## ۲. سطحِ API که پایدار است

```python
from world_discovery_action import translator, dry_run

translator.translate_discovery_artifact(artifact, *, now=None, prereg_id="") -> receipt
translator.build_action_request(discovery, experiment, *, now, prereg_id) -> action-request.v1
translator.build_no_action_receipt(artifact, *, reason, now) -> receipt
translator.compose_owner_draft(action_plan, *, now) -> draft
dry_run.run(artifact, *, sandbox_dir, now, prereg_lookup=None) -> bundle
```

`prereg_lookup` تزریق‌شدنی است — مرز هرگز `prereg` را import نمی‌کند.

## ۳. گام‌های LIVE شدن، به ترتیب

```text
گام ۱  رأیِ VQ-WD-CALLER-001 — آیا و با چه کادنسی صدا زده شود؟
گام ۲  رأیِ VQ-WD-TELEGRAM-001 — کدام کارت‌ها ارسال شوند؟
گام ۳  ساختِ `_ops/world_discovery/telegram_owner_gate.py` (فایلِ **نو**، نه
       ویرایشِ `approval_channel.py`). GLM جایش را در مانیفستِ خودش گذاشته.
گام ۴  retriever زندهٔ درون-پروسه‌ای برای GLM (بدونِ آن، validation در سطحِ
       ادعا ساختاراً ناممکن است — ریسکِ ثبت‌شدهٔ خودِ GLM §P)
گام ۵  فلگ `OCTOPUS_WIRE_WORLD_DISCOVERY` (ساخته نشده)
گام ۶  ثبتِ `test_boundary.py` و چهار تستِ پل در `run_all.py`
گام ۷  صداکننده — on-demand، **نه poller** (توصیهٔ خودِ GLM §۴)
```

## ۴. اتصالِ تلگرام — نقشه، اعمال‌نشده

```text
translator → telegram_draft (pure-data، بدونِ transport)
                    ↓
        TelegramOwnerGate  ← فایلِ نو، ساخته‌نشده
                    ↓
        approval_channel.send_text  ← دست‌نخورده، فقط‌خواندنی
```

⚠️ `approval_channel.py` هانکِ کامیت‌نشدهٔ جلسهٔ موازی دارد. هیچ ویرایشی روی آن
انجام نشد و نباید بشود تا آن هانک‌ها کامیت شوند.

## ۵. آنچه هرگز نباید معکوس شود

```text
مجاز:   world_discovery artifact → مرز → قراردادِ عمومیِ action_bridge
ممنوع:  action_bridge → internals ِ world_discovery
ممنوع:  world_discovery → executor ِ action_bridge
ممنوع:  world_discovery → organism/wiring مستقیم
```

## ۶. دامِ عملیاتی که یک‌بار خورد و باید بماند

هر دو پکیج فایلی به نامِ `contracts.py` دارند. با هر دو پوشه روی `sys.path`
مسطح، یکی دیگری را سایه می‌کند. مرز **دات‌دار** import می‌شود
(`from world_discovery_action import ...`) و importهای درونی‌اش نسبی‌اند؛ فقط
`action_bridge` مسطح می‌ماند. هر صداکنندهٔ آینده باید همین ترتیب را رعایت کند.
