---
type: moc
status: ready
tags: [4d, obsidian, foundation, architecture]
created: 2026-07-16
updated: 2026-07-16
---

# 4D × Obsidian Foundation — Start Here

> بسته‌ی پایه و **کاملاً نظری** برای اینکه یک ایجنت بعدی، پس از راستی‌آزمایی و رأی مالک، اتصال 4D به Obsidian را فازبه‌فاز کامل کند. این بسته هیچ runtime، کد، registry، داشبورد یا داده‌ی زنده‌ای را تغییر نمی‌دهد.

## وضعیت و مرجع واقعی

- Vault قابل‌مشاهده: `F:\backup`
- آینه/نسخه‌ی قابل‌مشاهده‌ی 4D: `F:\backup\4d_system`
- ادعای بعضی اسناد درباره‌ی نسخه‌ی Desktop یا git‌دار باید در شروع اجرای بعدی دوباره راستی‌آزمایی شود.
- کد و اجرای واقعی بر اعداد و وضعیت‌های تاریخی اسناد مقدم‌اند.
- فایل `.env` وجود دارد اما محتوایش در این کار خوانده نشده و نباید وارد نوت‌ها شود.

## مرز سه سیستم — قاطی نکن

1. **Architect/_ops** = HEAD و منبع حاکمیت اکوسیستم.
2. **4D System / Brain-OS** = مغز پژوهشی مستقل با دو هدف SOG و cognition testbed.
3. **4D `control_plane/`** = پلین داخلی همان limb؛ با NBB-CP یکی نیست.
4. **NBB-CP** = portable sibling/twin مستقل؛ ادغام آن تصمیم جداگانه است.

اصل رابطه: **coupled-not-merged**؛ evidence رو به بالا، policy envelope رو به پایین، بدون ساخت control-plane چهارم.

## ترتیب مطالعه برای ایجنت نهایی

1. [[01-FOUNDATION-AND-BOUNDARIES]]
2. [[02-OBSIDIAN-INFORMATION-ARCHITECTURE]]
3. [[03-THEORETICAL-SYSTEM-DESIGN]]
4. [[04-PHASE-PROMPTS]]
5. [[05-MASTER-COMPLETION-PROMPT]]
6. [[06-LIVING-OPTIMIZED-SYSTEM-TARGET]]
7. [[07-MLP-RELU-OPTIMIZATION-DOCTRINE]]

سپس منابع کانونی موجود:

- [[01 - Dashboard/HANDOFF]]
- [[06 - Architecture Maps/TRI-PLANE RECONCILIATION - ops vs NBB-CP vs 4D-control-plane]]
- [[06 - Architecture Maps/Property Schema]]
- `4d_system/PROJECT_STATE.md`
- `4d_system/MANIFEST.yaml`
- `4d_system/control_plane/registry.yaml`

## خروجی مورد انتظار آینده

هدف نهایی فقط bridge نیست؛ هدف یک **سیستم زنده و بهینه** است: stateful، self-observing، heartbeatدار، human-gated، metric-driven، و قابل rollback. تعریف دقیق در [[06-LIVING-OPTIMIZED-SYSTEM-TARGET]] و دکترین بهینه‌سازی عددی/سیستمی در [[07-MLP-RELU-OPTIMIZATION-DOCTRINE]].

```text
4D runtime (black box)
  └─ sanitised/read-only evidence adapter
       └─ Obsidian staging notes
            └─ human review / evidence gate
                 └─ canonical knowledge + dashboard views
                      └─ Architect/_ops registry visibility
```

Obsidian **کنترل‌پلین، دیتابیس runtime یا محل secret نیست**؛ یک Human Knowledge & Review Plane است.

## قوانین مادر

- Improve, don't rewrite. Extend, don't replace.
- `core/`، TCB، تست‌ها و لنگرهای SOG دست‌نخورده‌اند.
- ابتدا read-only و shadow؛ نوشتن فقط proposal و staging.
- external action، self-code apply، daemon start، cloud spend و canonical promotion همگی owner-gated.
- هیچ ادعای consciousness/qualia/sentience ساخته نشود.
- UNKNOWN هرگز به PASS تبدیل نشود.
- هر فاز: **Current / Delta / Preserved / Rollback / Evidence / Human Verdict**.

## این بسته چه چیزی را انجام نداده است؟

- تست اجرا نکرده؛ بنابراین هیچ عدد «سبز فعلی» ادعا نمی‌شود.
- `brain/vault_sync.py` را تغییر یا فعال نکرده است.
- 4D daemon، Telegram، Streamlit یا cloud API را اجرا نکرده است.
- فایل‌های Vault موجود را جابه‌جا، حذف یا بازنویسی نکرده است.
- تصمیم `VQ-4D-001` یا تصمیم اتصال سه‌پلین را به‌جای مالک نگرفته است.

## نقطه توقف

این بسته برای تحویل به ایجنت بعدی **READY** است؛ اجرای فازهای عملی بدون خواندن Master Prompt و گرفتن gate مربوط ممنوع است.
