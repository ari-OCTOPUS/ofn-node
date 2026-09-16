# OCTOPUS MAX-AUTONOMY ROADMAP
## نقشه خودآگاهی و حداکثر اختیار

> **وضعیت:** نهایی — 2026-08-16
> **مالک:** Armin
> **اصل:** بررسی تمام خودآگاهی، دادن حداکثر اختیار — با شفافیت مطلق

---

## ۱. تصمیمات نهایی مالک (۸ تصمیم)

| # | سؤال | تصمیم |
|---|------|-------|
| ۱ | halt | consensus halt — فقط موافقت هر دو مغز |
| ۲ | مبادله بودجه | آزاد با لاگ |
| ۳ | fallback | پله‌ای: Fugu/DeepSeek=execute, GLM/Ollama=propose |
| ۴ | A2/A4 | A2=خودکار, A4=فقط مالک |
| ۵ | self_improve | همه به جز TCB و safety gates |
| ۶ | ماژول خاموش | هر ۱۰ beat heartbeat OFF |
| ۷ | پاها | دسترسی مشترک — تقسیم بر اساس نوع تصمیم |
| ۸ | نوشتن | مستقیم browser در F:\backup |

---

## ۲. ۷ لایه خودآگاهی

| لایه | وضعیت | اقدام |
|------|-------|-------|
| L0 Body | ✅ واقعی | — |
| L1 Senses | 🟡 نیمه‌کور | وصل afferent |
| L2 Memory | 🔴 write-only | وصل read + intel_spine |
| L3 Understanding | 🟡 ناشنیده | وصل به spine |
| L4 Decision | 🟡 تعمیر | وصل chord + hypothesis |
| L5 Action | 🟡 propose | وصل action_bridge (A2=auto) |
| L6 Interface | ✅ غنی | — |
| L8 Safety | ✅ بالغ | اصلاح HEARTSTATE bug |

---

## ۳. وصل‌کردن ماژول‌های خاموش

| مرحله | ماژول | پرچم | پایش |
|--------|-------|------|------|
| ۱ | Event Spine | OCTOPUS_WIRE_SPINE | ۱ هفته |
| ۲ | Intel Spine | OCTOPUS_INTERACTION_LOG | ۱ هفته |
| ۳ | Afferent | OCTOPUS_WIRE_AFFERENT | ۱ هفته |
| ۴ | Synapse | SYNAPSE_ENABLED | ۱ هفته |
| ۵ | Chord | OCTOPUS_WIRE_CHORD | ۱ هفته |
| ۶ | Action Bridge | runtime caller | ۱ هفته |
| ۷ | 4d_system wiring | FOURD_* | ۱ هفته |

---

## ۴. رودمپ اجرا

### فاز ۱: بنیان (هفته ۱-۲)
- [ ] نوشتن این سه سند در F:\backup
- [ ] وصل Event Spine
- [ ] اصلاح HEARTSTATE audit bug
- [ ] commit درخت dirty
- [ ] heartbeat OFF برای ماژول‌های خاموش

### فاز ۲: اتصال مغزها (هفته ۳-۴)
- [ ] وصل 4d_system به data layer
- [ ] پیاده‌سازی dual veto
- [ ] پیاده‌سازی consensus halt
- [ ] وصل Intel Spine + Afferent
- [ ] تخصیص heartbeat budget سه‌بعدی
- [ ] پیاده‌سازی مبادله آزاد بودجه

### فاز ۳: خودمختاری و fallback (هفته ۵-۶)
- [ ] وصل Action Bridge (A2=auto)
- [ ] وصل Synapse + Chord
- [ ] fallback provider (Fugu→DeepSeek→GLM→Ollama)
- [ ] downgrade پله‌ای
- [ ] self_improve_auto (به جز TCB)

### فاز ۴: حداکثر اختیار (هفته ۷-۸)
- [ ] بررسی خودآگاهی (doctor 500+)
- [ ] حداکثر خودمختاری + شفافیت
- [ ] همه ماژول‌ها heartbeat
- [ ] گزارش صادقانه
- [ ] ممیزی مستقل D1

---

## ۵. ۱۱ عضو — هدف نهایی

| # | عضو | وضعیت هدف |
|---|------|-----------|
| ۱ | organism | زنده |
| ۲ | heart | زنده |
| ۳ | producers | زنده |
| ۴ | work_pump | بهبود awareness |
| ۵ | doctor_setpoint | بهبود |
| ۶ | governor | زنده |
| ۷ | sigma | زنده |
| ۸ | fitness | زنده |
| ۹ | school | زنده |
| ۱۰ | reconcile | زنده |
| ۱۱ | fourd_system | وصل‌شده |
