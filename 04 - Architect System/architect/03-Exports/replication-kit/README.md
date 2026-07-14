---
type: runbook
status: draft
tags: [replication, scaffold]
created: 2026-07-06
updated: 2026-07-06
---

# Replication Kit — بازسازی کامل vault agent-first

کپی دقیقِ قابلیت‌ها و featureهای این سیستم، بدون دیتای شخصی و بدون secret.

## محتویات

| چی | کجا | چیست |
|---|---|---|
| `BLUEPRINT.md` | ریشه kit | spec کامل همه لایه‌ها — مخصوصاً Architect (§۶): P1–P11، ۵ کامپوننت core، autonomy ladder، kill-switch، حلقه خودبهبودی gated، مدل بودجه، دو مغز |
| `scaffold.py` | ریشه kit | ساخت اسکلت در هر مقصد خالی — بدون هیچ overwrite |
| `seed/` | ریشه kit | خود اسکلت: قانون اساسی + Property Schema + ۶ template + validators واقعی (`validate_frontmatter.py`، `find_broken_links.py`، `gitleaks.toml`) + `.agentignore` + `.claude/` (deny + rules) + اسکلت‌های Dashboard/Agents/Architect/_memory |

## استفاده

```bash
python scaffold.py "D:\new-vault" --git-init
```

## چه چیزی عمداً کپی نشده

- محتوای `_code` (runtime لایه مادر — طبق `.agentignore` قفل است؛ بازسازی‌اش فاز ۵ در BLUEPRINT §۱۰).
- هر دیتای پروژه، نوت شخصی، عکس، لاگ تلگرام.
- هر secret، مسیر secret، یا ارجاع به فایل secret مشخص.

## اصل حاکم بر replica

همان اصل vault مادر: ایجنت می‌خواند/تشخیص می‌دهد/پیشنهاد می‌دهد؛ **انسان verdict می‌دهد.** §Security Gate جدید از روز اول بسته است تا مالک ROTATION_CHECKLIST خودش را سبز کند.
