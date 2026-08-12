---
type: draft
status: draft-awaiting-gate
gate: GATE 0 (ساخت لینک‌ها داخل داشبورد OF = پس از ساخت اکانت)
created: 2026-07-10
tags: [project-f, draft, tracking-links]
---

# طراحی Tracking-Link — draft-awaiting-gate

> سه قید الزامی (T6-verified): (۱) **هیچ PII/شناسه در URL یا نام لینک** — فقط کد کانال؛ (۲) **هیچ cloaking**: لینک OF هرگز پشت redirect پنهان نمی‌شود تا به پلتفرمی که OF-link را ممنوع می‌کند (TikTok/IG) تزریق شود — در آن پلتفرم‌ها فقط لینک hub می‌رود و خود hub هم فقط در bio؛ (۳) لینک مستقیم OF فقط در X ‏(bio ممنوع نیست، pin مصوب)، Reddit ‏(subهایی که اجازه می‌دهند)، hub، و ایمیل.

## نقشهٔ لینک‌ها (ساخت در OF: Statements → Tracking Links)
| کد لینک | محل استفاده | می‌سنجد |
|---|---|---|
| `x-pin` | pinned tweet | تبدیل هاب برند X |
| `x-bio-hub` *(لینک GAML، ردیابی سمت GAML)* | bio X → hub | ترافیک bio |
| `rd-a1` | پست‌های Reddit ‏(A1) — یک لینک واحد برای همهٔ subها در شروع | موتور Reddit کل |
| `rd-⟨sub⟩` | از هفتهٔ ۴ برای ۳ sub برتر، تفکیکی | بهترین sub |
| `hub-main` | دکمهٔ ۱ hub | تبدیل hub→OF |
| `hub-fansly` *(معادل Fansly اگر feature داشت، وگرنه ردیابی GAML)* | دکمهٔ ۲ hub | split دو پلتفرم |
| `em-news` | ایمیل ماهانه | کانال owned |
| `bs-test` | آزمایش Bluesky ‏(#۱۷، پس از تصویب) | کانال جدید |

## قواعد
- نام‌گذاری فقط `کانال-نقش` با حروف کوچک؛ هرگز نام/تاریخ تولد/مکان/دستگاه.
- هر کانال جدید = اول لینک، بعد پست (هیچ ترافیک بدون attribution).
- خواندن هفتگی در حلقهٔ جمعه → ستون «کلیک hub→OF» داشبورد؛ در حجم <۲۰۰ کلیک فقط جمع‌آوری، نه قضاوت (T6/M2 top-5 counter-arg).
- عمر لینک: دائمی؛ حذف لینک = حذف تاریخچه → به‌جای حذف، «retired» در Fable5 علامت بخورد.
