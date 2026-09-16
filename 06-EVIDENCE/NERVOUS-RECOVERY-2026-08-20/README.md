---
type: evidence
created: 2026-08-20
updated: 2026-08-20
tags: [octopus, wave0, nervous-recovery]
---

# Nervous-System Recovery — 2026-08-20

GitHub public `owner/repo`: **UNLOCATED**. Remote واقعی: `germline E:/germline/octopus.git`.

## حکم زنده

**WAVE0_PASS** · `wave1_unlocked=false` · Wave 1 **باز نشد** (فرمان جداگانه لازم است).

Verifier: `WAVE0-VERIFIER.json` · candidate: `WAVE0_PASS_CANDIDATE.json` · final: [[WAVE0_PASS]]

فاز ۱ (shadow): [[PHASE1-SHADOW]] · پنجرهٔ امروز: `duplicate=0` · `fabricated=0` · schema=100% · hash coverage=100%. رسید اصلی دست‌نخورده (sha256 `2e9f84a7…` · 977 خط).

## گیت‌های Wave 0

منبع: `WAVE0-GATES.json` (پس از verifier)

| Gate | اکنون | آستانه | pass |
|---|---|---|---|
| Receipt attribution (schema-present) | 1.0 (51/51) | ≥0.95 | **true** |
| Receipt attribution (today-full forensic) | 0.3423 (51/149) | — | not the gate |
| Test registry | 786/786 · gap=0 | gap=0 | **true** |
| Memory continuity | 15 consecutive | ≥10 | **true** |
| Capability inventory | parse n=10 | parse>0 | **true** |

Immune: ۵ `DECLARED_UNOBSERVED` + ۵ `DORMANT`. صفر `VERIFIED` (receipt+test لازم است؛ نبود receipt ≠ DORMANT).

## تست

۱۵ تابع در `test_nervous_recovery.py` · در `run_all.py` ثبت شد · اجرای مستقیم سبز. `run_all` کاملِ ۷۸۶ سوئیت اجرا نشد (محدودیت زمان).

## ریل B / C

پیاده نشد. C-048..C-053 کاندید ماندند. `01-TRUTH/CONTRADICTIONS.md` نوشته نشد.
