# ⚠️ DEPRECATED — این دایرکتوری به ارگانیسمِ زنده وصل نیست

> Verdict 2026-07-18 integration-debug

## وضعیت

`4d_system/` یک **مغزِ پژوهشیِ مستقل (standalone research experiment)** است.
طبق `4d_system/MANIFEST.yaml:14`: *"STANDALONE RESEARCH BRAIN — independent experiment,
not wired to Octopus projects"*.

## معنای این برای توسعه‌دهنده

- تغییر در این دایرکتوری **تأثیری در ارگانیسم زنده ندارد** (port 8771/8772).
- کد آن کامل است (autoloop، daemon، fugu_client، telegram_bot) ولی لانچ نمی‌شود.
- هیچ import از `_ops/` به `4d_system/` وجود ندارد و برعکس.

## Canonical جایگزین

- مغزِ controller: `_ops/cortex/cortex.py` (port 8772)
- مغزِ دوم کسب‌وکار: `_ops/cortex/business_brain.py`
- LLM routing: `_ops/cortex/model_router.py`
- تلگرام: `_ops/budget/approval_channel.py` و `_ops/telegram_center/center.py`
- وضعیت Hearts/Brains/Memory (2026-08-11): `07 - Knowledge/Architecture/OCTOPUS-HEARTS-BRAINS-4D-STATUS.md`

## اگر خواستی revive کنی

باید تصمیمِ صریحِ owner بگیرد (verdict) چون:
1. تداخلِ token تلگرام با bot #1 (هر دو `TELEGRAM_BOT_TOKEN`) → خطرِ 409.
2. تداخلِ budget با budgets.yaml (کل ارگانیسم AU$30/ماه).
3. منبعِ حقیقتِ LLM باید unified شود.

## نگهداری

این دایرکتوری به‌عنوان **آرشیوِ پژوهشی** نگه‌داری می‌شود. حذف نشود.
مرجعِ معماری: `ARCHITECTURE-SOT.md` در ریشه.
