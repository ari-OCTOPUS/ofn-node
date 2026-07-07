---
type: reference
kind: security-checklist
project: "[[07 - Knowledge/هیپنوتیزم  و خودآگاهی/PROJECT]]"
status: active
owner: آری
epistemic_status: speculative
tags: [security, rotation, secrets, checklist]
created: 2026-07-04
updated: 2026-07-04
---

# ROTATION_CHECKLIST — چرخشِ secretها و سخت‌سازی

> اقداماتِ **owner-only**. revoke/rotate/limit فقط با دسترسی به حساب‌های تو ممکن است و طبق قاعده‌ی امنیتی نباید توسط agent انجام شود. منبع: `TODO.md` #۱–۳ · `LessonsLearned.md` #۹ · `PROJECT.md` §Inventory/چک امنیتی.

## وضعیت زنده

| # | مورد | محل | وضعیت | اقدامِ تو |
|---|---|---|---|---|
| 1 | توکن ربات تلگرام | `Silabi-Bot/silabi_bot.py` خط ۶۶ | 🟩 کد اصلاح شد → `os.environ.get("TELEGRAM_TOKEN")` با fail-fast | اگر توکن واقعی بود: BotFather → `/revoke` → توکنِ جدید → `export TELEGRAM_TOKEN="…"` |
| 2 | نسخه‌ی زنده‌ی همان کد | `…\Documents\Claude\Projects\خویشتن\silabi_bot.py` | ⬜ خارج از vault | همان اصلاحِ خط ۶۶ را دستی اعمال کن |
| 3 | کلید Anthropic `sk-ant-api03-…` | `fusion-mvp/.env.example` | ⬜ خارج از vault | Anthropic Console → rotate + افزودن به `.gitignore` |
| 4 | سقفِ هزینه Anthropic ($۱۸۵) | Console → Settings → Limits | ⬜ | تأیید کن اعمال شده |
| 5 | secret-scan سراسری | همه‌ی repoها | ⬜ | `pre-commit` + `gitleaks` روی **همه** پروژه‌ها، نه فقط جاهایی که به آن فکر شده (درسِ #۹) |

## بستنِ حلقه
پس از انجامِ هر ردیف، وضعیت را 🟩 و تاریخ بزن. وقتی ۱–۴ سبز شد، این نوت را `status: done` کن و در `DecisionLog.md` ثبت شود.
