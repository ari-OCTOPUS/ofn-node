# OPEN GATES (generated 2026-08-19T01:04:06+00:00)
| gate | value | status | evidence |
|---|---|---|---|
| F3_METADATA_ENTRY | OPEN | CLAIMED | `06-EVIDENCE/CL01-191-20260818-2233/live4/METADATA-CONFIDENCE-AUDIT.md` |
| D3_GIT_HISTORY_RISK | OPEN | CLAIMED | `02-DECISIONS/D3-PHASE2-UNTRACK-2026-08-19.md` |
| FX_PIN | STALE_OR_EXPIRING | expires 2026-08-19T06:00:00+00:00 | `06-EVIDENCE/CL01-191-20260818-2233/live4/FX-RECORD.json` |
| LIVE4 D-A/D-B | بازوی baseline + پرامپت داوری | OPEN | `06-EVIDENCE/CL01-191-20260818-2233/live4/LIVE-4-INTERIM-STATUS.md` |
| LIVE4_SCORING | BLOCKED_JUDGE_UNREADABLE_1_OF_4 (شش اجرای E2E، بهترین ۳/۴) | BLOCKED | `06-EVIDENCE/CL01-191-20260819/OCTOPUS-OPEN-BLOCKERS.md` |
| LIVE4_PROTOCOL_VERSION | PENDING_V2_FREEZE — پیش از نمونهٔ primary باید با هش فریز شود | OBSERVED | `_ops/state/labels.json` |
| CONTRADICTION_RADAR | ادعای ACTIVE ولی در زنده وصل نیست (label باید CLAIMED شود تا سیم‌کشی) | CLAIMED | `06-EVIDENCE/AUDIT-191-20260819/OCTOPUS-FULL-AUDIT.md` §C4 |
| RECEIPT_BUDGET_BUG | هر ۸۲ رسید budget_after منفی (model_router.py:319) | OPEN | `06-EVIDENCE/AUDIT-191-20260819/OCTOPUS-DEFECT-REGISTER.md` RCPT-1 |

_افزودهٔ 2026-08-19T02:2xZ پس از ممیزی کامل: [[../../06-EVIDENCE/AUDIT-191-20260819/OCTOPUS-FULL-AUDIT|AUDIT-191]] — ردیف‌های بالایی دست‌نخورده ماندند._
| ~~LIVE4 D-A/D-B~~ | D-A: FIXED_VERIFIED · D-B: V3 4/4 E2E PASS (02:38Z) — گیتِ اولیه سبز شد | RESOLVED | `06-EVIDENCE/CL01-191-20260818-2233/live4/DEEPSEEK-ROUTING-CONTRACT.md` |
| LIVE4_SCORING | صرفاً منتظر دو کارِ مالک: فریز V2 (ODN-2) + پین FX قبل از 06:00Z (ODN-1) | BLOCKED | `02-DECISIONS/DEEPSEEK-AUTOMATIC-ROUTING-01-2026-08-19.md` |

_به‌روزرسانی 2026-08-19T02:39Z پس از اجرای DEEPSEEK-AUTOMATIC-ROUTING-01 (گیت E2E ۴/۴ پاس؛ ۱۹/۱۹ تست V3؛ بهداشت کلید PASS)._
| ~~RECEIPT_BUDGET_BUG~~ | FIXED_VERIFIED — مبنای بودجه = باقی‌ماندهٔ روز؛ اولین رسیدهای غیرمنفیِ تاریخ repo (probe زندهٔ 13:30 local) | RESOLVED | `06-EVIDENCE/RCPT-FIX-20260819/PROMOTION-NOTES.md` |

_به‌روزرسانی 2026-08-19T03:32Z: RCPT-1/RCPT-2 (15/15 تست + probe واقعی) و G10/G11 (رسید مستقل ریست/توقف رزرو) طبق یادآوری حاکمیتی مالک بسته شدند — پیش از باز شدن پنجرهٔ primary._
| LIVE4_PRIMARY_V2 | اجرا شد زیر پروتکل منجمد؛ معیار برآورده نشد (22/30 معتبر، 13/20 برد؛ هر ۸ void = قضاوتِ ناخوانا) — نرخ برد 59% در n=22، نتیجهٔ منفیِ معتبر | OBSERVED | `06-EVIDENCE/CL01-191-20260818-2233/live4/PRIMARY-V2-REPORT.md` |
| D_B_READABILITY_AT_SCALE | خوانایی داور در حجم batch ‏73% (E2E چهارتایی پنهانش می‌کرد) — سه گزینهٔ مالک در گزارش | OPEN | همان گزارش §Next options |
| ~~CONTRADICTION_RADAR~~ | ACTIVE_VERIFIED_WIRED — رادار روی MemoryGate تولیدی؛ تناقض ⇒ QUARANTINED (10/10 تست + مهاجرت زنده) | RESOLVED | `06-EVIDENCE/TEAM-A-PROMOTION-20260819/` |
| ~~F3_METADATA_ENTRY~~ | FIXED_VERIFIED — insert بدون confidence هرگز وارد نمی‌شود (fail-closed) | RESOLVED | همان |
| D-B/V4 | مالک: فقط V4a (سقف توکن ۵۱۲)؛ void سختِ فعلی پیش‌ثبت؛ پروب ۸تایی فردا → فریز V4 | SCHEDULED | `02-DECISIONS/OWNER-CONSENTS-2026-08-19T0615Z.md` |
| FX_PIN_STANDING | مجوز دائمی fetch/pin روزانهٔ RBA با قاعدهٔ سخت (بدون جعل + رسید) — شروع از فردا ~06:10Z | AUTHORIZED | همان سند §3 |

_به‌روزرسانی 2026-08-19T06:3xZ: ارتقای TEAM-A طبق رضایت §4 همین حالا اجرا شد._
