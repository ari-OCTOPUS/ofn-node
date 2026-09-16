---
type: session-note
date: 2026-08-13
status: verified
suites: talk_discovery 14/14 · route_scorer_wire 6/6 · collab_model_evidence 9/9 · api_collab 17/17 · conversation_hub 11/11 · chatbox · intents_100steps · awareness 6/6 · collab_and_live PASS
commits: e83d316 · 3ae20cc · 01d63b0
---

# 43 — اتصالِ کارهای ایجنت‌های موازی: مغز چت + فرمول‌بندیِ مدل + Hub

> مالک: «اینا کارای ایجنت موازیمه، همرو به هم وصل کن، کدنویسیارو کامل کن، ابسیدین رو براساسشون بروز کن، گزارش کامل بده که چک کنن بقیه.»

## چه چیزی وصل شد (سه لایه)

| لایه | کارِ ایجنت موازی | وضعیت قبل | کاری که اینجا شد |
|---|---|---|---|
| ۱. مسیرِ مرکزی | فیکس `collab_chat`→DeepSeek در `model_router.py` | ✅ درست بود ولی **commit نشده** (فقط working tree) | کامیت `e83d316` + تستِ pin جدید (scorer رأی local بدهد هم secondary می‌ماند) |
| ۲. فرمول‌بندیِ جواب | تبدیل ~۳۰ intent از template به تماسِ واقعیِ مدل («همه‌اش یکجا») | ⏳ کارِ باقی‌ماندهٔ گزارشِ ایجنت | کامیت `3ae20cc` — ۱۴ kindِ داده‌دار به مدل وصل شدند با شواهدِ واقعی؛ template تورِ ایمنی |
| ۳. Conversation Hub | آداپتورهای Phase 2 | 🔲 stub (Phase 1) | کامیت `01d63b0` — ask/runtime/memory/guide به ماژول‌های واقعی؛ mcp/epistemic/propose stubِ صادق |

## ۱ — فیکس مسیر مرکزی (کامیت e83d316)

**باگ (از گزارش ایجنت موازی):** `CORTEX_ROUTE_SCORER=1` باعث می‌شد `route_scorer` برای
`collab_chat` رأی `local` بدهد — ولی `collab_chat` عمداً qwen محلی را ممنوع کرده
(`_skip_local`) → چت `deepseek-unavailable` می‌گرفت در حالی که DeepSeek سالم بود.

**فیکس:** پینِ مالک-محور `collab_chat → secondary` **قبل از** مشورتِ route_scorer
اجرا می‌شود — نگاشتِ صریحِ مالک بر heuristic عمومی می‌چربد.

**تستِ نو** (`test_route_scorer_wire.py::test_collab_chat_pinned_to_secondary_ignores_scorer_local_vote`):
پرچم روشن + scorer رأی local → همچنان secondary، scorer **اصلاً** مشورت نمی‌شود؛
یک task عادی (classify) هنوز scorer را می‌بیند (pin فقط collab_chat است). **۶/۶ سبز.**

## ۲ — فرمول‌بندیِ مدل با شواهد واقعی (کامیت 3ae20cc)

**طراحی (مطابق گزارش ایجنت):** جمع‌آوریِ داده **در `conversation.py` می‌ماند** (همان
کدِ صادقِ فایل‌خوان — beat، سنِ فایل، فلگ‌های STOP، وضعیت هر عضو)؛ فقط «فرمول‌بندیِ
جواب» به مدل می‌رود — متنِ template (شاملِ همان دادهٔ واقعی) به‌عنوان **شواهد** به
DeepSeek داده می‌شود و مدل خودش جمله می‌سازد. template تورِ ایمنیِ شکستِ مدل.

**تغییرات:**
- `collaborator.py`: `_EVIDENCE_KINDS` (۱۴ kind: goal/runtime/protective-status/
  blockers/discovery/equation/architecture/business/effect/capabilities/capability/
  memory/limitations/selfmap) به `_LLM_KINDS` اضافه شد. هر کدام متنِ template را
  به‌عنوان شواهد می‌فرستند؛ `data.evidence_kind` برای ممیزی.
