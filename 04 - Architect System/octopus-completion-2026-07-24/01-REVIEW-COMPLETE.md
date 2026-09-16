# 🧭 OCTOPUS — بررسیِ کاملِ ۲۵ برنچ + نقشهٔ تکمیلِ موازی — 2026-07-24

> راست‌آزمایی‌شده با تحلیلِ فایل‌به‌فایلِ کدِ هر برنچ نسبت به `master` (نه فقط پیامِ commit).
> **حفظِ کامل:** ۲۰ `refs/rescue/*` + ۲ `rescue-base` tag + پچ‌ها. برنچ‌های حذفی هم قبلِ حذف `archive/*` tag می‌خورن → صفر گم‌شدن.

---

## A) نگه‌دار + مگا-پرامپت — ۹ workstreamِ ارزشمند (کدِ واقعی، تازه، در `_ops`)

| # | workstream | برنچ(ها) | چیست (فایل‌های کلیدی) | ریسکِ merge |
|---|---|---|---|---|
| WS-1 | **C6 خودبهبودی** | c6-self-improvement-ignition + octopus-reproduction-c6 | `_ops/c6_trigger.py` (نو) + هوکِ `organism.py` (flag-gated، propose-only) + پچِ accepted‌شدهٔ memory-index (`_sandbox/evolution_v3/proposed_v3_final.patch`) | متوسط (پشتِ فلگ) |
| WS-2 | **فیکسِ باگ‌های قلب** | heart-vessels-debug | ۵ باگ در `cardiac.py`, `heart/control_law.py`, `doctor_setpoint.py`, `heartstate.py`, `work_pump.py`, `wiring.py` + ۵ تست | پایین (فیکسِ واقعی) |
| WS-3 | **یکسان‌سازیِ model_router** | octopus-fugu-everywhere (+ `model_router.py` از fail-closed) | انتقالِ call-siteهای LLMِ `budget/governor_epoch.py` + `heart/doctor_setpoint.py` به `cortex/model_router.py` (flag-gated) | پایین (additive) |
| WS-4 | **رصدِ tick-timing** | octopus-tick-decoupling | `_ops/tick_timing.py` (نو) + probe در `organism.py` (صفر تغییرِ رفتار) | خیلی پایین |
| WS-5 | **پایپ‌لاینِ lead-gen** | phase-d | D3–D7: `legs/harvest_austender.py`, `email_inbound.py`, `funnel_store`, `speed_to_lead.py`, `lead_effect_gate.py`, `outbound_worker.py` — ۹۴ تست، flag-off | متوسط (پول/ارسال پشتِ فلگ) |
| WS-6 | **پکِ امنیتی M1–M7** | fail-closed-human-guard | `now_moves/`: ledger_integrity_probe, staleness_stamp, cortex_symmetric_revive, unified_bus_guard, kill_seam_closer, module_self_manifest, route_scorer_shadow_log (همه additive/flag-off) | پایین (flag-off) |
| WS-7 | **Project-F / Saba** (کانونی) | project-f-agent-build | زیرپروژهٔ کاملِ Saba: Fable5 ۴-DB + RAGِ محلی + KPI/attribution + productionِ CI — ۴۵۹ تست، ۵۳ فایلِ نو | زیرپروژهٔ جدا |
| WS-8 | **Ziman / بات‌مامان** (کانونی) | ziman-gif-deep-scan | `legs/ziman_leg.py` + `mom-bot/` (bot/flow/questions/staging + ۲۳ تست) + برندینگِ خودکار | زیرپروژهٔ جدا |
| WS-9 | **Painting-OS** (کسب‌وکارِ خودت) | telegram-governance-integration | موتورِ کوت + اینویس + ایمیل + intake (۴ ستون) — ۱۲ commit | مرورِ ویژه (کسب‌وکارِ اصلی) |

## B) مرزی — کدِ واقعی دارن، راست‌آزمایی و بعد نگه/ادغام — ۴

