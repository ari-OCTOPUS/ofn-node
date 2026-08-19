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

_افزودهٔ 2026-08-19T02:2xZ پس از ممیزی کامل: [[../06-EVIDENCE/AUDIT-191-20260819/OCTOPUS-FULL-AUDIT|AUDIT-191]] — ردیف‌های بالایی دست‌نخورده ماندند._
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

_دیباگ‌سوئیپ 2026-08-19T07:0xZ (هرچی مونده بود):_
| مورد | وضعیت |
|---|---|
| F18 (انقضای FX در مسیر عمومی) | ✅ بسته — گیت fx_pinned_fresh در _ask_paid؛ ۲۴/۲۴ تست؛ فعال‌سازی کامل پس از restart پروسه‌ها |
| F15 (رسیدِ fallback محلی) | ✅ بسته — رسید FREE_OR_UNBILLED با fallback_of (mrfb-*)؛ اثبات runtime پس از اولین fallback موفق |
| E14 (گیت E2E در Core) | ✅ بسته — test_e2e_gate.py ‏۵/۵ |
| B9 (REFERENCE_DIR) | ✅ بسته — .env→`4D` + دایرکتوری مرجع ساخته شد؛ مؤثر پس از restart دیمن |
| A4 (label-history بدون زنجیره) | ✅ بسته از امروز — label_history.py با هش‌زنجیره (لنگر تأییدشده؛ ردیف‌های قدیمی legacy) |
| زامبی :8765 | ✅ خودحل — listener دیگر وجود ندارد |
| V4a (سقف توکن داور ۵۱۲) | ✅ پیاده + بکاپ؛ ⏸ پروب/فریز منتظر نرخ تازهٔ RBA |
| HTTP-8765/TASKS-PATH/MATH-TCB/DAEMON-PRED/WIRING-ORPHANS | مالک‌محور — بدون تغییر |

_اجرای OWNER-QUEUE-RESOLUTION + هماهنگی 06:42Z (2026-08-19 ~07:1xZ):_
| مورد | وضعیت |
|---|---|
| حلقهٔ یادگیری دیمن (Q3) | ✅ **LIVE_VERIFIED** — دیمن واقعی: ۲۰ prediction/۱۴ outcome؛ لیبل DAEMON_PREDICTION_LOOP |
| باگ پیام novelty (Q3b) | ✅ فیکس — ریشه: پیام دروغگو (گیت عمدی بود)؛ self_evolve با مراسم TCB |
| لنگرهای ریاضی (Q1) | ✅ Var_ex + I_pred در self-test؛ **C-035**: ناهمخوانی Var_eff باز |
| سه‌گانهٔ router (Q2) | ✅ llm/router.py بنر RETIRED (مراسم ×۲، امضا معتبر)؛ survival-gateway یافت نشد |
| Councils (Q4) / supervisor (Q5) | ✅ CLOSED / RETIRED — بدون schtask |
| تسک‌های ویندوزی (Q7) | ✅ از قبل سبز بود (کاتالوگ کهنه) |
| زنجیرهٔ FX→V4a→فریز→primary | 🔒 **PIPELINE-OWNERSHIP.lock** (مالک 06:42Z) — مالکش سشن دارای آخرین وضعیت؛ LOOP-01 کنار کشید |
| c7 در تست رگرسیون | ⏳ رفع هماهنگ دوسشن‌ای — BLOCKERS جزیره |
| نسل دوم candidateها | 📋 پیش‌شرط جدید: اعتبارسنجی روی کد واقعی (یافتهٔ سشن ۲) |

| جنگ ۲۴ساعته (فروش زخم) | 🔁 **لغو توسط مالک 09:30Z** — حالت خصوصی؛ سطل تجارت منجمد | CANCELLED |  |
| مأموریت جدید: کشف معماری تحول | 🎯 Island نسل دوم با پیش‌شرط کد واقعی + شکاف صادق «تحول=صفر» | ACTIVE | همان سند |

_صبح 2026-08-20 — صف مالک (از ممیزی مستقل + شب):_
| مورد | وضعیت |
|---|---|
| ratify TCB #3 (C-035 anchor patch) | ⏳ PATCHED-UNSIGNED — patch/tests در درخت؛ امضای ایجنت کافی نیست |
| ratify فریز V4 (decision_id خالی شد) | ⏳ مبانی امضاشده نشان داده شد؛ خودِ ratify با شما |
| چرخش واقعی سه کلید (D3) | ⏳ OPEN تا ابطال واقعی |
| پذیرش answer-first در پروتکل منجمد (بازو/داور) | 🆕 A4 — پس از ratifyها؛ پروب PASS است |

| answer-first wrap (پروتکل-هم‌مرز) | CLAIMED — بازو 8/8 و داور 7/8 در دور اول، 3/8 در دور دوم (غیرقطعی)؛ fallback تک‌توکنی VERIFIED؛ iteration سوم ممنوع؛ V5 freeze نه | CLAIMED |  |
| improve→digest | READY-FOR-OWNER-VOTE — کد بسته، فقط رأی زندهٔ مالک لازم | READY |  |

_موج 0/A — research-sprint (2026-08-20):_
| مورد | وضعیت |
|---|---|
| R01 (حقیقت عملیاتی) | ✅ اسلات ۱ آماده؛ اسلات ۲ PENDING-OWNER-PASTE · GAP-001 کاندید: چرخهٔ بستهٔ ایده‌ها |
| ساختار R01–R10 | ✅ ساخته شد (`octopus-research-sprint/`) |
| CARD-001 | ⏳ ممنوع تا R10 + تأیید مالک (طبق پروتکل) |

| P10 root-cause (daily_cap) | باگ سیم‌کشی B2 تأیید شد: cardiac-budget.json بدون daily_cap → daily_pool→0.0؛ اصلاح در FASE 6 | OPEN | life_currency.py:170 |
| swap_consistency.py | FOUND_AT (island, 68279b4) — اختلاف panel-only حل شد | VERIFIED | ls+hash |
| LAW-23 | تثبیت شد: ادعای «ساخته شد» = مسیر+هش+git ls-files | ACTIVE | DEAD-CLAIMS-REGISTRY |
