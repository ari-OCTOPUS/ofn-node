---
type: proposal
project: "[[04 - Architect System/architect/PROJECT]]"
status: draft-for-verdict
created_by: agent
relates_to: "_ops/live_loop.py · _ops/unified_bus.py · همهٔ اجزا · [[DOCTOR-BOX-OF-AGENTS-SPEC]] (fractal/constructal)"
tags: [octopus, architecture, cell, brain, comms, review, propose-only]
created: 2026-07-09
updated: 2026-07-09
---

# CELL ARCHITECTURE REVIEW — «هر جزء = مغزِ مستقل + ارتباطات»

> اودیت + طرح. هدف: هر جزء یک **سلولِ خودمتشابه** باشد = هسته (Brain: تصمیمِ محلی) + غشا (Comms: اتصالِ خودش به bus) — نه اسپوکِ نازکی که یک هابِ مرکزی (`live_loop`) از بیرون سیمش کند.

## ۱. یافتهٔ اودیت (اعداد واقعی)
| جزء | Brain (تصمیم) | Comms (bus خودش) | حکم |
|---|---|---|---|
| chrono/heart | ✅ | ✅ (۱۳) | سلولِ کامل |
| chrono_rhythm | ✅ | ✅ | سلولِ کامل |
| sensory_bus | ~ (classifier) | ✅ (۳) | تقریباً |
| doctor | ✅ | ❌ (۰) | مغز دارد، غشا نه |
| box / evolution / spectral | ✅ | ❌ | مغز دارد، غشا نه |
| project-f brain | ✅ (۷ زیرعامل) | ❌ (route via live_loop) | مغز دارد، غشا نه |
| school | ✅ (diffusion) | ~ | مغز دارد، غشا ناقص |
| legs (Lead-نقاشی…) | ~ (executor) | ❌ | نازک |
| cockpit آری / studio صبا | ❌ (UI) | studio ✅ / cockpit ❌ | UI، مغزِ محلی ندارد |
| watchdog / germline / checkpoint | ~ | ❌ | ابزار، غشا نه |
| **live_loop** | ❌ | ✅ (۱۵) | **هابِ متمرکزِ سیم‌کشی** |
| unified_bus | — | (backbone) | زیرساخت |
| ledger | (حافظه) | — | substrate، نه سلول |

**نتیجه:** comms در چند هاب (`live_loop`/`chrono`/`bus`) متمرکز است؛ اکثرِ اجزا `comms:0`اند و از بیرون سیم می‌شوند. هیچ قراردادِ واحدِ Cell نیست.

## ۲. دو مشکل
1. **هابِ متمرکز (`live_loop`):** SPOF/گلوگاه — همه از یک نقطه وصل‌اند. برخلافِ اصلِ constructal/small-world (که خودمان §Part 11 گذاشتیم: partial-mesh نه ستاره‌ی تک‌مرکز).
2. **بدونِ یکنواختی:** هر جزء ساختارِ خودش را دارد؛ نمی‌شود یکسان restart/monitor/test کرد.

## ۳. طرح — الگوی واحدِ `Cell`
هر جزء یک `Cell` را پیاده کند (زیست‌الگو: هسته + غشا):
```
Cell:
  brain(perceive, state) -> Proposal | None      # تصمیمِ محلیِ propose-only
  comms:                                          # غشای خودِ سلول
     on_start(): bus.subscribe(topics_i)          # خودش subscribe می‌کند
     emit(proposal): bus.publish(...)             # خودش publish می‌کند
  health() -> {alive, stress, last_beat}          # برای watchdog/doctor
  identity: cell_id, role, capabilities, budget_share
```
- **غشا مالِ خودِ سلول است:** هر سلول خودش subscribe/publish می‌کند → `live_loop` از «سیم‌کشِ reach-in» به یک **رجیستری/ارکستریتورِ نازک** کوچک می‌شود (فقط ثبتِ سلول‌ها + ترتیبِ beat). حذفِ hubِ SPOF.
- **مغزِ محلی:** حتی سلولِ نازک (leg/UI) حداقل یک policyِ کوچکِ محلی دارد (نه صرفاً executor).
- **خودمتشابهی (fractal):** هر سلول یک مینی-ارگانیسم است؛ همان الگو در هر مقیاس → monitor/restart/test یکسان.

