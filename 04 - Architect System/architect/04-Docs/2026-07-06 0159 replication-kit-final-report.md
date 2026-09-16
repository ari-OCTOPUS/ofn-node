---
type: report
status: ready
tags: [replication, architect, governance]
created: 2026-07-06
updated: 2026-07-06
created_by: agent
sources:
  - "[[_PROJECT_INSTRUCTIONS]]"
  - "[[04 - Architect System/architect/01-Project/SYSTEM-BLUEPRINT-v2]]"
  - "[[_memory/TWO-BRAIN-CONTROL-BLUEPRINT]]"
  - "[[05 - Agents/AGENT_REGISTRY]]"
  - "[[06 - Architecture Maps/Property Schema]]"
  - "[[06 - Architecture Maps/SYSTEM_MAP]]"
---

# گزارش نهایی — Replication Kit (کپی دقیق قابلیت‌های vault + Architect)

## ۱. خواسته و خروجی

خواستهٔ آری: «کپی‌برداری دقیق از تمام قابلیت‌ها و featureهای این ساختار، مخصوصاً قسمت Architect» — به‌صورت template قابل‌اجرا، مقصد `00 - Inbox`.

خروجی: **`04 - Architect System/architect/03-Exports/replication-kit/` — ۵۳ فایل، تماماً additive** (هیچ فایل موجودی ویرایش/حذف/جابه‌جا نشد).

| جزء | چیست |
|---|---|
| `BLUEPRINT.md` | spec کامل ۸ لایه: ساختار پوشه‌ها · قانون اساسی · Property Schema · حافظه/handoff · امنیت defense-in-depth · **Architect (§۶ — عمیق‌ترین بخش)** · ناوگان ایجنت‌ها · Dashboard · اعتبارسنجی · نقشهٔ بازسازی ۶فازی |
| `scaffold.py` | بازسازی اسکلت در هر مقصد خالی؛ هرگز overwrite/حذف نمی‌کند؛ `--git-init` اختیاری |
| `seed/` (۵۰ فایل) | کپی دقیق فایل‌های generic واقعی + اسکلت‌های sanitized |

## ۲. پوشش Architect (مطابق SYSTEM-BLUEPRINT-v2 و TWO-BRAIN)

ثبت‌شده در `BLUEPRINT.md §۶`: اصول P1–P11 · ۵ کامپوننت core (Telegram bot با Intent-Router rule-based و step-up passphrase · Brain/Router · Research Engine با دو checkpoint · Memory با `origin` و `<external_data>` · Safety Kernel) + دو satellite · قرارداد Tenant Adapter (read-only creds enforced) · نردبان L0–L3 و لیست سیاه human-only · kill-switch fail-closed (DB flag + STOP، چک هر round/هر commit) · حلقهٔ خودبهبودی با گیت سه‌شرطی + judge بین‌خانواده + cold-start ≥۵۰ trajectory · مدل بودجهٔ دو-mode ($2/$60 Normal · $10/$300 Growth) · eval/observability · چرخهٔ نسخه‌بندی blueprint با red-team (PROMPT-B) · مدل دو مغز و حلقهٔ کنترل ۶گامی.

## ۳. چه چیزی عیناً کپی شد (seed)

قانون اساسی (جدول اکوسیستم → placeholder) · `Property Schema.md` کامل · هر ۶ template · `validate_frontmatter.py` + `find_broken_links.py` + `gitleaks.toml` + `scripts/README.md` · `.agentignore` · `CLAUDE.md` · هر ۳ فایل `.claude/rules/`. اسکلت‌های نو: AGENT_REGISTRY (با وراثت §Gate) · RATIFIED-TASKS (درس bootstrap) · ROTATION_CHECKLIST (گیت از روز اول بسته) · SYSTEM_MAP/ECOSYSTEM · Home/HANDOFF/Brain · HEARTBEAT/EXPERIENCE-LEDGER · SOP/ROUTING تلگرام · DECISIONS/GAPS/BACKLOG/CHANGELOG/SYSTEM-BLUEPRINT-v1 · Weekly Review · AGENT_QUESTIONS.

## ۴. Sanitization (ریسک نشت)

- دو مسیر Read-deny شخصی در `settings.json` اصلی → با الگوی generic (`**/*wallet*` و مشابه) جایگزین شد؛ هیچ نام فایل secret واقعی در kit نیست.
- اسکن regex روی کل kit (کلید/توکن/آدرس/پسورد): تنها match یک کامنت توضیحی در `.agentignore` بود — **صفر مقدار محرمانه**.
- محتوای `_code`، دیتای پروژه‌ها، عکس‌ها، لاگ‌ها، نوت‌های شخصی: **عمداً کپی نشد** (بازسازی runtime = فاز ۵ بلوپرینت).

## ۵. تست

- `scaffold.py` در sandbox اجرا شد → ۵۰ فایل ساخته شد؛ مسیر خطای «مقصد ناخالی» و «overwrite» چک شده fail-closed است.
- هر دو validator روی vault تولیدشده: **frontmatter ۱۵/۰ خطا · لینک ۳۰/۰ شکسته — سبز.**
- خطای `git commit` در sandbox (نبود git identity) به WARN تبدیل شد — رفتار طراحی‌شده.

## ۶. محدودیت‌ها و ریسک‌های باقی‌مانده

- BLUEPRINT از اسناد خوانده شده، نه از کد `_code` (طبق `.agentignore`) — جزئیات پیاده‌سازی runtime ممکن است با سند فاصله داشته باشد (قانون خود vault: کد واقعی > سند).
- اعداد بودجه/متریک از SYSTEM-BLUEPRINT-v2 است؛ اگر v3 ratify شود، kit باید sync شود.
- kit سند نیت است؛ replica جدید از روز اول §Gate بسته دارد تا مالکش ROTATION را سبز کند.

## ۷. checkpoint — نیازمند verdict

**commit ممکن نیست: vault هنوز git repo نیست** و آری قبلاً به `git init` «نه» گفته (HANDOFF جلسه ۱۳؛ تغییر git = human-only در منشور). دستهٔ ۵۳+۲ فایلی این جلسه بدون checkpoint ماند — مثل جلسه ۹. اگر نظرت عوض شده، `git init` + commit اول را خودت بزن یا verdict صریح بده.