- `collab_model_adapter.py`: پارامتر `evidence` — داخل prompt با دستورِ «فقط از
  همین شواهد فرمول‌بندی کن؛ عدد/وضعیت/مسیر را تغییر نده»؛ سقف ۱۵۰۰ کاراکتر.
- **استثناهای عمدی (قطعی می‌مانند — تست‌ها pin کرده‌اند):** `discover` (متنِ
  journal/pulse نباید جایگزین شود)، `intro` (فیکس timeout ۶۰ث)، `honest-self`
  (invariant صداقت AGI — INT-04)، و رشته‌های ردِ امنیتی (blocked/owner-gate/...).

**تست‌ها** (`test_collab_model_evidence.py` ۹/۹): شواهد در prompt هست، discover/
intro/honest-self/deny قطعی‌اند، شکستِ مدل → template، clarify/chat بدون تغییر،
مسیر کامل handle()، سقف ۱۵۰۰.

**رگرسیون:** talk_discovery 14/14 · api_collab 17/17 · chatbox · intents_100steps
· awareness 6/6 · conversation_hub 11/11 · collab_and_live PASS.

## ۳ — Conversation Hub به مسیر واقعی وصل شد (کامیت 01d63b0)

`_ops/conversation_hub/service.py` — آداپتورهای Phase 2-lite (همه fail-soft):

| Route | آداپتور واقعی | رفتارِ شکست |
|---|---|---|
| ask/vault/brain/collab | `collaborator.handle` (مسیرِ DeepSeekِ فیکس‌شده) | fallback قطعی + limitation صادق |
| runtime | `status.runtime_truth()` (فقط‌خواندنی) | fallback + limitation |
| memory | `owner_recall` (cite-only، خالیِ صادق) | fallback + limitation |
| guide | `owner_guidance.effective()` (فولدِ فقط‌خواندنی) | fallback + limitation |
| mcp / epistemic / propose | stubِ صادق — «not wired» صریح در limitation | — |

**مرزهای سخت دست‌نخورده:** `external_effect=False` همیشه · `may_authorize=False`
· فلگ `OCTOPUS_UNIFIED_CHAT=0` (پیش‌فرض خاموش — صفر اثر روی رفتارِ زنده).

**تست‌های Hub** بروزرسانی شدند (۱۱/۱۱): دیگر `[stub:*]` برای مسیرهای واقعی
نمی‌بینیم؛ smoke زنده: ask → intro با beat=33632 واقعی، runtime → حقیقتِ زنده.

## وضعیتِ فازهای باقی‌مانده (ADR-040)

- **Phase 2-lite** ✅ (این جلسه) — آداپتورهای observe برای ۴ مسیر
- **Phase 2 کامل**: MCP broker (۳ ابزارِ read) + epistemic projection → باز
- **Phase 3**: `POST /api/octopus/chat` در gateway + ثبت فلگ → باز
- **Phase 4–6**: projection، UI واحد، shadow rollout → باز

## چیزهایی که عمداً انجام نشد

- بازنویسیِ `conversation.py` (جمع‌آوریِ داده همان‌جا ماند — improve don't rewrite)
- `execute` از چت — همیشه ممنوع (ADR-040 §hard)
- Cortex invocation از chat — فقط read-model
- باز کردنِ فلگ‌های جدید روی زنده — همه default OFF
- معماِ ۷۱۳M توکن: ممیزیِ ایجنت موازی هر ۵ سرنخ (Studio/learning-engine/4d/
  doctor/fugu_proxy) را رد کرد — از بیرونِ کدبیس می‌آید؛ اینجا دنبال نشد

## شواهد برای راستی‌آزمایی

```
git show e83d316 --stat     # fix + تست pin
git show 3ae20cc --stat     # template→model
git show 01d63b0 --stat     # Hub Phase 2-lite
python -X utf8 tests/test_route_scorer_wire.py
python -X utf8 tests/test_collab_model_evidence.py
python -X utf8 tests/test_conversation_hub.py
```
