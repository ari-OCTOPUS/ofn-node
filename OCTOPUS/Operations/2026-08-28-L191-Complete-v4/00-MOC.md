---
project: OCTOPUS
mission_id: OCTOPUS-L191-COMPLETE-v4
status: PARTIAL
baseline_sha: 7154675dc66afda88feb102afcf0a057e8b1a540
evidence_bundle_sha256: eafae79996b3dfd15af2dc84fe4ae757af06ee7b53a97571f09071ce86c4c89b
updated_at_utc: 2026-08-28T11:55:00Z
tags: [octopus, operations, l191, evidence]
---

# MOC — OCTOPUS-L191-COMPLETE-v4 (Waves 1-2)

- [[01-REPOSITORY-BASELINES]] — ofn-node کامل (@68813370 پاک) + langar (@4ff00f31) + Armin (@fcaca746)؛ ‏CTR-01..04
- [[03-ADAPTER-CENSUS]] — census واقعی چهارجذبی: ‏۲۲۸ ماژول؛ ‏LIVE=۴ (systemd-anchored)؛ ‏SHADOW=۹۰؛ کشف BOM در brainport
- [[04-T0-REALITY-LOCK]] — تک-llama:8081؛ ‏sha سومین تأیید؛ گارد ExecStartPre طلایی؛ **cgroup throttle زنده؛ OOM مرده**
- [[05-RUNTIME-PATH]] — زنجیره کامل؛ **EDGE-6 = PROVEN_BROKEN (FACT)**: spine handler بدون persist/transmit برمی‌گردد؛ ترمیم ۳خطی (OD-30)
- [[07-SAFETY-COST-GUARDS]] — نقشه گاردها؛ lab پیشوند-cache ثبت؛ اسکیمای بودجه
- [[08-ARCHITECTURE-DECISIONS]] — ۱۳ ADR + حل ‏CTR-03/04
- [[09-ACCEPTANCE-TESTS]] — ۲۰ تست: ‏۹ PASS · ‏۱ PARTIAL · ‏۲ BLOCKED_GO-E · ‏۷ آماده
- [[10-OWNER-DECISIONS]] — **OD-30 (پچ EDGE-6، منتظر رأی شما)** · ‏OD-31 (بودجه T1) · ‏OD-32

## ایستگاه فعلی
موج ۵ (بستن زنجیره) فقط با GO شما روی OD-30 باز می‌شود؛ موج ۶-۷ (router shadow/guards روی 191) مستقل و قابل ادامه. شاخه‌ی `exec-v3/integration` در germline (@0aef445a). هیچ run جدیدی ساخته نشد؛ ‏F:\backup فقط این پوشه‌ی جدید Obsidian را گرفت (GO-D؛ بدون git).
