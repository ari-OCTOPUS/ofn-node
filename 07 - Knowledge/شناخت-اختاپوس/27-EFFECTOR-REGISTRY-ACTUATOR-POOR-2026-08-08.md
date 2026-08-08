---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, architecture, effector-registry, sensor-rich, actuator-poor, neural-loop]
created: 2026-08-08
updated: 2026-08-08
created_by: agent
sources:
  - "effector_registry.py (commit this session) — 10 sensors mapped from live code"
  - "parallel agent verification of applied-field fix (wiring.py:1702-1738, 5 rows applied=true)"
---

# رجیستریِ Effector — نقشهٔ بیماریِ actuator-poor — ۲۰۲۶-۰۸-۰۸

> مالک خواست: Effector Registry بساز — هر حس → یک مسیرِ اکشن. این نوت نتیجه است:
> یک فایلِ اعلانی (`_ops/effector_registry.py`) که ۱۰ حس را به اکچوئیتورهایشان
> نگاشت می‌کند و **بیماریِ sensor-rich/actuator-poor را قابل‌دیدن می‌کند**. مکملِ
> [[26-AI-ARCHITECTURE-GAP-ANALYSIS-2026-08-08]] (اشتباهِ #۲).

## کشفِ اول — `applied` قبلاً فیکس شده بود

مگاپرامپت گفت `applied` در effect-shadow «همیشه False هاردکد است (`wiring.py:1730`)».
ولی وقتی **شخصاً کدِ زنده را خواندم**، دیدم:
- `wiring.py:1702-1738` یک `_learned_applied = bool(APPLY && pressure>0)` دارد (نه هاردکد).
- کامنتِ ۰۸-۰۷ توضیح می‌دهد چرا قبلاً همیشه False بود و کِی فیکس شد.
- `effect-shadow.jsonl`: ۵ ردیفِ آخر `applied=true` دارند (beat 28659+، امروز).

**نتیجه:** یک ایجنتِ موازی این فیکس را امروز انجام داده. این درسِ روشی مهم است:
**قبل از فیکس، کدِ زنده را بخوان** — مگاپرامپت از یک وضعیتِ قدیمی می‌آمد.

## Effector Map — وضعیتِ زنده (۱۰ حس)

| sensor | produced_by | actuator | status |
|---|---|---|---|
| `bcm.learned_pressure` | wiring.py → effect-shadow.jsonl | wiring.protective_override | ✅ wired |
| `c6.hypothesis_producer` | c6_producer → hypothesis-queue.jsonl | c6_trigger → RFC card | ✅ wired |
| `vault_bridge.rag_evidence` | vault_bridge.py | retrieval_router (context) | ✅ wired |
| `deep_dive.smallest_fix` | self_knowledge.py | **None** (فقط digest) | 🟡 display-only |
| `self_model.pathology` | self_model.py | **None** (فقط alert) | 🟡 display-only |
| `latent_space.vector` | latent_space.py | **None** | 🟡 display-only |
| `bcm.weights_bidirectional` | bcm.py → bcm-weights.json | **None** | 🔴 dead-output |
| `hebbian.associations` | hebbian.py → hebbian.json | **None** | 🔴 dead-output |
| `consolidation.insights` | consolidation.py → memory.db | **None** | 🔴 dead-output |
| `effect_shadow.would_throttle` | wiring.py:1698 | خودش observation است | 🟣 shadow |

**شمارش:** ۳ وصل، ۳ display-only، ۳ dead-output، ۱ shadow.

## سه مثالِ زنده (برای درکِ تفاوت)

**حلقهٔ بستهٔ خوب (C6):** فرضیه تولید → آزمایشِ sandbox → RFC card به مالک → رأی →
خودبهبودیِ کد. این یک effectorِ کامل است.

**بن‌بستِ مهم (smallest_fix):** دقیق‌ترین جملهٔ تصمیمِ سیستم روی ۱۸ سیکل محاسبه
می‌شود → در digest به مالک نمایش داده می‌شود → **هیچ ماژولی آن را به action تبدیل
نمی‌کند**. کامنتِ organ_dialogue.py:138 صراحتاً می‌گوید «هیچ ماژولی نمی‌خواندش».

**حلقهٔ بستهٔ ترمز (BCM):** فشارِ آموخته‌شده → protective_override → throttle/halt →
ثبتِ applied=true. این از امروز کار می‌کند.

## کارِ بعدی (پشتِ رأیِ مالک، نه این جلسه)

۱. **smallest_fix → action_bridge.propose** — مهم‌ترین. این دقیق‌ترین خروجیِ سیستم
   است و باید propose-only به action برسد.
۲. **consolidation dedup** — ۳ بینشِ تکراری در ۲۹۰+ سیکل.
۳. **bcm.weights / hebbian** — وزن‌ها تولید می‌شوند ولی تصمیمی نمی‌خواندشان.

## فایل
- `_ops/effector_registry.py` — رجیستریِ اعلانی + توابعِ کمکی (`dead_outputs`،
  `display_only`، `wired`، `status_counts`).
- `_ops/tests/test_effector_registry.py` — ۸ تستِ سازگاریِ ساختاری (همه سبز).

## commit
- این جلسه: `effector_registry.py` + تست.
