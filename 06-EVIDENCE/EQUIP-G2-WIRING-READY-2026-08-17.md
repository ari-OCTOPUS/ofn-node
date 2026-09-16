---
type: evidence
session: EQUIP G2 production wiring — owner-approved, sandbox-tested, ready for TCB ceremony
agent: Claude Sonnet 5 (Claude Code)
created: 2026-08-17 ~21:5x
mode: propose-only for the live file — sandboxed apply+test only, real automation.py untouched
---

# EQUIP G2 وصل به تولید — پچِ آماده، تست‌شده در سندباکس

## چرا مستقیم اعمال نشد
`4d_system/brain/automation.py` در لیستِ TCB است (`4d_system/config/trust-boundary.json:tcb.files`). دیمونِ 4d همین امروز (پین `4D-DAEMON-RESTART-2026-08-17`) با `OCTOPUS_TCB_MANIFEST_ENFORCE=1` ریاستارت شد. ویرایشِ مستقیمِ این فایل بدونِ بازساختِ manifest+امضا، تیکِ بعدیِ `_job_guard` را `tampered=True` می‌بیند و دیمونِ تازه‌ریاستارت‌شده را halt می‌کند. امضا با کلیدِ خصوصیِ مالک (`C:\Users\Armin\.octopus-signing\`) انجام می‌شود — بیرونِ اختیارِ ایجنت، هم‌الگو با C-026/C-029/C-033.

## چه چیزی آماده است
`00 - Inbox/PATCH-EQUIP-G2-automation-writegate-2026-08-17.patch` — دیف یونیفایدِ تمیز (۲ hunk، ۳۳ خطِ افزوده، صفر حذف):
1. `from pathlib import Path` (نبود، لازم شد).
2. بعد از موفقیتِ `save_hypothesis()` + read-back، `stamp_hypothesis_with_gate()` صدا زده می‌شود — **فقط سایه/ممیزی**، verdict فقط لاگ می‌شود، رفتار/بازگشتِ `_job_create()` عوض نمی‌شود.

## چرا `source="deterministic"` و نه چیزِ دیگر
`_creative_idea()` (خطِ ۴۱۱-۴۲۱) از `random.Random(self._create_i*131+7)` می‌آید — شمارندهٔ داخلیِ صرف، صفر شبکه/LLM. این را امروز مستقیماً در تستِ سختِ S1 اثبات کردم (متنِ ایده بین DB تمیز/مسموم بایت‌به‌بایت یکسان بود). پس طبقهٔ درستِ این منبع در `_TRUSTED_SOURCES`ِ `write_gate_enforcer.py` واقعاً `"deterministic"` است، نه `"llm:create"` — برچسبِ غلط اینجا خودش یک نمونهٔ الگویِ C (تله‌متریِ گمراه‌کننده) می‌ساخت.

## چرا importlib به‌جای import معمولی
`_ops/memory/write_gate_enforcer.py` و `4d_system/memory/*` دو پکیجِ کاملاً جدا با نامِ یکسانِ `memory` هستند. `from memory.write_gate_enforcer import ...` داخلِ `automation.py` به پکیجِ خودِ 4d resolve می‌شود (که چنین ماژولی ندارد) — **در اولین تلاشِ من دقیقاً همین اتفاق افتاد و ساکت (try/except) شکست، بدونِ کرش ولی بدونِ اثر.** فیکس: `importlib.util.spec_from_file_location` با مسیرِ مطلقِ مشتق‌شده از `Path(__file__).resolve().parents[2]` — هم‌الگو با فیکسِ سایه‌پکیجِ `_doctor_ingest` در `center.py`.

## راستی‌آزماییِ سندباکس [A]
کپیِ کاملِ `4d_system` (بدونِ `outputs/__pycache__/chroma_db`) + فقط فایلِ stdlib-only `write_gate_enforcer.py` کنارش (هم‌الگو با چیدمانِ واقعیِ `F:\backup`)؛ پچ رویِ کپی اعمال شد، `AutomationController(use_llm=False)._job_create()` سه‌بار زده شد:

| بررسی | نتیجه |
|---|---|
| بازگشتِ `_job_create()` | بدونِ تغییر (همان `{"ok","mode","summary"}`) |
| فایلِ `write-gate-audit.jsonl` | ۳ ردیف، یکی به‌ازای هر فرضیهٔ ذخیره‌شده |
| هر ۳ ردیف | `verb=commit · source_class=trusted · content_hash درست · writer_agent=automation._job_create` |
| اجراهای بعدی (اسکریپتِ اول، بدونِ importlib) | شکستِ خاموشِ صحیح‌گرفته‌شده — «No module named 'memory.write_gate_enforcer'» تویِ لاگ، صفر کرش |

اسکریپتِ سندباکس + پچ‌ساز در `scratchpad` (نه vault) ماندند — قابلِ‌بازتولید از خودِ متنِ `.patch`.

## مراسمِ لازم از دستِ مالک (~۲ دقیقه، هم‌الگویِ C-026)
```
1. git apply "00 - Inbox/PATCH-EQUIP-G2-automation-writegate-2026-08-17.patch"
2. بازسازیِ digest manifest (همان اسکریپتی که برای C-026/C-033 استفاده شد)
3. امضای Ed25519 با کلیدِ owner-signing
4. RESTART دیمونِ 4d (رویهٔ همین شب: `06-EVIDENCE/4D-DAEMON-RESTART-2026-08-17.md`)
5. راستی‌آزماییِ زنده: چک کردنِ اولین ردیفِ `4d_system/outputs/write-gate-audit.jsonl` بعد از یک تیکِ create
```

## کارِ باز
- الان فقط سایه است — quarantine/reject هیچ اثری روی جریان ندارد. اگر مالک بخواهد enforce شود (رد کردنِ واقعیِ محتوایِ نامعتبر)، آن یک رأیِ جداست.
- فقط `_job_create` وصل شد. اگر بعداً مسیرِ ورودیِ بیرونی/LLM اضافه شود (VOTE 1 در گزارشِ حافظه)، آن مسیر باید از روزِ اول از همین گیت رد شود، نه بعداً.
