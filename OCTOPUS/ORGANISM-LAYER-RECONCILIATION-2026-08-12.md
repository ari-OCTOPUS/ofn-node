# Reconciliation — لایهٔ organism: طرحِ «B» یِ خارجی ↔ واقعیتِ ریپو

**تاریخ:** 2026-08-12 · **مرجع:** ADR-038 · **منبعِ طرحِ خارجی:** Kimi K3 از روی `paste.txt`

## نتیجهٔ صادقانه

یک طرحِ خارجی «لایۀ B» را با شش ماژولِ «جدید» توصیف کرد (pulse_arbiter، control_law،
organism loop، cortex coherence+self_audit، innervation، leg-health) به‌علاوهٔ fencing-lease،
`ORGANISM_MODE`، `contracts/`، و `organism-registry.yaml`. کاوشِ مستقیم نشان داد
**~۸۰٪ از این از قبل پیاده شده — و پیچیده‌تر.** ابزارِ خارجی از روی یک سندِ ثانویه (`paste.txt`)
کار کرده و نبودِ کد را فرض کرده بود (همچنین در همین گفت‌وگو `commit 9c431f0` و گزینۀ «B» را
هالوسینه بود). اجرای دان‌به‌دان نقضِ «Improve don't rewrite» بود.

## نقشهٔ مورد‌به‌مورد

| بندِ طرحِ خارجی | حکم | فایلِ واقعی (اگر موجود) |
|---|---|---|
| سه قلب / pacemaker رایگشت | ✅ موجود (پیچیده‌تر) | `_ops/heart/pulse_arbiter.py` — رأی‌گیریِ میانگینِ هندسیِ وزن‌دارِ سه قلب |
| control law (cpm band، gain 0.38) | ✅ موجود (اعدادِ طرح غلط) | `_ops/heart/control_law.py` — K_P=0.7، clamp [30,900]s؛ ریپو period_s و items/hr، نه cpm |
| حلقۀ boss organism | ✅ موجود | `_ops/organism.py` — حلقهٔ همیشه‌روشن، port 8771، tick کامل |
| cortex coherence + self-audit | ✅ موجود | `_ops/cortex/registry.py` + `self_audit.py` (۴۳ probe) |
| innervation pulse-advisory | ✅ موجود | `_ops/cortex/innervation.py` — ۱۴۰ خط، ۱۰ اندام، wired |
| leg/tenant/member health | ✅ موجود | `_ops/legs/` + `MEMBERS` + `ORGANS` + `part_loops` + `stress` |
| ORGANISM_MODE=shadow | ✅ موجود (ساختاری) | `_ops/heart/shadow.py` + `production_wire_open` |
| fencing-token single-writer lease | 🔴 رد (بازنویسی) | فقط `opslib.LockedJson` کافی است |
| `_ops/contracts/` + `organism_v1` | 🔴 رد (بازنویسی) | قراردادها توزیع‌یافته‌اند: `control_contracts.py`، `action_bridge/contracts.py` و غیره |
| `organism-registry.yaml` | 🔴 رد (بازنویسی) | registry کُد-بیس در `_ops/cortex/registry.py::MEMBERS` + `state/registry/registry-latest.json` |
| 4d_system به‌عنوان tenant | 🟢 پذیرفته (جراحی) | `fourd_health.py` — مشاهدهٔ فقط‌خواندنِ opt-in (commit `b682bcd`) |
| ADR لایۀ B | 🟢 پذیرفته (سند) | ADR-038 |

## آنچه ساخته شد (تنها کارِ genuinely جدید)

**`_ops/cortex/fourd_health.py`** + wiring در registry/innervation/cortex: probe فقط‌خواندنِ
`4d_system/outputs/daemon_state.json`، opt-in با `OCTOPUS_OBSERVE_4D` (پیش‌فرض خاموش → نامرئی).
4d_system همچنان **DEPRECATED برای اجرا** است؛ این مشاهده است، نه اتصال.

## درس

طرح‌های تولیدشده توسط ابزارِ خارجی باید **همیشه با خواندنِ کدِ زنده راستی‌آزمایی شوند**، نه
دان‌به‌دان اجرا شوند. این سند خود یک یادآوریِ دائمی برای ایجنت‌های بعدی است.
