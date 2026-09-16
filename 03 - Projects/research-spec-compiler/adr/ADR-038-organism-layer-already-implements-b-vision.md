# ADR-038: لایهٔ organism از قبل چرخانِ «B-vision» را پیاده کرده — فقط یک افزودنیِ جراحی

**وضعیت:** ACCEPTED — رأیِ مالک 2026-08-12 (گزینۀ «اضافۀ جراحی: 4d_system»)
**تاریخ:** 2026-08-12 · **شماره:** 038 (بعد از ADR-037)

---

## زمینه

یک طرحِ خارجی (Kimi K3، از روی `paste.txt`) «لایۀ B» را چنین پیشنهاد داد: سه‌قلبِ افزونه با
fencing-token single-writer lease، control law با باندِ cpm، قراردادِ versioned‌ِ organism،
`organism-registry.yaml`، و `ORGANISM_MODE=shadow`. کاوشِ مستقیمِ ریپو نشان داد **بیش از ۸۰٪
از این طرح از قبل پیاده شده — آن هم پیچیده‌تر.** اجرای دان‌به‌دانِ آن نقضِ مستقیمِ
«Improve don't rewrite» بود.

## تصمیم

**۱. بازنویسی‌ها رد شدند.** مواردِ زیر از قبل موجودند و نباید دوباره ساخته بشوند:

| موردِ طرحِ خارجی | فایلِ موجود (واقعی) |
|---|---|
| سه قلب / pacemaker رایگشت | `_ops/heart/pulse_arbiter.py` — سه قلب با رأی‌گیریِ میانگینِ هندسیِ وزن‌دار (پیچیده‌تر)؛ امروز advisory-only |
| control law (cpm band + gain) | `_ops/heart/control_law.py` — K_P=0.7، clamp [30,900]s، CPI/budget/futility/E_shadow. (اعدادِ cpm/0.38 طرح، اختراعی بودند — ریپو period_s و items/hr) |
| حلقۀ boss organism | `_ops/organism.py` — حلقۀ همیشه‌روشن، port 8771 انحصاری، tick کامل |
| cortex coherence + self-audit | `_ops/cortex/registry.py` (sweep) + `_ops/cortex/self_audit.py` (۴۳ probe) |
| innervation pulse-advisory | `_ops/cortex/innervation.py` — ۱۴۰ خط، ۱۰ اندام، wired |
| leg/tenant/member health | `legs/` + `MEMBERS` + `ORGANS` + `part_loops` + `stress` |
| ORGANISM_MODE=shadow | الگوی shadow ساختاری موجود (`heart/shadow.py` + `production_wire_open`) |
| fencing-token lease | رد — فقط `LockedJson` کافی است؛ fencing بازنویسیِ معماریِ ایمنیِ کارا بود |

**۲. fencing-token lease، `_ops/contracts/`، `organism-registry.yaml`، `ORGANISM_MODE` enum
به‌طور صریح رد شدند** (بازنویسی، بدونِ سود بر سرِ الگوهای موجود).

**۳. تنها کارِ genuinely جدید پذیرفته شد: مشاهدهٔ فقط‌خواندنِ 4d_system.** تا امروز
`blackbox_map.py` آن را «DEPRECATED — وصل به ارگانیسمِ زنده نیست» علامت زده. این ADR
آن را به‌عنوان یک عضوِ **فقط‌مشاهدۀ opt-in** در sweepِ coherence/innervation ثبت می‌کند
(`_ops/cortex/fourd_health.py`، commit `b682bcd`) — بدونِ هیچ مسیرِ اجرا.

## مرزِ سخت (افزودنیِ پذیرفته‌شده)

- فقط‌خواندن: هیچ import از 4d_system، هیچ write به آن، هیچ اتصالِ اجرایی (دستۀ `read_only`
  از `autonomy_grant`).
- پیش‌فرض خاموش (`OCTOPUS_OBSERVE_4D=0`): وقتی خاموش است، 4d_system برای coherence
  **نامرئی** است (نه stale، نه نویز).
- absence ≠ healthy: نبودِ `daemon_state.json` = "missing"، هرگز "fresh".

## پیامدها

- **مثبت:** مشاهده‌پذیریِ صادقانهٔ لایول‌نسِ 4d_system (الان نامرئی است)؛ صفر مسیرِ اجرا/اختیارِ جدید؛
  بدونِ بازنویسیِ کدِ سالم.
- **هزینه:** یک probe کوچک + سه ویرایشِ افزودنی.
- **خنثی‌شده:** 4d_system همچنان DEPRECATED برای اجراست — این مشاهده است، نه اتصال.

## بدیل‌های ردشده

- **اجرای کاملِ طرحِ خارجی:** بازنویسیِ شش ماژولِ تولیدی → رد (ضدِ Improve-don't-rewrite).
- **fencing-token lease:** بازنویسیِ معماریِ ایمنیِ کارا → رد.
- **`ORGANISM_MODE` enum / `organism-registry.yaml`:** بازنویسیِ الگوی shadow/registryِ موجود → رد.
