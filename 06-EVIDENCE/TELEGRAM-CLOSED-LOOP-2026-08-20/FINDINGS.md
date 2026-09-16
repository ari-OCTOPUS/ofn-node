---
type: evidence
status: active
tags: [telegram, findings, 2026-08-20]
created: 2026-08-20
updated: 2026-08-20
created_by: agent
project: "[[04 - Architect System/architect/PROJECT]]"
---

# سه یافته — Telegram Closed Loop

ماشین: `FINDINGS.json`

## CORRECT_ACCEPTED_INVALID_TURN_ID

`/correct` توکن اول را `turn_id` می‌گیرد و هرگز آن را با `memory_id` یا `update_id` زنده نمی‌سنجد. ردیف حافظه همیشه `turn_id=owner-cmd` است. زنده: `update_id=223883331`. بازتولید آفلاین پذیرفته شد.

## STALE_GATE_LABEL_IN_REPLY

A13 قبلاً PASS است، ولی پاسخ local-degraded هنوز می‌گوید «مدل پولی تا گیت A13 خاموش است». همان برچسب در `capabilities_text`. زنده: `update_id=223883330` · ۱۰۶ کاراکتر.

## MISSING_ACK_FOR_/remember

ارسال پاسخ `/remember` برای `update_id=223883328` در `tg-send-log` با `ok=false` ثبت شد (۷۵ کاراکتر، sha `eb6febc35bed45d5`). ردیف حافظه روی دیسک هست (`mem-6c528a350df6`)؛ ACK روی سیم تأیید نشد.
