# جواب‌های مالک به مگاپرامپت نهایی — ۲۰۲۶-۰۸-۰۷

این سند جواب‌های مالک (سبا) به سؤال‌های F-۱ و F-۲ مگاپرامپت نهایی است.
ایجنت بعدی این را قبل از شروع بخواند.

## جواب‌ها

| ID | سؤال | جواب مالک | اقدام |
|---|---|---|---|
| **F-۱** | فاز ۴ (اتصال inline OFN↔memory) انجام شود یا bridge script کافی است؟ | **انجام فاز ۴** | OFN باید مستقیم از `memory_corpus` بخواند و بنویسد. |
| **F-۲** | دادهٔ قدیمی `sessions.consent` در hypno مهم است؟ | **migrate شود** | دادهٔ قدیمی به `safety_acknowledged` کپی شود، نه حذف. |

## ترتیب اجرا (همه فازها)

```
فاز ۰: WAL checkpoint + backup کامل + git status
فاز ۱: B-۲ panel_note — حذف brain call از write path
فاز ۲: B-۳ consent → safety_acknowledged + MIGRATION دادهٔ قدیمی
فاز ۳: B-۸ thread safety در hypno
فاز ۴: اتصال inline OFN ↔ memory_corpus (خواندن + نوشتن)
فاز ۵: pytest + restart + smoke + گزارش نهایی
```

## مکان مگاپرامپت

```
/home/ari/hypno-fugu-mini/docs/docs/agent-context/archived/MEGAPROMPT-UNIFY-FINAL.md
/home/ari/ofn/docs/agent-context/archived/MEGAPROMPT-UNIFY-FINAL.md
```

هش: `63ad9bd929a6622e6a537c15bbe1551f10ad491ddd5a730231ff8abce4d5974d`

## وضعیت فعلی (تأییدشده)

```
pytest:      fugu_core 25 · OFN 1512+5skip · hypno 62 = 1599 سبز
سرویس‌ها:    ofn · hypno-fugu-mini · cloudflared → همه active
دامنه‌ها:    panel/ziman/lead/studio/app/hypno → همه 200
مغز مشترک:  Sakana fugu (OFN + hypno)
حافظه:      memory.sqlite سه‌لایه (132 chunk shared)
quota:      35/35/20/10 = 1.00
```

## ممنوعیت‌ها (یادآوری)

- هیچ دیتایی از دست نمی‌رود (migration = کپی، نه بازنویسی)
- WAL checkpoint قبل از هر کپی
- `assistant.sqlite` و `hypno.sqlite` بازنویسی نشوند
- consent OFN (`may_publish`) هرگز در hypno صدا زده نشود
- متن فنی در UI ممنوع (D-22)
- هر فاز: restart + pytest + smoke
