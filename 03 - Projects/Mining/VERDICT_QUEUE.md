---
type: log
project: "[[03 - Projects/Mining/PROJECT]]"
status: active
tags: [mining, decisions]
created: 2026-07-03
updated: 2026-07-28
---

# ✅ Mining VERDICT_QUEUE

> به‌روزرسانیِ ۲۰۲۶-۰۷-۲۸ — چهار تصمیم با رأیِ مالک بسته شد. شواهد در
> [[03 - Projects/Mining/DecisionLog|DecisionLog]] (D-008/D-009/D-011).

| ID | تصمیم | گزینه‌ها | وضعیت | اثر |
|---|---|---|---|---|
| MIN-V1 | چند rig/Orange Pi قابل‌استفاده؟ | عدد | ✅ **closed 2026-07-28** — ۱۶۲ نود (۱۶ OPI + ۱۴۰ ESP32 + ۲ FPGA)؛ پایهٔ هش = ۱۶ | [[03 - Projects/Mining/Hardware Registry & Runbook\|رجیستری]] بازنویسی شد |
| MIN-V2 | برق <$0.05/kWh یا solar؟ | yes/no/unknown | ✅ **closed 2026-07-28** — خورشیدیِ نصب‌شده و فعال → گیت پاس | گیتِ آزمایش باز شد |
| MIN-V3 | الان هیچ mining فعال نیست؟ | yes/no | ✅ **closed 2026-07-28** — همه خاموش، صفر ماینِ فعال | safety state تأیید شد |
| MIN-V4 | Hardware Registry پر شود؟ | yes/no | 🔄 **open — روی مالک** | شمارش قفل شد؛ IP/سلامتِ تک‌نود هنوز `[To measure]` |
| MIN-V5 | wallet access برای agent صفر بماند؟ | yes/no | ✅ **closed 2026-07-28** — صفر می‌ماند (D-11 تأیید شد) | hard rule |
| MIN-V6 | coin scouting فقط report باشد؟ | yes/no | ⚠️ **open — تضادِ فعال با D-10** | scope — پایین |

---

## ⚠️ MIN-V6 — تنها بلوکرِ تصمیمیِ باقی‌مانده

مالک خواسته Coin Hunter Bot «هر هفته کوین پیدا کند، **ماین کند، عوض کند**». سه فعل، سه سطحِ ریسکِ متفاوت:

| فعل | یعنی چه | تضاد با قاعده؟ |
|---|---|---|
| **پیدا کردن** | اسکن + امتیازدهی طبق [[03 - Projects/Mining/Coin Scouting Framework\|چارچوب]] | ❌ هیچ — امروز هم مجاز است |
| **ماین کردن** | سوییچِ الگوریتم/پول روی نودهای خودی | ❌ هیچ — پول جابه‌جا نمی‌شود |
| **عوض کردن** | swap/trade یک کوین با کوینِ دیگر | ✅ **مستقیماً D-10** — swap یعنی معامله |

**D-10:** «هر buy/sell/withdraw = HARD_STOP — فقط انسان.»

پس تا رأیِ صریحِ مالک، دو فعلِ اول اجرا می‌شوند و سومی نه. سؤالِ دقیق:

> بات حق دارد **خودکار** swap کند، یا فقط کارتِ پیشنهاد بسازد و swap را دستِ خودت انجام می‌دهی؟

ثبت‌شده در [[00 - Inbox/AGENT_QUESTIONS|AGENT_QUESTIONS]]. **تا جواب، هیچ مسیرِ swapی ساخته نمی‌شود.**
