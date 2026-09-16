# IDENTITY-HEALTH DELTA — 0.572 → 0.672

created: 2026-08-20T12:22+10:00
updated: 2026-08-20T12:36+10:00
grade: **RESTART_ARTIFACT_SUSPECTED**
do_not_conflate: coherence
do_not_report_as_progress: true

## حکم جدید (دستور مالک #۳)

جهش در همان ثانیهٔ beat **42780** رخ داد که HRV ریست شد و AMBER کاذب ساخته شد. مقدار روی دیسک اندازه‌گیری شده است (`math-control-observe.jsonl` 2026-08-20T01:47:26Z) ولی **بهبود سلامت واقعی نیست** و نباید به‌عنوان پیشرفت گزارش شود.

قبلی را کنار فعلی بگذار: **0.572 → 0.672** · برچسب پیشرفت = ممنوع.

## فرضیهٔ پیش‌فرض خوش‌بینانه برای L — رد شد

کد `identity_equations.py`:

- `_read_signals` پیش‌فرض: `delta=None`, `c6_done=0`, `romajan_verified=0` (**144–166**)
- `delta is None` → `delta_pos = 0.0` (**376–377**) نه ۱
- `_hat(n,scale) = clamp01(n/scale)` (**130–134**)
- پس سیگنال خالی: `L = 0.40·0 + 0.30·0 + 0.30·0 = 0.0`

L=1.0 در `identities-latest.json` (ts 2026-08-20T01:49:50Z) یعنی `delta>0` و `c6_hat=1` و `romajan_hat=1` از **دیسک** (`c6_done=46`, `romajan_verified=44`, `delta=0.002775`). پیش‌فرض خالی خوش‌بینانه برای L **نیست**.

سری زمانی L پیش از جهش همچنان **UNLOCATED** (فقط latest). جزء دقیق جهش کامل UNVERIFIED می‌ماند.

## مؤلفه‌هایی که فقدان را وسط می‌گذارند (نه UNKNOWN)

| جزء | فقدان | مقدار | خط |
|---|---|---:|---:|
| L `delta_pos` | `delta is None` | **0.0** (بدبین) | 376–377 |
| E hats | شمارنده‌های صفر | 0.0 | 146–157, 400 |
| G `sigma_health` | `sigma is None` | **0.5** «unknown ≠ healthy» | 387–389 |
| G `coherence` | `probe` نیست/خطا | **0.5** | 348–352, 393 |
| K `c6_seed_ratio` پیش‌فرض | کلید غایب | **1.0** → `real_not_seed=0` (بدبین) | 155, 395 |
| O `alive` | ORGANISM-STATE غایب | 0.0 از init؛ اگر فایل هست و نه halt/freeze → **1.0** | 161, 199–201 |
| `budget_frac` | `musd==0` | **0.5** | 221 |

هیچ‌کدام در نبود تاریخ `UNKNOWN` برنمی‌گردانند.

## وابستگی به بافر درون‌حافظه‌ای

خود `evaluate()` از فایل‌های state می‌خواند، نه از deque ریتم.

| وابسته به حافظهٔ پروسه؟ | چیست |
|---|---|
| خیر (دیسک) | c6 / romajan / measurements.jsonl / identities-latest |
| بله، ولی **خارج از** identity_health | Rhythm `_beat_times` deque (`chrono_rhythm/rhythm.py:168`) — رنگ AMBER می‌سازد نه L |
| نیمه | `coherence.probe()` اگر state در حافظه داشته باشد؛ در فقدان → 0.5 روی دیسک نوشته می‌شود |
| زنده بودن O | `ORGANISM-STATE.halted/frozen` هر تیک بازنویسی می‌شود |

قاعدهٔ پیشنهادی (طراحی، اجرا=۰): تا پر شدن پنجرهٔ تاریخ، مؤلفه = **UNKNOWN** نه ۰ و نه ۰.۵. میانگین identity_health اگر هر جزء UNKNOWN باشد منتشر نشود / null.

## رد conflation با coherence

coherence در CURRENT-TRUTH برچسب STALE نسبت به beat زنده است. identity_health از میانگین پنج هویت است نه آن فیلد.
