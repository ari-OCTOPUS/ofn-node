# 🐙 شناخت فعلی اختاپوس — Snapshot

> این فایل خلاصهٔ شناخت فعلی از اختاپوس است، بر اساس کاوش‌های آزمون‌وخطا روی `F:\backup`.

---

## 1. تعریف فعلی اختاپوس

[FACT] اختاپوس در `F:\backup` یک پوشهٔ واحد نیست؛ یک اکوسیستم چندلایه است.

لایه‌های مشاهده‌شده:

| لایه | مسیر | نقش فعلی |
|---|---|---|
| بدن اجرایی/حاکم | `_ops` | organism, cortex, heart, budget, legs, doctor, state |
| هستهٔ v2 | `octopus_core` | event bus, actuator, telemetry, health |
| کنترل‌پلین مالی/گیت | `app` | NBB Control Plane, invariants, budget, ledger, human verdict |
| مغز پژوهشی | `4d_system` | SOG / Brain-OS / self-model experiments |
| visualization | `OCTOPUS` | HTML worlds, architecture bible, dashboard visuals |
| سیستم عصبی داده | `nervous-system` | extractors, JS globals, live-data, ops-data |
| ابزار نقشه‌برداری | `نقشه اختاپوس` | vault scanner, report, inventory |
| پروژه‌ها/پاها | `03 - Projects` | ۶ پای درآمدی + اندام‌های تازه مثل PMO/spec compiler |

---

## 2. مدل اندامی

```text
Owner / GOALS / Verdict / Kill
        ↓
_ops/organism.py
        ↓
[cortex]  تصمیم، synthesis، route، self-model
[heart]   ضربان، کنترل، work pump
[budget]  متابولیسم، پول، گیت، fitness، replication
[legs]    پاهای اجرایی propose-only
[doctor]  خودبهبود، RFC، sandbox، critic
[state]   حافظه، event، chrono، queue، telemetry
        ↓
app / octopus_core / 4d_system / nervous-system / OCTOPUS
```

---

## 3. یافته‌های کلیدی

### 3.1 `_ops` محتمل‌ترین بدن اجرایی است

[FACT] `_ops` شامل این‌هاست:

- `organism.py`
- `cortex/`
- `heart/`
- `budget/`
- `legs/`
- `doctor/`
- `state/`
- activation flags
- run scripts

[INFERENCE] پس `_ops` احتمالاً بدن اجرایی/حاکم اصلی است.

---

### 3.2 `octopus_core` هستهٔ v2 است

[FACT] `octopus_core` شامل:

- `event_bus.py`
- `actuator.py`
- `telemetry.py`
- `health.py`
- `capability_registry.py`
- گزارش rebuild با ادعای ۳۶ تست pass

[INFERENCE] این لایه برای تبدیل استعارهٔ اختاپوس به event bus / actuator / telemetry واقعی ساخته شده است.

---

### 3.3 `app` نقش NBB Control Plane دارد

[FACT] `app/README.md` می‌گوید:

- human-sovereign
- budget-governed
- Governor proposes, gates enforce, human rules
- ۱۲ invariant

[INFERENCE] `app` کنترل‌پلین رسمی برای پول، گیت، ledger و human verdict است.

---

### 3.4 عدد پاها drift دارد

[FACT] اسناد از ۶ پای پروژه‌ای حرف می‌زنند.
[FACT] اما `03 - Projects` شامل این‌ها بود:

- `Accounting`
- `Crypto - etoro`
- `Lead-نقاشی`
- `Mining`
- `Ziman Galerry`
- `اونلی فنز`
- `research-spec-compiler`
- `_OCTOPUS-PMO`

[INFERENCE] تعبیر درست‌تر:

```text
۶ پای درآمدی/کسب‌وکار
۸ اندام عملیاتی در 03 - Projects
```

---

## 4. DNA حاکمیتی

[FACT] در چند لایه تکرار شده:

- propose-only
- human verdict برای اقدام برگشت‌ناپذیر
- budget cap
- kill-switch
- fail-closed
- ledger append-only
- quarantine برای boundary text
- no self-law-edit

[INFERENCE] DNA اصلی اختاپوس کنترل، گیت، مشاهده‌پذیری و تسلیم در برابر انسان است.

---

## 5. وضعیت اجرای واقعی

[FACT] launchers، state، chrono.db، logs و activation flags وجود دارند.
[UNKNOWN] اما runtime زنده اجرا/تست نشد.

پس:

```text
وجود ارگانیسم از روی فایل‌ها تأیید شده؛ زنده‌بودن runtime هنوز نیازمند probe جداگانه است.
```

---

## 6. قانون فعلی برای ادامه

مهم‌ترین سؤال بعدی:

```text
Source of Truth اجرایی کدام است؟
_ops؟ octopus_core؟ app؟ 4d_system؟ ترکیبی؟
```

تا این معلوم نشود، هر اتصال/اجرا ریسک split-brain و drift دارد.
