---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, tests, backlog]
created: 2026-08-06
updated: 2026-08-06
created_by: agent
sources:
  - "run_all.py full sweep (597 files) + 7-agent triage workflow, 2026-08-06"
---

# بدهیِ تست‌های کهنه — ۲۵ ردیف — ۲۰۲۶-۰۸-۰۶

اجرای کاملِ `_ops/tests/run_all.py` (۵۹۷ فایل) ۲۷ شکست داد. یک workflowِ
۷-ایجنته هرکدام را جدا اجرا/خواند/تاریخ‌گذاری کرد. نتیجه: **فقط ۱ مورد**
ساختهٔ همین جلسه بود (رفع شد — به `find_broken_links.py` بستهٔ `4D-Vault`
اضافه شد). ۲۵ موردِ باقی **بدهیِ کهنه‌اند**: کد عوض شد، تست هرگز آپدیت
نشد. هیچ‌کدام امروز فیکس نشدند — نیازِ قضاوتِ مالک یا وقتِ اختصاصی دارند.

## ⚠️ اولویتِ بالا — احتمالِ نشتِ واقعی

**`test_miniapp_lifecycle_view.py`** — تستش می‌گفت «بدنهٔ HTTP هرگز نباید
متنِ کارت/rfc_id داشته باشد» و حالا دارد (فیچرِ کارتِ راکد، کامیت `3bfebcd`،
۰۸-۰۵). ممکن است تست کهنه باشد (فیلد جدید مجاز است) **یا** یک نشتِ واقعی
باشد که طراحیِ اصلی می‌خواست جلویش را بگیرد. **قبل از فیکس، تصمیمِ مالک لازم
است.**

## بقیه (کدام کهنه‌تر است، نه اولویت)

| فایل | علت | تاریخِ رانده‌شدن |
|---|---|---|
| `test_budget_gate_v2.py` | پنجرهٔ سقفِ هزینهٔ owner-approved (۲۰۰$ تا ۰۸-۱۳) هاردکد را می‌شکند | ۰۷-۳۰ |
| `test_phase_gate.py` | زنجیره‌ای از بالا (held_out_evaluator زیرپروسهٔ test_budget_gate_v2 را دوباره اجرا می‌کند) | همان |
| `test_project_f.py` | `_ARCHIVE_PATH` → `_archive_path()` تغییر کرد، تست نه | ۰۸-۰۳/۰۵ |
| `test_llm_call_inventory.py` | `cockpit_brain.py` تماسِ جدیدِ inventory-نشده + false-positive روی docstring در `governor.py` | ۰۸-۰۳/۰۵ |
| `test_mining_wiring.py` | Mining با قراردادِ `_BUSINESS_LEGS_SPEC` ساخته شد نه factory-function؛ رندر هم `electricity_mood` را نمی‌بیند | باز (AGENT_QUESTIONS ۰۸-۰۱) |
| `test_selfaware_wiring.py` | `SchoolBridge()` بدونِ override به state زنده می‌نویسد؛ گاردِ live-state (۰۸-۰۳) می‌گیردش | ۰۸-۰۳ |
| `test_command_discoverability.py` | `/sh`، `/شل` به منو اضافه نشدند (عمدی، درِ owner-only) | ۰۸-۰۴ |
| `test_orphan_scan.py` | `arm_gate` دیگر یتیم نیست (سیم‌کشیِ DR-001) | ۰۸-۰۴ |
| `test_activation_flag_presence.py` | دو فایلِ `.flag` (RAW-SHELL، PULSE-ARBITER) با رجیستری هماهنگ نیستند | ۰۸-۰۴/۰۵ |
| `test_phantom_guards.py` | لیستِ سخت‌کدِ flag ratchet چند روز عقب است (شاملِ یک ورودیِ خودِ امروز که مثبت است) | تجمعی |
| `test_route_scorer_wire.py` | mock ِ `_ask_paid` آرگومانِ `task=` جدید را نمی‌گیرد | ۰۸-۰۴ |
| `test_governor_routing.py` | همان علتِ بالا | ۰۸-۰۴ |
| `test_leg_chain_wire.py` | مجموعهٔ ۵ پا هاردکد؛ الان ۷ پا (`sync_agent`+`studio_pf`) | ۰۸-۰۲/۰۳ |
| `test_leg_registry_parity.py` | `sync_agent` در منوی تلگرام/weekly-review نامرئی | ۰۸-۰۲ |
| `test_render_legs.py` | کارتِ عددیِ ماینینگ به‌جای متنِ skeleton می‌نشیند (D-013) | ۰۸-۰۱ |
| `test_c6_trigger_propose_only.py` | خطِ گاردِ pin‌شده در `doctor.py` بازنویسی شد (شاید هنوز معادل باشد) | ۰۸-۰۳ |
| `test_audit_origin_guard.py` | `DEFAULT_AUDIT_FILE` → `_default_audit_file()`؛ monkeypatch بی‌اثر شد؛ **فایلِ تولیدیِ Project-F واقعاً آلوده می‌شود** | ۰۸-۰۳/۰۵ |
| `test_hebbian_eventclock.py` | `DECAY_RATE`/`PRUNE_THRESHOLD` تیون شدند، مقادیرِ تست نه | ۰۸-۰۴ |
| `test_tg_leg_commands.py` | صف‌بندیِ async (brain lane)، تست منتظر نمی‌ماند | ۰۸-۰۳/۰۴ |
| `test_tg_voice_worker.py` | `center._VOICE_Q` حذف شد (`_BG_LANES` جایگزین شد) | ۰۸-۰۳ |
| `test_tg_wiring_w2.py` | رسیدِ بوت دو خط شد (شمارندهٔ ری‌استارت)، تست یک‌خطی می‌خواهد | ۰۸-۰۴ |
| `test_tg_wiring_w3.py` | همان علتِ `_VOICE_Q` بالا | ۰۸-۰۳ |
| `test_tg_group_allowlist_policy.py` | `mo:1` عمداً مجاز شد، تست هنوز ردش می‌کند | ۰۸-۰۱ |
| `test_miniapp_cockpit_ui.py` | anchor-هایِ سورس (HEADER_LITERAL و…) با ریدیزاینِ UI عوض شدند | ۰۸-۰۳→۰۸-۰۵ |
| `test_cartographer_wiring.py` | فلیکیِ محیطی — یک HALT/restart واقعیِ ارگانیسم دقیقاً وسطِ رانِ تست افتاد | — |

جزئیاتِ کاملِ هر ردیف (شواهد، file:line، fix پیشنهادی) در ترنسکریپتِ
workflow ِ همین جلسه است، نه اینجا — این جدول فقط برای اولویت‌بندیِ سریع.