| برنچ | کدِ یکتا | تصمیم |
|---|---|---|
| `cranky-chandrasekhar` | anti-replayِ پول (approvalِ تک‌مصرف، consume اتمیک، TTL، action-id سوخته) + channel layer | 🔶 امنیتِ پول — verify vs master؛ اگر تازه → WS جدا |
| `three-heart-rhythm-math` | `heart/pulse_arbiter.py` + `drawdown_guard` + `indicator_scorecard` | 🔶 verify vs master؛ اگر تازه → به WS-2 (قلب) بچسبون |
| `obsidian-vault-org-swarm` | control-plane: `octopus_logger.py`, `cortex/improve.py`, `self_model.py`, panic, FLAG-REGISTRY + ۱۸ blind-spot | 🔶 زیرساختِ سنگین — verify؛ شاید WS جدا |
| `wave1/a-telegram` | Menu v2 + `outcomes/verdict_recorder.py` (durable OutcomeStore) | 🔶 verify vs `telegram_center` فعلی |

## C) منسوخ → `archive/*` tag + حذف — ۱۲ (کاهشِ حجم)

| برنچ | چرا منسوخ |
|---|---|
| `optimistic-maxwell` | مرحلهٔ قدیمیِ Project-F → در `project-f-agent-build` |
| `project-analysis-planning` | Project-F planning → در `project-f-agent-build` (فقط MASTER-SCHEDULE/BACKLOG-50 را به‌عنوان داک نگه می‌داریم) |
| `saba-vaultbank-tests` | Saba co-pilotِ قدیمی → در `project-f-agent-build` |
| `higgsfield-integration-setup` | mom-bot Phase 0 → در `ziman-gif-deep-scan` |
| `ollama-fugu-brain` | email/AusTender → در `phase-d` (نسخهٔ تازه‌تر) |
| `architecture-docs-5d67ea` | عمدتاً merge-noise + lead-cockpitِ منسوخ |
| `octopus-architecture-refactor` | `legs_registry.py` (۱ commit؛ اگر بخوای به WS-infra) |
| `octopus-qa-red-team-findings` | ۶ فیکسِ کوچک (verify در master) |
| `kind-kirch` | فقط فیکسِ test-isolation (منسوخ) |
| `session-f92f3d` | فقط داکِ نیت (fusion-lab/WLOS) — نیت را در یک نوت نگه، بعد حذف |
| `three-heart-rhythm-math`؟ | اگر در master باشد → اینجا |
| `wave1/a-telegram`؟ | اگر در `telegram_center` باشد → اینجا |

---

## نقشهٔ اجرای موازیِ ایجنت‌های بعدی (پیش‌نویس)

**موجِ ۱ (مستقل، موازی، کم‌ریسک):** WS-4 (tick-timing) · WS-3 (model_router) · WS-2 (heart bugs) · WS-6 (security pack)
**موجِ ۲ (متوسط، بعد از موجِ ۱):** WS-1 (C6) · WS-5 (lead-gen)
**زیرپروژه‌های مستقل (هر زمان، جدا):** WS-7 (Project-F) · WS-8 (Ziman) · WS-9 (Painting-OS)

هر WS یک **مگا-پرامپتِ standalone** می‌گیره: context + refِ منبع (`refs/rescue/*` یا برنچ) + چه verify + چه merge + پروتکلِ ایمن + تست‌ها.

## گامِ بعدی (تصمیمِ تو)
- ۴ مرزیِ بخشِ B: راست‌آزمایی کنم (diff vs master روی ویندوز، چون diff رو mount timeout می‌ده) و بعد نگه/حذف؟
- بعدش مگا-پرامپت‌ها رو دونه‌دونه می‌سازم (از موجِ ۱ شروع)، بعد پلنِ نهایی، بعد حذفِ بخشِ C، بعد مرتب‌سازیِ Obsidian.
