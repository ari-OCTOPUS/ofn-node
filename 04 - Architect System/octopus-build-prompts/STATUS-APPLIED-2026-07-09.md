---
type: status
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
created_by: agent
verified_by: "Claude (architect) — disk audit 2026-07-09"
tags: [octopus, status, applied, audit, handoff]
created: 2026-07-09
updated: 2026-07-09
---

# STATUS — چه چیزی واقعاً اعمال شده (اودیتِ دیسک 2026-07-09)

> اودیتِ مستقلِ معمار روی دیسک + git + OVERNIGHT-LOG. «اعمال‌شده» = فایل روی دیسک و در git.

## ✅ اعمال‌شده و committed
**اسناد/گزارش (۱۰):** OCTOPUS-BASE-MAP-v0 · HYBRID-DESIGN-v1 · GLM-MAPPER-PROMPTSET · GO-LIVE-PACK · OVERNIGHT-QUEUE · DOCTOR-BOX-OF-AGENTS-SPEC · DOCTOR-EVOLUTION-BENCHMARK-10systems · CHRONO-RHYTHM-LAYER-SPEC · fusion-doctor-spectral-sense · SCHOOL-MEMORY-SPEC.

**کد (تست‌سبز طبق OVERNIGHT-LOG، ~۲۲ فایلِ تست):**
| فاز | ماژول |
|---|---|
| P1 قلب | `_ops/chrono.py` · `organism.py` |
| P3 تلگرام | `_ops/budget/approval_channel.py` |
| P4 پاها | `_ops/legs/leg.py` · `lead_leg.py` |
| P2 دکتر | `_ops/doctor/doctor.py` |
| P5 بقا | `_ops/watchdog.py` · `germline.py` · `unified_bus.py` · `checkpoint.py` · `smoke_24h.py` |
| Wiring | `_ops/wiring.py` |
| Evolution (10-systems) | `_ops/doctor/evolution.py` (RFCArchive + measured_lift + tournament) |
| Spectral | `_ops/doctor/spectral.py` · `fusion_sim.py` |
| Box B0/B1/B3/B4 | `_ops/doctor/box/` (۱۴ ماژول: warden, topology, sensors, dynamics, agent_state, archivist, primitive, null_dreamer, falsif_harness, b3_bridge, b4_fusion, box) |

**git:** `Octopus P1-P5…` + `overnight checkpoint: wiring + chamber + spectral + box B0 + evolution`. بدهیِ commit بسته شد.

## ⛔ هنوز ساخته نشده (اسپک آماده، کد نه)
| زیرسیستم | اسپک | پرامپتِ آماده |
|---|---|---|
| **Chrono-Rhythm layer** | `CHRONO-RHYTHM-LAYER-SPEC.md` | ✅ §۸ (CR-B0) |
| **School Memory** | `SCHOOL-MEMORY-SPEC.md` | roadmap §۱۰ (SM-B0؛ پرامپتِ کامل لازم) |
| **CP-1 Sensory Bus** (afferent) | Research-cycle round1 (چت) | ❌ پرامپت لازم |
| Box B2 (صداهای LLM) | box spec Part 8·B2 | نیازِ کلیدِ gateway (دستِ مالک) |

## 🔒 فقط‌مالک — go-live (کد نمی‌تواند)
1. باتِ تلگرام: `TELEGRAM_BOT_TOKEN` + `TELEGRAM_OWNER_CHAT_ID` در `.env`.
2. Scheduled Task: watchdog ۵دقیقه + germline ساعتی.
3. off-site backup credential.
4. اجرای ۲۴h smoke → اولین لیدِ paperِ Lead-نقاشی.
5. کلیدِ gateway برای Box B2 (اگر خواستی صداهای LLM).
6. P6 پول — قفل تا ۲۰۲۶-۰۷-۲۱ + پرچمِ تو.

## صفِ عملیاتیِ باقی‌مانده (queue-2، وقتی خواستی)
1. CR-B0 (پرامپت در chrono spec §۸) → به GLM.
2. SM-B0 + CP-1 → پرامپت لازم (معمار می‌سازد).
3. Box B2 → بعد از دادنِ کلیدِ gateway.
4. go-live فقط‌مالک (بالا).

> «کاملاً operational/live» گیت‌خورده به: (الف) ۳ ساختِ باقی‌مانده، (ب) اقدام‌های فقط‌مالک، (ج) تاریخِ money-lock. کد از سمتِ معمار (سندباکس) نه اجرا/commit می‌شود نه go-live — طبقِ قاعدهٔ Windows-side.