## ۴. نگاشتِ اقدام
| جزء | اقدام |
|---|---|
| doctor · box · evolution · spectral · project-f brain | **غشا اضافه کن** (خودش subscribe/publish) — مغز آماده است |
| legs · cockpit | **مغزِ محلیِ حداقلی** + غشا |
| watchdog · germline · checkpoint | wrap در Cell (health/comms) |
| chrono · rhythm · sensory | تقریباً سلول‌اند — فقط قراردادِ Cell را رسمی کن |
| live_loop | **لاغر شود** → رجیستری + beat-order (نه سیم‌کشِ reach-in) |
| ledger · unified_bus | بی‌تغییر (substrate/backbone) |

## ۵. خطِ قرمزِ ایمنی (مهم)
«مغزِ مستقل برای هر جزء» ≠ **یک LLM برای هر جزء.** مغز = تصمیمِ محلیِ عمدتاً **ارزان/عددی/قاعده‌ای**؛ LLM فقط جایی که واقعاً لازم است، از میانِ boxِ ۲٪-capped. وگرنه: انفجارِ بودجه + agreement-spiral + همان failure-modeِ «۴۰٪ پروژه‌های agentic تا ۲۰۲۷ کنسل». پس:
- همه propose-only · human-append برای هر اثر · λ_persist<0 (هیچ سلول بقای خودش را optimize نمی‌کند) · سهمِ بودجهٔ هر سلول capped.
- **سلولِ بیشتر ≠ خودمختاریِ بیشتر** — فقط ساختارِ یکنواخت‌تر و غیرمتمرکزتر.
- migration **additive/non-destructive:** `live_loop` حین مهاجرت کار کند؛ سلول‌ها یکی‌یکی رسمی شوند.

## ۶. پرامپتِ GLM
```
تو کارگرِ کدنویسِ Octopus (GLM) هستی. الگوی واحدِ Cell را پیاده کن و اجزا را روی آن رفکتور کن. additive/non-destructive، propose-only، commit با مالک.
گام ۰ ضدِتکرار: grep -rln "class Cell\|def emit\|self.bus.subscribe" _ops/ | grep -v __pycache__.
گام ۱ بخوان: CELL-ARCHITECTURE-REVIEW.md + unified_bus.py + live_loop.py + doctor/*, box/*, legs/*, brain/cockpit.py. PLAN بده.
بساز:
1) _ops/cell.py — کلاسِ پایهٔ Cell (brain: perceive→Proposal|None · comms: on_start=خود-subscribe / emit=خود-publish · health() · identity+budget_share).
2) اجزای مغزدار (doctor, box, evolution, spectral, project-f brain) را در Cell بپیچ: خودشان subscribe/publish کنند (غشای خودشان) — منطقِ موجود دست‌نخورد.
3) اجزای نازک (legs, cockpit) یک policyِ محلیِ حداقلی + غشا بگیرند.
4) live_loop را لاغر کن → رجیستریِ سلول‌ها + ترتیبِ beat؛ سیم‌کشیِ reach-in را deprecate (نه delete) کن. مسیرِ قدیمی سبز بماند حین مهاجرت.
خطِ قرمز (نقض=رد): مغز = محلی/ارزان، LLM فقط via boxِ ۲٪-cap · propose-only · human-append برای اثر · λ_persist<0 هر سلول · advisory بی‌اثر · ساعتِ لجر deterministic · additive (live_loop حین migration کار کند) · بدونِ git commit.
تست‌ها ($0): هر سلولِ رفکتورشده خودش subscribe/publish می‌کند · یک event از سلول→bus→سلول بدونِ live_loopِ reach-in می‌رسد · health() برای watchdog کار می‌کند · هیچ سلول اثر settle نمی‌کند بدونِ human-append · مسیرِ قدیمی هنوز سبز · λ_persist منفی. خروجیِ خامِ run_all را paste کن.
DoD: Cell base + حداقل ۳ سلولِ رفکتورشده سبز، live_loop لاغرتر، مسیرِ قدیمی دست‌نخورده. ORGANISM-SPEC + HANDOFF آپدیت. هر ابهام → «⚑ برای معمار».
```

## Sources
اودیتِ کدِ `_ops/` (2026-07-09) · [[DOCTOR-BOX-OF-AGENTS-SPEC]] §Part 11 (constructal/fractal) · `_ops/unified_bus.py` · `_ops/live_loop.py`
