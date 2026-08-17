---
type: knowledge
project: "[[03 - Projects/VibeGuard/PROJECT]]"
status: active
tags: [vibeguard, index]
created: 2026-08-17
updated: 2026-08-17
created_by: agent
sources:
  - "[[Project-Specification]]"
  - "[[Deep-Research-and-Architecture-Report]]"
---

# VibeGuard — از اینجا شروع کن

دو فایل سنگین در همین پوشه‌اند. این نوت فهرست است، نه کپی.

| اولویت | فایل | نقش |
|---|---|---|
| ۱ | [[Project-Specification]] | **SoT پیاده‌سازی.** اگر با گزارش تعارض داشت، spec برنده است مگر D1–D11 داسیهٔ گم‌شده. |
| ۲ | [[Deep-Research-and-Architecture-Report]] | شواهد، بازار، تهدید، ۸ گزینه معماری، roadmap. |
| ۳ | [[NEXT-AGENT]] | دستور ایجنت بعد (Claude Code / Cursor). |
| ۴ | `research/` | هفت داسیهٔ استناد اولیه — **هنوز وارد نشده**؛ ببین [[research/README]]. |

## تصمیم‌های قطعی (بحث مجدد ممنوع مگر مالک)

- هسته = Engine/CLI `vg` (Python 3.12، آفلاین). MCP / plugin / GitHub App فقط adapter.
- Skill تنها = رد (shell + `allowed-tools` سطح محصول امنیتی نیست).
- موتور قوانین = Opengrep (LGPL-2.1) + corpus خود؛ CodeQL CLI و قوانین Semgrep برای توزیع تجاری نه.
- Hooks تنها سطحی در Claude Code که tool call را رد می‌کند.
- Checks API فقط از GitHub App نوشتنی است.
- سه شکاف: auto-fix با تأیید اکسپلویت (~۲۶٪ مستقل در برابر ۷۶–۹۰٪ فروشنده) · نقص AI که SAST نمی‌بیند (۵۵٫۸٪ در برابر ۲٫۲٪) · پویش agent-hijack سطح مخزن (هیچ ابزار نگهداری‌شده).
- واژگان: کاهش ریسک، residual risk، confidence — نه «امن».

## نقشهٔ گزارش (۲۲ بخش)

۱ خلاصه · ۲ روش · ۳ چشم‌انداز GitHub · ۴ پروژه‌های برتر · ۵ ابزارها · ۶ امنیت coding agent · ۷ MCP · ۸ Threat Model · ۹ استانداردها · ۱۰ هشت گزینه · ۱۱ معماری پیشنهادی · ۱۲ استک · ۱۳ pipeline · ۱۴ لایه AI · ۱۵ Auto-Fix · ۱۶ Risk Engine · ۱۷ Agent Security · ۱۸ Benchmark · ۱۹ رقابت · ۲۰ شکاف بازار · ۲۱ MVP/V2/V3 · ۲۲ Roadmap.
