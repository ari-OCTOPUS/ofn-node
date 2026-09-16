# اونلی فنز (Project-F) — کپیِ Portable برای Orange Pi 5

> نسخهٔ مستقل · ۲۰۲۶-۰۸-۰۳ · ۴۲۶/۴۲۶ تست سبز ✓

##这是什么 (What this is)
این یک کپیِ **خودکفا و قابل‌حمل** از پروژهٔ «اونلی فنز» (Project-F) است که می‌تواند
**مستقل از کلِ vault اختاپوس** اجرا شود. همهٔ وابستگی‌های ضروریِ `_ops/` (۱۳ فایل)
داخل همین بسته هست.

## ساختار
```
vault/                              ← ریشه (نام دلخواه، مسیرها relative‌اند)
├── 03 - Projects/
│   └── اونلی فنز/                  ← پروژهٔ اصلی
│       ├── orchestrator.py         ← چسبِ زندهٔ همهٔ لایه‌ها
│       ├── pf_os/                  ← OS ماژولار (loop/api/bridge — همه flag-OFF)
│       ├── brain/                  ← مغز (DualBrainV3، acquisition، learning)
│       ├── studio/                 ← استودیوی محتوای صبا
│       ├── langar/                 ← کاکپیت تلگرامی Operator
│       ├── tests/                  ← ۴۲۶ تست (همه سبز)
│       └── conftest.py             ← تست‌ها را به tmp می‌برد (ایزوله)
└── _ops/                           ← حداقلِ وابستگی‌های اختاپوس (۱۳ فایل)
    ├── events.py
    ├── budget/opslib.py
    ├── neural/                     ← neural_driver، hebbian، consolidation، sprint، hooks، circadian، nociceptor، reflex، signal_hub
    ├── telegram_center/pf_miniapp.py
    └── legs/studio_pf_leg.py
```

## اجرا روی Orange Pi 5
```bash
# ۱. فایل zip را باز کن
unzip onlyfans-portable-2026-08-03.zip -d ~/project-f

# ۲. پایتون ۳.۱۱+ لازم است (روی ۳.۱۳ تست شده)
python3 --version

# ۳. pytest لازم است
pip install pytest

# ۴. تست‌ها را اجرا کن (باید ۴۲۶ passed ببینی)
cd ~/project-f/vault/03\ -\ Projects/اونلی\ فنز
python3 -m pytest -q

# ۵. orchestrator را امتحان کن (shadow mode، همه flag‌ها OFF)
python3 orchestrator.py    # یا import کن
```

## وضعیت فعلی (همه flag-OFF = shadow/propose-only)
| Flag | وضعیت | معنی |
|---|---|---|
| `OCTOPUS_WIRE_PROJECTF_LOOP` | OFF | حلقهٔ tick خاموش |
| `OCTOPUS_WIRE_PROJECTF_API` | OFF | REST API روی :8780 خاموش |
| `OCTOPUS_WIRE_SABA_BRIDGE` | OFF | نوشتن به saba-bridge.jsonl خاموش |
| `OCTOPUS_WIRE_PROJECTF_CORTEX` | OFF | فراخوانیِ cortex → heuristic fallback |
| `OCTOPUS_WIRE_PROJECTF_EVAL` | OFF | حلقهٔ eval/learn خاموش |
| `OCTOPUS_WIRE_PROJECTF_SPINE` | OFF | انتشارِ یکپارچه خاموش |

**هیچ کاری outward انجام نمی‌شود.** همه‌چیز advisory/propose-only است.

## تغییراتِ این نسخه (نسبت به نسخهٔ اصلی)
1. **فاز ۱**: ۷ موردِ import-time path binding به lazy resolution تبدیل شد
   (ریشهٔ ۲ شکست تست). الگوی مرجع: `pf_os/saba_link.py::_studio_dir()`.
2. **فاز ۲**: ۴ `MODULE.md` برای pf_os/brain/studio/langar اضافه شد.
3. **فاز ۳**: `opslib` import در orchestrator fix شد (`_ops/budget` به sys.path).
4. **فاز ۴**: مستندسازیِ فنس در `cortex_client.py` (server-side fenced، client-side redundant).

## نکات برای ایجنتِ ارشد
- **PII**: این کپی شامل دادهٔ شخصی واقعی است (پرسشنامهٔ پارتنر، drafts، حافظه).
  با احتیاطِ کامل برخورد کنید.
- **GATE 0**: محل اقامت پارتنر ثبت نشده → هیچ‌چیز outward اجرا نمی‌شود.
- **معماری**: هر subsystem مستقل است. `pf_os` از طریق فایل (نه import مستقیم)
  با brain/studio/langar صحبت می‌کند. با اختاپوس از طریق cortex HTTP (:8772)
  و saba-bridge.jsonl صحبت می‌کند.
- **تست**: همیشه قبل از تغییر، `pytest -q` بزنید. ۴۲۶ باید سبز بماند.

## محدودیت‌ها
- `cortex` مرکزی در این کپی **نیست** (فقط client). وقتی `WIRE_CORTEX=1` روشن شود
  و cortex نباشد، fallback به heuristic می‌رود (طراحی‌شده، نه خطا).
- `growth_arch/` (Node.js) جداگانه است و در تست‌های پایتون شرکت نمی‌کند.
