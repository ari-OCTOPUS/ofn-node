---
type: knowledge
kind: discovery-ledger
status: active
updated: 2026-08-16
created: 2026-08-16
created_by: agent (deep-seams, دوازدهمین مگاپرامپت)
audience: owner
tags: [octopus, deep-seams, self-improve, vote-cards, propose-only]
evidence: "[[../06-EVIDENCE/DEEP-SEAMS-2026-08-16|DEEP-SEAMS]]"
next_free_contradiction: C-029
---

# DISCOVERY — Deep-Seams Ledger (2026-08-16)

> ماشینِ خودبهبودی باید بسته، سنجیده، و دیدنی باشد. چهار فیکس additive امروز نشست؛ سه درز نیاز به رأی دارند. صداقت بر پیروزی مقدم.

## چه چیزی بهتر شد (عدد)

| قبل | بعد |
|---|---|
| ۲۴/۲۴ FAIL روی `attribution.claimed=0`؛ recall هرگز هدف نبود | `propose()` → `recall-events` baseline **۹۰** (money deadline-exhausted، streak=24) |
| حذفِ دمِ ledger.jsonl → `verify()=ok` | `verify_tip()` همان را می‌گیرد؛ `verify()` دست‌نخورده |
| digest یادگیری = `{}` شبیه «ردی نبود» | `verdicts_file=False` · `verdicts_n=0` صریح |
| vitals خودیادگیری پراکنده | پنج gauge در digest: بستن حلقهٔ ۷روزه **۰/۱۵ = 0.0٪** |

## کارت‌های رأی (حداکثر ۷ — این ۵ تا)

### [VOTE 1] experiments را وصل کنیم یا بازنشسته؟
```
الان: _ops/hypothesis_engine/experiments/ صفر import تولیدی دارد (کاتالوگ طبقهٔ ۷)
پیشنهاد: یا یک caller در مسیر سایه (مثل هولداوت L1) یا STATUS retired مثل genome-loop
اگر تأیید: additive؛ بدون فلگ تازه تا طرح مشخص شود
ریسکِ بی‌عمل: کد کامل، ارزش صفر — همان الگوی effector dead-output
نه: اجرای deceptive-grid روی دادهٔ زنده
```

### [VOTE 2] رأیِ improve از کدام دکمه به یادگیرنده برسد؟
```
الان: OCTOPUS_WIRE_IMPROVE_LEARN=1 در flags.cmd · improve-verdicts.jsonl روی دیسک غایب
      هوک در live_loop هست؛ کارت‌های upgrades-digest از آن مسیر نمی‌آیند
پیشنهاد: همان هوک را به کارتِ digest هم وصل کن (observe-only اگر جریمه نخواهی)
ریسکِ بی‌عمل: مالک «نه» می‌گوید و همان دسته دوباره می‌آید — ادعا یادگیری، عمل صفر
نه: روشن‌کردن فلگ تازه؛ این فلگ از قبل روشن است
```

### [VOTE 3] money-claimed را در کاتالوگ نگه داریم؟
```
الان: deadline_cycles=2 اجرا شد → صدر رفت به recall-events (۹۰).
      اولویت اعلام‌شدهٔ مالک هنوز «پول اول» است.
پیشنهاد: بماند (فیلدِ خودِ کاتالوگ را اجرا کردیم) مگر بخواهی money تا ابد قفل باشد
اگر نه: deadline را برای money-claimed بردار (صریح، نه باگِ برگشتی)
```

### [VOTE 4] tip-commit لجر را قانون روزانه کنیم؟
```
الان: verify() LAW است (دم را نمی‌بیند). verify_tip() additive است.
      organism روزانه seal می‌کند اگر unsealed باشد.
پیشنهاد: ledger_ok روزانه = verify() AND verify_tip() بعد از اولین seal
نه: عوض‌کردن verify() — هم‌کلاس verify_scar_aware، سوئیچ جدا
```

### [VOTE 5] (قدیمی، دست نزن) C-026 + پنج کارت HARDTEST + بودجهٔ deepseek
```
همچنان صف مالک — این نشست دست نزد.
```

## دست نزن

فلگ تازه · TCB · حذف · ری‌استارت بی‌نیاز · تماس پولی · اولامای ۷بی
