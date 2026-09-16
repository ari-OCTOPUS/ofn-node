# KB-12 — Australia Compliance & Market Governance

> ستونِ قانونیِ Brushline. سه‌گانهٔ AU + اصلاحاتِ Privacy Act 2024 (گراند‌شده). اجراییِ این KB = KB-07 (Gate)، KB-03 (publishing)، KB-09 (consent).
> ⚠️ این سند راهنمای عملیاتی است، نه مشاورهٔ حقوقی؛ قبل از اجرا با وکیلِ AU تأیید شود (به‌ویژه قلم‌های «verify»).

---

## ۰. خلاصهٔ سریع

چهار قانون: **Spam Act 2003**، **Privacy Act 1988 + اصلاحاتِ 2024**، **Australian Consumer Law (ACL)**، **Do Not Call Register**. ناظرها: ACMA، OAIC، ACCC. نکتهٔ ۲۰۲۶: محیط از «راهنمایی» به «enforcement فعال» منتقل شده (OAIC sweep، statutory tort، جریمه‌های بالاتر).

---

## ۱. Spam Act 2003
- هر email/SMS/IM/DM **تجاری** نیاز به consent (express یا inferred در محدودهٔ رابطهٔ تجاریِ مرتبط).
- بدونِ consent نمی‌توان پیامِ «consent بخواه» فرستاد (خودش spam).
- Sender ID: نام + ABN.
- Unsubscribe: کارکردی، بدونِ login، اقدام ظرفِ ۵ روز؛ suppression list نگه‌داری شود.
- جریمه: قابلِ‌توجه per breach (ACMA) — **رقم دقیق verify**.

## ۲. Privacy Act 1988 + اصلاحاتِ 2024 (گراند‌شده)
**Privacy and Other Legislation Amendment Act 2024** (Royal Assent ۱۰ دسامبر ۲۰۲۴، اکثر مفاد در اجرا):

| تغییر | اثر بر Brushline | زمان |
|---|---|---|
| **Statutory tort** (serious invasion of privacy) | افراد می‌توانند مستقیم شکایت کنند (intrusion/misuse، intentional/reckless)؛ no-win-no-fee ممکن | از ۱۰ ژوئن ۲۰۲۵ |
| **ADM disclosure (APP 1.7)** | privacy policy باید افشا کند که AI در تصمیمِ مؤثر بر فرد دخیل است — **مستقیماً Brushline** (AI در lead handling) | از ۱۰ دسامبر ۲۰۲۶ |
| **جریمه‌ها** | OAIC infringement تا ~AUD ۶۶٬۰۰۰/contravention؛ mid-tier civil ~AUD ۶۶۰٬۰۰۰ (فرد)/۳٫۳M (شرکت) | در اجرا |
| **small-business exemption ($3M)** | احتمالِ حذف در tranche 2 (~۲۰۲۶/۲۷)؛ به آن **تکیه نکن** | آینده |
| **OAIC sweep** | هدف‌گیریِ real estate agents (شریکِ ارجاعِ Brushline) | از ژانویه ۲۰۲۶ |
| **fair & reasonable** + تعریفِ گسترده‌ترِ personal info | consent باید proactive/unbundled؛ pre-ticked نامعتبر | tranche 2 |

**APP 7 (direct marketing):** reasonable expectation/consent؛ opt-out ساده؛ sensitive → consent صریح.

> اقدامِ Brushline: (۱) privacy policy با **افشای ADM** (APP 1.7)؛ (۲) consent proactive/unbundled، نه pre-ticked؛ (۳) فرایندِ access/correction/deletion؛ (۴) breach response (اعلان OAIC ظرفِ ۷۲h در موارد eligible)؛ (۵) تکیه‌نکردن به small-business exemption.

## ۳. ACL — no false/misleading claims
«بهترین/#1»، warranty بدونِ مدرک، «تأییدشده» بی‌سند = ریسکِ قانونی. اجراییِ این = `check_acl_claims` در KB-07.

## ۴. Data Sovereignty
دادهٔ شخصی/حساسِ مالیِ مشتری: ترجیحاً ذخیره در AU؛ هرگز وارد ابزارِ عمومیِ AI یا LANGAR (INV-2). APP 8 برای cross-border disclosure.

## ۵. نگاشت به Brushline governance
| قاعده | قانون |
|---|---|
| consent + sender-ID/ABN + unsubscribe ۵-روزه + suppression | Spam Act |
| no pre-ticked؛ proactive opt-in؛ ADM disclosure؛ access/delete | Privacy Act 2024 |
| no false claim (Gate) | ACL |
| داده در AU، نه LANGAR (INV-2) | sovereignty/APP 8 |

## ۶. قواعدِ سخت
۱. هیچ پیامِ تجاری بدونِ consent. ۲. privacy policy باید ADM را افشا کند (۲۰۲۶). ۳. هیچ ادعای دروغ. ۴. به small-business exemption تکیه نکن. ۵. PII در AU.

## ۷. قدم بعدی
verify با وکیل: جریمه‌های دقیقِ Spam Act، وضعیتِ tranche 2، نیازِ دقیقِ ADM disclosure. اجراییِ این قواعد در KB-07/03/09. (جزئیاتِ بازار: KB-13.)
