# AMBER CAUSALITY — GREEN@42770 → AMBER@42784

created: 2026-08-20T12:20+10:00
verdict: **RESTART_INDUCED**
frozen_pair: beat 42770 GREEN · beat 42784 AMBER · only restart between (PID 10028→7096, boot 11:47:04)
until_this_verdict: جملهٔ «restart was clean» **مجاز نیست**

## سری زمانی رنگ (arbiter-shadow)

منبع: `_ops/state/pulse/arbiter-shadow.jsonl` (دلایل در این سینک نوشته نمی‌شود — C-044).

| beat | ts local | period_s | driver | color |
|---:|---|---:|---|---|
| 42760 | 11:04:41 | 114.69 | consensus | GREEN |
| 42766 | 11:11:33 | 114.28 | consensus | GREEN |
| 42770 | 11:16:07 | 114.01 | consensus | GREEN |
| 42778 | 11:28:47 | 114.74 | solo:rhythm | GREEN |
| 42779 | 11:35:41 | 114.63 | solo:rhythm | GREEN |
| — | 11:42:46 ATTEMPT2_START · 11:47:04 organism boot PID 7096 | — | — | (gap: ارگانیسم پایین) |
| **42780** | **11:47:26** | 112.76 | consensus | **AMBER** ← اولین رنگ بعد از boot |
| 42784 | 11:52:18 | 113.65 | consensus | AMBER |
| 42786 | 11:54:21 | 113.64 | consensus | AMBER |
| 42788 | 11:56:25 | 114.35 | consensus | AMBER |
| 42790 | 11:58:28 | 114.33 | consensus | AMBER |
| 42792 | 12:00:32 | 114.44 | consensus | GREEN |

اسنپ‌شات پیش‌ریاستارت: `06-EVIDENCE/RESTART-BASELINE-2026-08-20/SNAPSHOT.json` beat 42770 GREEN period 114.01. ATTEMPT-2: PID 10028→7096 boot 11:47:04 RESULT OK.

اولین AMBER = beat **42780** در **۲۲ ثانیه** بعد از boot، نه 42784. 42784 فقط ادامهٔ همان رژیم AMBER است.

بازگشت GREEN در 42792 با `arbiter-latest.json` note ریتم: `mode=STEADY/GREEN · hrv=0.26`.

## ورودی‌هایی که رنگ را می‌سازند

`pulse_arbiter.arbitrate` خط ۲۱۰–۲۱۲: رنگ آشتی = **بدترین رنگ قلب‌های حاضر**.

| قلب | شرط رنگ | قبل از boot (42779 GREEN) | بعد از boot (42780 AMBER) | الان (GREEN) |
|---|---|---|---|---|
| cardiac | AMBER iff `budget.depleted` (`pulse_arbiter.py:286–288`) | depleted=false (وگرنه کل سری صبح AMBER بود) | spent پایدار ماند | `heart-setpoint-latest.json` `daily_beat_cap=2000` · `cardiac-budget.json` spent=299 < 2000 → depleted=false · vote GREEN `pace=mice` |
| control_law | RED iff braking/`fail_closed_reason` (`:328`) | GREEN (کل سری 42760–42779) | fail_closed در shadow فعلی `null` (`heart-shadow-latest.json`) | GREEN · period~390s LIVE |
| rhythm | `_mode_map`: `hrv < 0.2` → AMBER (`chrono_rhythm/rhythm.py:227–228`) | GREEN · driver حتی solo:rhythm | **پنجرهٔ HRV خالی → hrv=0.0 → AMBER** | GREEN · hrv=0.26 (فقط بالای آستانهٔ 0.2) |

Cardiac spent **ریست نشد**: GATE-0 00:21 spent=4؛ حالا 299؛ date همان 2026-08-20. پس AMBER از ته کشیدن سقف ضربان (cap=2000) نیست.

## آیا پنجرهٔ آماری / شمارندهٔ خطا روی ریاستارت ریست می‌شود؟

| شمارنده | persist؟ | ریست روی ریاستارت؟ | شاهد |
|---|---|---|---|
| Rhythm `_beat_times` deque maxlen=20 | حافظهٔ پروسه (`rhythm.py:168`) | **بله** — آبجکت `Rhythm` با پروسه می‌میرد | organism.py:266 `_rhythm = None` سپس در حلقه زنده می‌شود؛ بعد از PID 7096 پنجره خالی است |
| Rhythm HRV | از همان deque (`:196–206`)؛ اگر deltas خالی → **hrv=0.0** | بله | خط ۲۰۵–۲۰۶ + آستانه `hrv < 0.2` → AMBER |
| cardiac `spent`/`resting` | دیسک `cardiac-budget.json` | **خیر** (فقط تغییر `date`) | spent 4→299 همان روز |
| control_law 24h plant_saturation | `heart-shadow-latest.json` `window_hours=24` | فایل می‌ماند | fail_closed_reason=null |
| cortex `organism_stress` | `cortex/stress-latest.json` | فایل می‌ماند | خوانده می‌شود در neural_beat نه در رنگ داور |

## حکم

**RESTART_INDUCED.** مکانیسم: cold-start ریتم (deque خالی → hrv=0 < 0.2 → vote AMBER) در اولین ضربان پروسهٔ نو (42780، 11:47:26). 42770 GREEN و 42784 AMBER با همین علیت به هم وصل‌اند؛ 42784 نقطهٔ شروع نیست.

رنگ بعد از ~۶ ضربان (hrv=0.26) به GREEN برگشت — سازگار با پر شدن پنجره نه با خطای پایدار بودجه.

ادعای «ریاستارت تمیز بود» تا این حکم باطل است: ریاستارت از نظر PID/RESULT:OK قبول است؛ از نظر رنگ داور **القاکنندهٔ AMBER موقت** بود.

## نقص تله‌متری reasons:[]

1. `allocate_beat` موفق همیشه `"reasons": []` می‌نویسد (`life_currency.py:247`) — طراحیِ شکست تخصیص است نه توضیح رنگ.
2. `arbitrate` فقط برای **RED** دلیل رنگ append می‌کند (`pulse_arbiter.py:243–244`). گذار GREEN↔AMBER در reasons داور **نامرئی** است.
3. `persist` در jsonl فقط `ts, beat, period, driver, color, wire_open` می‌نویسد (`:443–446`) — reasons drop می‌شود.

اگر طراحی نبود: → [[C-044-EMPTY-COLOR-REASONS-2026-08-20]]. ثبت شد: طراحی ناقص / حذف تله‌متری، نه «طبق قرارداد خالی بودن = سالم».
