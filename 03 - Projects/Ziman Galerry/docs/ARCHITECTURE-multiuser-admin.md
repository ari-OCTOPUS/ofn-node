---
type: architecture
project: "[[03 - Projects/Ziman Galerry/PROJECT]]"
status: draft
tags: [ziman/architecture, design]
created: 2026-07-04
updated: 2026-07-04
---

# 🏛️ معماریِ چند-کاربره با ادمین — طرحِ اولیه (v0)

> طرحِ اولیه برای بحث — «بعداً دقیقش می‌کنیم». هنوز پیاده‌سازی نشده.

## ۱. خلاصهٔ سریع
مسیرِ تبدیلِ **مغزِ کنترلِ تک‌کاربره‌ی فعلی** به یک **control-plane چند-کاربره** که **تو ادمینِ کلّی** هستی
و بقیه با نقش‌های محدود (operator / viewer) کار می‌کنند. این سند **نقشه** است، نه کد؛
تغییرات را پله‌پله و **behavior-preserving** انجام می‌دهیم تا چیزی که الان کار می‌کند نشکند.

## ۲. تحلیل

### وضعیتِ فعلی (تک‌کاربره)
- یک مالک (`OWNER_CHAT_ID`)، یک `projects.yaml` سراسری، یک SQLite، داشبوردِ **بدونِ auth**، رباتِ تلگرام فقط به مالک جواب می‌دهد.
- هیچ مفهومِ «کاربر» یا «مالکیتِ پروژه» وجود ندارد؛ همهٔ پروژه‌ها global اند.

### قیود و ریسک‌ها
- **قید:** نباید هستهٔ تست‌شدهٔ فعلی بشکند → تغییرات افزایشی و پشتِ authz متمرکز.
- **ریسکِ امنیتی #۱:** داشبورد الان write ندارد و auth ندارد؛ در حالتِ چند-کاربره اگر کنترل (start/stop) به وب بیاید، **بدونِ auth یک درِ باز است**.
- **ریسکِ #۲:** جداسازیِ رمزها بین کاربران — operator نباید به رمزِ tenantِ دیگر برسد.
- **ریسکِ #۳:** ردگیری (audit) — بدونِ `actor` روی هر اکشن، پاسخگویی ممکن نیست.

### فرض‌های صریح (باید تأیید کنی)
- **[Assumption]** «کاربر» = **اپراتورهای تیم/چند-tenant که پروژه کنترل می‌کنند**، نه مشتریانِ نهاییِ زیمان (CRM). ← سؤالِ بازِ ۱.
- **[Assumption]** در فازِ چند-کاربره احتمالاً به **VPS همیشه‌روشن** می‌رویم (README همین را پیش‌بینی کرده).
- **[Assumption]** تلگرام کانالِ اصلیِ کنترل می‌ماند؛ وب برای مشاهده/ادمین.

## ۳. راه‌حلِ پیشنهادی (مدلِ مفهومی)

### نقش‌ها (RBAC)
| نقش | می‌تواند | نمی‌تواند |
|---|---|---|
| **admin (تو)** | مدیریتِ کاربران، همهٔ پروژه‌ها، نگاشتِ رمز، halt/resume سراسری، دیدنِ auditِ کامل | — |
| **operator** | start/stop/test فقط روی پروژه‌های **assign‌شده به خودش** | مدیریتِ کاربر، تعویضِ رمز، دیدنِ tenantِ دیگر |
| **viewer** | فقط status/داشبوردِ محدود به scope خودش | هر اکشنِ کنترلی |
| **(آینده) service-token** | اکشن‌های مشخص و محدود برای اتوماسیون | خارج از scope تعریف‌شده |

### جداسازیِ داده (per-user isolation)
- **users**: `id, name, telegram_chat_id, role, status, created`.
- **مالکیتِ پروژه**: به هر پروژه `owner_user_id` + `allowed_user_ids[]` (یا جدولِ جدا `project_acl`).
- **store**: افزودنِ `actor_user_id` به جدولِ `events` (audit)؛ `status_all` بر اساسِ scope فیلتر شود.
- **secrets**: یک vaultِ KeePassXC می‌ماند ولی عنوان‌ها **namespace per-tenant** (مثلِ `zimAN/anthropic-key`)؛ فقط admin نگاشت را تغییر می‌دهد.

### احراز هویت (auth)
- **تلگرام:** `chat_id → user → role` جایگزینِ `OWNER_CHAT_ID` تکی می‌شود؛ چتِ ناشناس رد.
- **داشبورد:** الان بی‌auth. سه گزینه در بخشِ Trade-offs مقایسه شده؛ پیشنهاد: پشتِ **reverse-proxy + OIDC**.

