---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, miniapp, control-panel, testing, debugging, frontend]
created: 2026-08-09
updated: 2026-08-09
created_by: agent
sources:
  - "_ops/telegram_center/miniapp/app.js — خوانده‌شده کامل (۲۱۰۴ خط)، ویرایش‌شده"
  - "_ops/telegram_center/miniapp_gateway.py — خوانده‌شده (routing/allowlist/handlers)"
  - "_ops/telegram_center/miniapp_state.py — خوانده‌شده (get_legs_state، dispatch_api)"
  - "curl زندهٔ ۲۴ endpoint با initData امضاشده (soak_gateway._refresh_initdata)"
  - "مرورگر زنده (devMode) روی http://127.0.0.1:8774/miniapp بعد از ری‌استارتِ gateway"
  - "test_miniapp_cockpit_ui.py / test_miniapp_look_locked.py / test_live_control_panel_smoke.py — اجرا و ویرایش‌شده"
  - "کامیت‌های f324098 (fix)، 194d218+f78bea0 (docs/merge) روی master"
---

# اسکن+دیباگِ کاملِ کنترل‌پنلِ مینی‌اپ — ۲۰۲۶-۰۸-۰۹

> رأیِ صریحِ مالک: «کنترل پنل اختاپوس وب اپ تلگرام رو کامل اسکن و دیباگ کن».
> این نوت نتیجهٔ آن اسکن است — یک باگِ **زندهٔ واقعی**، یک سوییتِ تستِ
> **اکثریت-قرمز** (عضوِ `run_all.py`)، و دو فایلِ تستِ دیگر که هرکدام یک
> سنجهٔ شکننده داشتند. همه با curl امضاشده + مرورگرِ زنده + mutation-test
> راستی‌آزمایی شدند، نه فقط با خواندنِ کد.

## روش

بعد از تلاشِ ناموفق برای گرفتنِ initData ِ واقعیِ تلگرام در مرورگر (SDK
رسمی `initData` را getter-only می‌سازد — امنیتِ درست، نه باگ)، استراتژی به
دو مسیرِ موازی تقسیم شد: (۱) خواندنِ کاملِ `app.js` سطر‌به‌سطر، (۲)
کنتراستِ زندهٔ هر ۲۴ endpoint (با initData ِ واقعاً امضاشده از طریقِ
`soak_gateway._refresh_initdata()`) در برابرِ دقیقاً همان فیلدهایی که هر
`render*` می‌خواند.

## یافتهٔ ۱ — باگِ زنده: `renderLegs()` بدونِ `panelGuard`

`get_legs_state()` (در `miniapp_state.py`) وقتی `business_legs` از
`ORGANISM-STATE.json` گم است، صادقانه `{status:"unknown", reason:"business_legs missing", legs:{}}`
برمی‌گرداند — **همین الان واقعاً این حالت بود** (تأییدشده با خواندنِ مستقیمِ
فایل). ولی `renderLegs()` هیچ‌وقت `d.status` را چک نمی‌کرد:

```js
// قبل:
var legs = d.legs||{}, ks = Object.keys(legs);
var up = ks.filter(...).length;   // up=0, ks.length=0 ⇒ up===ks.length ⇒ true
secHead("پاها", pill(..., up===ks.length ? "live" : ...))   // "live" یعنی سبز
```

نتیجه: قرصِ «۰ از ۰» با تُنِ **live** (سبز) رندر می‌شد — یعنی «نخواندم»
دقیقاً شبیهِ «صفر پا دارم، همه سالم» دیده می‌شد. همان کلاسِ باگی که این
هفته چند جای دیگر (`renderBrain`/`renderGovernor`/`renderObsidian`/
`renderRegistry`) با یک گاردِ مشترک (`panelGuard()`) بسته شده بود —
`renderLegs` از آن گارد استفاده نمی‌کرد، جا افتاده بود.

**فیکس:** همان `panelGuard("پاها", d)` که چهار خواهر/برادرش استفاده
می‌کنند. راستی‌آزمایی:
- مرورگرِ زنده (devMode → همهٔ endpoint ها ۴۰۳): بخشِ «پاها» حالا دقیقاً
  همان کارتِ صادقِ «خوانده نشد / HTTP 403 …» را می‌سازد که خواهرانش می‌سازند.
