---
type: integration-manifest
project: OCTOPUS
component: action_bridge
status: IMPLEMENTED_NOT_INTEGRATED
created: 2026-07-30
updated: 2026-07-30
---

# action_bridge — مانیفستِ ادغام

> **این پکیج امروز به هیچ‌چیز وصل نیست، و این عمدی است.** پایین دقیقاً نوشته
> شده که برای وصل‌شدن چه چیزی لازم است و چه چیزی هنوز نیست.

## ۱. وضعیتِ صادقانه

| محور | وضع |
|---|---|
| کد | نوشته و تست‌شده |
| صداکنندهٔ runtime | **صفر** |
| فلگ | **ساخته نشد** — عمداً؛ فلگِ خاموش یعنی کدِ آمادهٔ خفته |
| اتصال به `organism`/`wiring` | صفر |
| اتصال به `test_cycle`/`prereg`/`cycle_evaluator` | صفر |
| اتصال به `world_discovery` | صفر (namespace ِ GLM لمس نشد) |
| ثبت در `run_all.py` | **نشد** — کارِ موازی روی آن فایل در جریان است |
| اثرِ بیرونی | صفر، در هر مسیر، تست‌شده |
| خرج | صفر، در هر مسیر، تست‌شده |
| تغییرِ state زنده | صفر |

## ۲. سطحِ API که پایدار است

فقط این چهار تابع قراردادِ عمومی‌اند. بقیه داخلی‌اند و ممکن است عوض شوند.

```python
planner.plan(req, *, sandbox_root, prereg_lookup=None, ledger=None,
             approval=None, used_nonces=None, now=0.0) -> plan
executor.execute(req, plan, *, sandbox_root, receipts_dir, ledger_path,
                 now_iso="", dry_run=True) -> {"ok", "receipt"}
owner_gate.make_card(req, plan, *, now) -> card          # کارت ≠ مجوز
owner_gate.grant(req, *, now, ttl_s, approver) -> {"ok", "approval"}
```

`prereg_lookup` عمداً **تزریق‌شدنی** است: پل هیچ‌وقت `prereg` را import نمی‌کند،
تا دو ماژول بتوانند جدا از هم بمیرند و تست بدونِ درختِ زنده بدود.

## ۳. آنچه برای LIVE شدن لازم است — به ترتیب

```text
گام ۱  لایهٔ ترجمه: «متنِ روش» → action-request.v1
       ⚠️ این نگاشت **نباید** با مدل ساخته شود. اگر مدل تصمیم بگیرد یک روش
       کدام `action_type` است، متن دوباره مجوز شده و کلِ اصلِ ۳ می‌شکند.
       نگاشت باید جدولی و بازبینی‌شده باشد.

گام ۲  sandbox ِ تولیدی: کدام ریشه؟ پیشنهاد `_ops/state/action_bridge/`
       ⚠️ ولی VQ-OBS-REPLACE-001 باز است: `os.replace` روی `_ops/state/`
       با WinError 5 شکست می‌خورد. تا آن بسته نشود، sandbox باید جای دیگری
       باشد یا `receipt._atomic_write` (که retry دارد) کافی بودنش سنجیده شود.

گام ۳  کلیدِ امضا: `OCTOPUS_ACTION_BRIDGE_HMAC` (≥۱۶ کاراکتر) در `.env`.
       بدونِ آن هیچ مجوزی صادر یا تأیید نمی‌شود — یعنی A3 عملاً بسته است.

گام ۴  پایدارسازیِ `used_nonces` و `ledger`. امروز in-memory اند؛ در تولید
       باید روی دیسک بنشینند وگرنه ری‌استارت = بازگشتِ replay و از دست رفتنِ
       idempotency.

گام ۵  ثبتِ چهار فایلِ تست در `run_all.py` (بعد از پایانِ کارِ موازی).

گام ۶  صداکننده در `test_cycle.run` طبقِ `integration.PROPOSED_CALLER`،
       پشتِ فلگِ نو `OCTOPUS_WIRE_ACTION_BRIDGE`.

گام ۷  رأیِ مالک برای هر کلاسی بالاتر از A1.
```

## ۴. رأی‌هایی که مالک باید بدهد

| # | تصمیم | پیش‌فرضِ امن |
|---|---|---|
| ۱ | ریشهٔ sandbox ِ تولیدی کجا باشد؟ | تا رأی، هیچ‌جا — پل وصل نیست |
| ۲ | `OCTOPUS_ACTION_BRIDGE_HMAC` ساخته شود؟ | بدونِ آن A3 بسته می‌ماند |
| ۳ | `A2` (تغییرِ برگشت‌پذیرِ allowlisted) باز شود؟ | `BLOCK` — تا چهار پیش‌شرطِ VQ-SELFGOAL-002 |
| ۴ | `A3` واقعاً کارتِ تلگرام بفرستد؟ | امروز فقط شیءِ کارت ساخته می‌شود، ارسال نه |
| ۵ | فلگِ `OCTOPUS_WIRE_ACTION_BRIDGE` ساخته و آرم شود؟ | ساخته نشده |

## ۵. نگاشتِ آیندهٔ کشف ← عمل (وقتی GLM تحویل داد)

```text
E0 → A0      E1 → A1      E2 → A3      E3 → A4      E4 → A5
```

جهتِ وابستگی، یک‌طرفه و بدونِ استثنا:

```text
artifact ِ world_discovery  →  لایهٔ ترجمه (پکیجِ سوم)  →  action-request.v1
```

نه `action_bridge` داخلِ `world_discovery` را import می‌کند، نه برعکس. اگر روزی
یکی دیگری را import کرد، همان لحظه دو اندام به هم جوش خورده‌اند و جدا مردنشان
ناممکن شده.

## ۶. چک‌لیستِ بازبینیِ handoff ِ GLM

در `integration.HANDOFF_REVIEW_CHECKLIST` ماشین‌خوان است. سرفصل‌ها: pure-data و
نسخه‌دار · اثرِ بیرونی صفر · هزینه صفر · source/evidence/falsifier در هر کشف ·
owner gate صریح · ایزولاسیونِ prompt-injection · قابلِ ترجمه به `action-request.v1`
· صفر privilege برای `source_component` · نگاشتِ E0..E4 · صفر importِ دوطرفه.
