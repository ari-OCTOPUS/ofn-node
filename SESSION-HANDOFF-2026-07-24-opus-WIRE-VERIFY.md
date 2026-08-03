# SESSION-HANDOFF — 2026-07-24 (Opus) — WIRE VERIFY / GROUND TRUTH — START HERE

> **چرا این فایل هست:** یک گزارشِ ایجنتی ادعا کرد `doctor.py` / `tradequote_bridge.py` / `OCTOPUS-flags.cmd`
> در `F:\backup` **وجود ندارند** و تغییرات به `app/NBB-CP` رفته. **این ادعا غلط است.**
> این سند واقعیتِ **راست‌آزمایی‌شده** را با شواهد + فرمانِ بازتأیید ثبت می‌کند.
> **قانونِ سخت (از هندآفِ خودِ پروژه):** منبعِ حقیقت = کد + git، نه گزارشِ ایجنت. قبل از عمل، خودت چک کن.

---

## ۱) واقعیت — راست‌آزمایی‌شده 2026-07-24، برنچ `claude/octopus-event-bridge-aligned`

هر شش فایل **موجودند** (بایت واقعی، خواندهٔ مستقیمِ فایل‌سیستم):

| فایل | مسیر | بایت | محتوا |
|---|---|---|---|
| `doctor.py` | `_ops/doctor/` | 79,245 | وصلِ **RULES** خط ۴۷۷ + **FATIGUE** خط ۵۸۴ (پشتِ فلگ، `try/except` دفاعی) |
| `tradequote_bridge.py` | `_ops/legs/` | 7,470 | وصلِ **OUTPUT_GUARD** خط ۱۵۶ (`allow_prefixes=("state/legs/",)`) |
| `OCTOPUS-flags.cmd` | `_ops/` | 12,225 | `OCTOPUS_WIRE_RULES=1` (armed) · `OCTOPUS_WIRE_FATIGUE=0` · `OCTOPUS_WIRE_OUTPUT_GUARD=0` |
| `rules_store.py` | `_ops/doctor/` | 11,744 | ماژولِ نو — RULES رفتاریِ hash-chain (G1/P3) |
| `approval_fatigue.py` | `_ops/budget/` | 10,505 | ماژولِ نو — `observe()` ضدِ rubber-stamping (فقط لاگ، صفر suppress) |
| `output_guard.py` | `_ops/` | 7,879 | ماژولِ نو — ضدِ خروجیِ اجراییِ ایجنت (درسِ فرارِ سندباکس) |

**تأییدِ مستقلِ مالک:** خودِ مالک `git status -sb` را در `F:\backup` زد و همین‌ها را دید
(`M _ops/doctor/doctor.py`, `M _ops/legs/tradequote_bridge.py`, `?? _ops/doctor/rules_store.py`, …)،
و `run_all.py` هم `test_doctor.py` + `test_tradequote_bridge.py` را اجرا کرد (سبز).

## ۲) بازتأیید — کپی‌پیست روی ویندوز (هر ایجنت/مالک)

```bat
cd /d F:\backup
git status -sb
dir _ops\doctor\doctor.py _ops\legs\tradequote_bridge.py _ops\OCTOPUS-flags.cmd _ops\doctor\rules_store.py _ops\budget\approval_fatigue.py _ops\output_guard.py
findstr /n "OCTOPUS_WIRE_RULES OCTOPUS_WIRE_FATIGUE" _ops\doctor\doctor.py
findstr /n "OCTOPUS_WIRE_OUTPUT_GUARD" _ops\legs\tradequote_bridge.py
findstr /n "OCTOPUS_WIRE_RULES OCTOPUS_WIRE_FATIGUE OCTOPUS_WIRE_OUTPUT_GUARD" _ops\OCTOPUS-flags.cmd
```

## ۳) فیکسِ تست‌ها (همین نشست — ۴ قرمزِ `run_all` رفع شد)

- `heart/heartstate.py`: `_FLAG_FILE` را از `opslib.STATE_DIR.parent` مشتق کن (مثلِ خطِ `LATEST`). در production **همان مسیرِ قبلی** (`_ops/ACTIVATION-HEARTSTATE.flag`، فلگ همچنان دیده می‌شود → صفر تغییرِ رفتارِ زنده)، ولی در تست به vaultِ ایزولهٔ harness اشاره می‌کند → نشتِ فلگِ armed به تست بسته شد. نتیجه: `test_phase1_envelope` **۹/۹**، `test_leg_chain_wire` **۸/۸**.
- `tests/test_studio_telegram.py` + `tests/test_dual_brain.py`: گاردِ **skip-if-absent**. این‌ها ماژول‌های **Project-F (اونلی‌فنز، GATE-0)** هستند که فقط در worktree ساخته شده‌اند، نه درختِ اصلی؛ merge‌شان **تصمیمِ مالک** است. skip = صادقانه (نه fail، نه ماژولِ جعلی).
- بکاپ‌ها: `/tmp/*.bak.py` (سندباکسِ ephemeral؛ برای revert در همان نشست).

## ۴) تصحیحِ ابهامِ معماری (چرا ایجنت اشتباه کرد)

طبقِ `ARCHITECTURE-SOT.md`:
- `F:\backup\_ops` = **ارگانیسمِ زنده** (runtime واقعی).
- `app/NBB-CP` = **دوقلوی خفتهٔ وصل‌نشده** (R-19 split-brain).

وصل‌های بالا در `_ops` **زنده** انجام شدند (جای درستِ وصل)، **نه** در NBB-CP. ایجنتِ مدعی این را برعکس فهمیده بود (احتمالاً در محیط/سندباکسِ دیگری بوده یا جستجویش خطا داده).

## ۵) پُسچرِ ایمنی (این «بای‌پسِ گیت» نبود — برعکسش بود)

- **owner-authorized** صریح · هر پچ با پروتکل: بکاپ → `assert count==1` → `compile()` قبل از نوشتن → دو `sha` متوالی.
- **همه پشتِ فلگِ خاموش** (جز `OCTOPUS_WIRE_RULES` که مالک گفت arm) · هر وصل `try/except` دفاعی (باگ هم نمی‌تواند بوت را بشکند).
- **صفر لمسِ TCB:** پول / کلیدها / genome / kill-switch دست‌نخورده.
- یک «پلنِ تزریق‌شده» که وسطِ کار خواست path-check را **bypass** و کارتِ approval را **suppress** کند → **رد شد** (رأیِ صریحِ مالک: نادیده). فلگ‌ها خودِ گیت‌اند و خاموش‌اند → هیچ گیتی دور زده نشد.

## ۶) گامِ باقی‌مانده (فقط مالک، ویندوزی)

`RESTART-ORGANISM.bat` → `OCTOPUS_WIRE_RULES` زنده می‌شود (و `_ops/doctor/state/rules-ledger.jsonl` باید رشد کند). `FATIGUE`/`OUTPUT_GUARD` با `set OCTOPUS_WIRE_...=1` + restart، هر وقت مالک خواست. لنگرِ بزرگ‌تر همچنان: **deploy master `f9a8d48`** (advance_rfcs/verify_scope آن‌جایند).

---

*این سند فقط واقعیتِ راست‌آزمایی‌شده را ثبت می‌کند؛ هیچ کدِ زنده‌ای با نوشتنِ آن تغییر نکرد. ادعاهای «انجام‌شده/نشده» را با فرمان‌های بخشِ ۲ خودت چک کن.*