## ۴. نقاطِ تغییر در `control-brain` (نقشهٔ دقیق)
| فایل | تغییر |
|---|---|
| `core/authz.py` **(جدید)** | تنها منبعِ حقیقتِ مجوزها: `can(actor, action, project) -> bool`. |
| `core/models.py` | افزودنِ `User`, `Role`؛ گسترشِ `Project` با `owner_user_id`/`acl`. |
| `core/registry.py` | خواندنِ `users.yaml` + ACLِ پروژه‌ها (یا از DB). |
| `core/store.py` | جدولِ `users`؛ `actor_user_id` روی `events`؛ (در صورتِ نیاز) pid با scope. |
| `core/manager.py` | هر متد یک `actor` می‌گیرد → **اول authz، بعد اکشن**؛ `status_all` فیلترشده. |
| `core/safety.py` | `halt/resume` سراسری **admin-only** (بعداً haltِ per-tenant). |
| `adapters/telegram_bot.py` | resolve `chat_id→user`؛ دستورهای admin (`/adduser`, `/halt`) محافظت‌شده. |
| `adapters/dashboard.py` | لایهٔ auth + نمای فیلترشدهٔ per-user؛ اکشن‌های write پشتِ POSTِ authenticated + CSRF. |
| `core/secrets.py` | ACL روی مرجعِ رمز؛ operator فقط رمزِ پروژه‌های خودش. |

## ۵. مسیرِ مهاجرت (بدونِ شکستنِ چیزی)
- **فاز ۰ (الان):** تک‌کاربره، `OWNER_CHAT_ID`. ✅ کار می‌کند.
- **فاز ۱:** `users` + `authz.py` با **یک adminِ seed‌شده (تو)**. رفتار عوض نمی‌شود؛ همهٔ پروژه‌ها مالِ admin.
- **فاز ۲:** نقش‌های operator/viewer + ACLِ پروژه؛ نگاشتِ چند-chatِ تلگرام.
- **فاز ۳:** auth داشبورد (reverse-proxy/OIDC) + اکشن‌های writeِ وب.
- **فاز ۴:** جداسازیِ رمزِ per-tenant + نمای audit + rate-limit؛ انتقال به VPS با TLS.

## ۶. Trade-offs — گزینه‌های authِ داشبورد (امتیاز ۱–۱۰)
| گزینه | Cost | Complexity | Scalability | Maintainability | Security | Time | Vendor lock-in |
|---|---|---|---|---|---|---|---|
| **A) session/token دستیِ درون‌اپ** | ۹ (کم) | ۵ | ۵ | ۵ | ۵ | ۸ (سریع) | ندارد |
| **B) reverse-proxy + OIDC (Authelia/Keycloak، open-source)** ⭐ | ۸ | ۶ | ۸ | ۸ | ۹ | ۶ | کم (استانداردِ باز) |
| **C) IdPِ managed (Auth0/Clerk)** | ۶ (pricing پلکانی) | ۳ | ۹ | ۸ | ۹ | ۸ | **بالا** |

**پیشنهاد (بیشترین ROI):** منطقِ RBAC را **درون‌اپ و بدونِ وابستگی** بساز (فاز ۱–۲، ارزان و سبک)؛
برای auth داشبورد در فاز ۳ به‌جایِ ساختنِ auth، آن را **پشتِ Authelia (OSS)** بگذار —
امنیتِ بالا، بدونِ vendor lock-in، و کدِ اپ ساده می‌ماند. `Auth0/Clerk` فقط اگر سرعتِ راه‌اندازی از هزینه/lock-in مهم‌تر شد.

## ۷. ملاحظاتِ امنیتی (کلیدی)
- **Least privilege:** operator نه به رمز دست می‌زند، نه به tenantِ دیگر.
- **Audit کامل:** `actor_user_id` روی هر اکشن (گسترشِ جدولِ `events` موجود).
- **Kill-switch:** `halt` سراسری به‌عنوانِ ادمین باقی می‌ماند.
- **رمزها:** هرگز log/چاپ نمی‌شوند (الان هم همین‌طور است)؛ در VPS بدونِ plaintext + TLS + firewall.
- **وب:** تا auth نیامده، **هیچ اکشنِ کنترلی نباید از وب expose شود** (فعلاً کنترل فقط تلگرام).

## ۸. سؤال‌های باز (این‌ها را «بعداً دقیق می‌کنیم»)
1. «کاربر» = **اپراتورهای تیم** (control-plane چند-tenant) یا **مشتریانِ نهاییِ زیمان** (CRM)؟ ← این کلِ مدل را تعیین می‌کند.
2. مقصدِ استقرارِ چند-کاربره: همان لپ‌تاپِ همیشه‌روشن یا **VPS**؟
3. چند کاربر، و آیا operatorها پروژه‌ها را **share** می‌کنند یا هرکس **مالِ خودش**؟
4. فقط تلگرام، یا **loginِ وب** هم برای کاربرانِ بدونِ تلگرام؟

## ۹. قدم‌های بعدی
1. به سؤالِ ۱ جواب بده (اپراتور vs CRM) تا مدلِ نهایی قفل شود.
2. من فاز ۱ (users + `authz.py` + adminِ seed) را به‌صورتِ behavior-preserving پیاده و تست می‌کنم.
3. بعد فاز ۲ (RBAC + ACLِ پروژه) روی همان هستهٔ تست‌شده.
