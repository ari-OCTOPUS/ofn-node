# IDENTITY-HEALTH DELTA — 0.572 → 0.672

created: 2026-08-20T12:22+10:00
grade: **MEASURED** (زمان و فایل میانگین) · جزء هویت **INFERRED** (سری زمانی اجزا نیست)
do_not_conflate: coherence

## اعداد

| مقدار | path | beat / ts | grade |
|---|---|---|---|
| 0.572 | `ORGANISM-STATE.json` math_control (GATE-0) | beat **42148** · ts 2026-08-20T00:09:30 · **STATE_STALE** | OBSERVED_STALE · `06-EVIDENCE/GATE-0-DISCOVERY-2026-08-20.md` |
| 0.572 آخرین در observe | `_ops/state/pulse/math-control-observe.jsonl` | تا پیش از 2026-08-20T01:47:26Z | MEASURED |
| **0.572 → 0.672** | همان jsonl یک ردیف تغییر | **2026-08-20T01:47:26Z** (= 11:47:26+10) | **MEASURED** |
| 0.672 زنده | `ORGANISM-STATE.json` `math_control.identity_health` | همزمان با خوانش T11 | MEASURED |
| اجزا بعد از جهش | `_ops/state/identities-latest.json` | ts **2026-08-20T01:49:50Z** | MEASURED |

`spine.py:_identity_health` خط ۱۵۷–۱۷۶: میانگین سادهٔ پنج مقدار `learner, earner, guardian, creator, organism` سپس `round(mean, 4)`.

## کدام جزء عوض شد

`identities-latest.json` بعد از جهش:

| id | value | parts |
|---|---:|---|
| learner L | **1.0** | delta_pos=1.0 · c6_hat=1.0 · romajan_hat=1.0 |
| earner E | 0.0 | money_hat=0 |
| guardian G | 0.675 | honest_hat=1.0 · sigma_health=0.5 · coherence=0.5 |
| creator K | 1.0 | c6_activity=1 · probe_div=1 |
| organism O | 0.685 | L=1 E=0 G=0.675 K=1 alive=1 |

میانگین: (1.0+0+0.675+1.0+0.685)/5 = **0.672**.

سری زمانی اجزا روی دیسک نیست (فقط latest). اگر G/K/O/E همان بمانند، 0.572 ⇒ **L=0.5**. Δ میانگین +0.100 = +0.5 روی یک عضو از پنج. این تناظر **INFERRED** است نه شاهد مستقیم L پیش از جهش.

معادلهٔ L (`identity_equations.py:399`): `0.40*delta_pos + 0.30*c6_hat + 0.30*rom_hat` با `delta_pos ∈ {0,1}`. L=1 یعنی هر سه جزء ۱. L=0.5 با c6=rom=1 ممکن نیست (آن‌وقت L∈{0.6,1.0})؛ پس یا کلاهک‌ها هم عوض شده‌اند یا G/K/O همزمان تکان خورده‌اند. جزء دقیق بدون اسنپ‌شات پیش‌ریاستارت **کامل UNVERIFIED** می‌ماند؛ زمان میانگین MEASURED است.

قبلی را کنار فعلی بگذار: **0.572 → 0.672**.

## ماشه

جهش observe دقیقاً **2026-08-20T01:47:26Z** = **11:47:26+10** = timestamp اولین ضربان بعد از boot ارگانیسم (ATTEMPT-2 PID 7096 boot 11:47:04، arbiter beat 42780 همان ثانیه).

`assoc_strength` در همان ردیف **عوض نشد** (0.9558895783575597 قبل و بعد). پس این جهش coherence نیست.

## رد صریح conflation با coherence

| سنجه | مقدار | منبع | کهنگی |
|---|---|---|---|
| identity_health | 0.672 | ORGANISM-STATE math_control | زنده نسبت به observe 01:47:26Z |
| coherence (خوانش اول T11) | **0.957** | CURRENT-TRUTH auto **2026-08-20T01:44:35Z** beat **42779** | **STALE_LABEL** آن لحظه |
| coherence (بازخوانی پایان جلسه) | **0.975** | CURRENT-TRUTH auto **2026-08-20T02:14:51Z** beat **42805** | در برابر زنده beat **42809** ≈ ۴ ضربان عقب |
| live beat پایان | 42809 | ORGANISM-STATE.ts 2026-08-20T12:17:03 | MEASURED |

گزارش قبلی «۵ ضربان عقب» مربوط به 42779 در برابر 42784 بود. این دو عدد را با identity_health قاطی نکن.