- mutation-test: حذفِ موقتِ فراخوانیِ `panelGuard` از `renderLegs` →
  `t_c_panel_guard_never_lets_bad_or_missing_data_render_as_healthy` درست
  قرمز شد با پیامِ دقیق («renderLegs( دیگر از panelGuard رد نمی‌شود»).

## یافتهٔ ۲ — سوییتِ اکثریت-قرمز: `test_miniapp_cockpit_ui.py`

این فایل عضوِ `run_all.py` است (نه یک تستِ دستی) و **۶ از ۱۱** بود.
هر سه علتِ ریشه، سه نمونهٔ متفاوتِ یک الگو بودند: **کدِ فرانت‌اند عوض شد،
تستش نه.**

| علت | جزئیات | فیکس |
|---|---|---|
| رگرسِ درایورِ Node | `tabRe` انتظار داشت بلافاصله بعدِ `data-tab="X"` علامتِ `>` بیاید؛ فازِ ARIA-tablist (`role`/`id`/`aria-selected`/`aria-controls`/`tabindex`) بینشان نشست ⇒ صفر تب پارس می‌شد ⇒ هر `clickTab` روی `undefined.closest` کرش می‌کرد | `[^>]*` به regex اضافه شد |
| `t_h` هاردکد | `assert d["rendered_tabs"] == 6` — تبِ هفتم/هشتم/نهم (notifications/scans/ask، ۰۸-۰۷..۰۸-۰۸) این عدد را کهنه کرده بودند | شمارش از خودِ `index.html` استخراج می‌شود |
| `t_d` فرضِ تک-endpoint | `assert all(c == '"/api/actions"' ...)` — دکمهٔ نوِ «ری‌استارتِ کامل» یک `apiPost("/api/restart", ...)` لیترالِ مشروع اضافه کرده بود | allowlist از خودِ `miniapp_gateway.py` خوانده می‌شود، نه فهرستِ دومِ هاردکد |

علاوه بر این سه، `t_c` گسترش یافت تا `renderLegs` را هم در فهرستِ
consumersِ `panelGuard` بپوشاند (بند بالا). هر چهار فیکس مستقلاً
mutation-tested. نتیجه: **۱۱/۱۱**.

## یافتهٔ ۳ و ۴ — دو فایلِ تستِ دیگر

- **`test_miniapp_look_locked.py`** (۱۷/۱۸ → ۱۸/۱۸): اکشنِ `diagnostics.noop`
  (کارِ قبل‌ازاینِ همین جلسه، پروبِ soak-testِ بی‌اثر) هیچ UI caller نداشت —
  و **نباید هم داشته باشد** (اقدامِ مالک‌محور نیست). استثنایِ صریح
  (`NO_UI_ACTIONS`) اضافه شد به‌جایِ ساختنِ یک دکمهٔ بی‌معنا.
- **`test_live_control_panel_smoke.py`** (دستی، خارجِ `run_all.py`، عمداً
  روی گیت‌ویِ زنده): فازِ ۵ با شمارشِ خامِ `len(items)` قبل/بعد سنجیده
  می‌شد — رویِ سیستمِ **واقعاً زنده و هم‌زمان**، یک تسکِ نامرتبط («تپِ
  دوگانه») بینِ دو خواندن ظاهر شد و شمارش را دروغین قرمز کرد (تأییدشده با
  یک repro-ی ایزوله: create→close واقعاً net-zero می‌شود). فیکس: سنجهٔ
  presence-by-id به‌جایِ شمار. اجرایِ کاملِ نهایی: **۵۳/۵۳**، ۵.۳ دقیقه.

## کدِ مرده

- `renderHome` و `renderNext`: صداکنندهٔ صفر، **بدونِ** هیچ pin-test — حذف
  شدند (بازماندهٔ بازطراحیِ تریاژِ خانه و ادغامِ تبِ سیستم در ۰۸-۰۴).
- `renderStudio`: صداکنندهٔ صفر **ولی** `test_miniapp_cockpit_ui.py::t_d`
  صریحاً pin کرده («مردهٔ دست‌نخورده») با پیامِ خطای «اگر عمدی است این
  تست را به‌روز کن». **دست‌نخورده ماند** — تصمیمِ قبلاً ثبت‌شده را دور
  نزدم.

## راستی‌آزماییِ نهایی

۸ فایلِ تستِ مرتبط سبز: `test_miniapp_gateway` (۴۷/۴۷)،
`test_absence_is_not_emptiness` (۲۴/۲۴)، `test_deep_scan_followups_20260807`
(۷/۷)، `test_miniapp_ops_readmodel` (۲۸/۲۸)، `test_miniapp_shell_2026`
(۱۱/۱۱)، + سه فایلِ فیکس‌شدهٔ بالا. سوییتِ کاملِ ۴۶۷فایلیِ `run_all.py`
اجرا **نشد** — خارج از دامنهٔ «کنترل‌پنل» بود، عمداً صریح گفته می‌شود
که این پوشش نداده شده، نه بی‌صدا فرض‌شده.

gateway ری‌استارت شد (PID تغییر تأیید شد) تا کدِ فیکس‌شده لود شود.

## یافتهٔ فرعیِ فرایندی

`Write(_Archive/**)` و `Edit(_Archive/**)` در `.claude/settings.json` روی
`deny` هستند. یعنی سرریزِ استانداردِ `HANDOFF.md` (که خودِ آن فایل چند بار
قبلاً انجام داده، مقصدش `_Archive/Logs/HANDOFF-archive-*.md`) دیگر برایِ
ایجنت ممکن نیست. `HANDOFF.md` فعلاً بالایِ سقفِ ۲۰۰ خط مانده تا مالک تصمیم
بگیرد این deny عمدی است یا باید برایِ همین یک مسیر استثنا بخورد.

## کجا زندگی می‌کند

فیکسِ کد: `_ops/telegram_center/miniapp/app.js` +
`_ops/tests/test_miniapp_cockpit_ui.py` +
`_ops/tests/test_miniapp_look_locked.py` +
`_ops/tests/test_live_control_panel_smoke.py` — کامیتِ `f324098` روی
master. مستندسازی: [[../../01 - Dashboard/HANDOFF|HANDOFF]] +
[[../../04 - Architect System/architect/PROJECT|architect/PROJECT]].
