---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, session, worker-agent, directive, governance, life-currency, dual-brain]
created: 2026-08-16
updated: 2026-08-16
created_by: agent
sources:
  - "[[61-OBSIDIAN-NIGHT-LOCK-2026-08-16]]"
  - "[[../../04-SYSTEMS/AGENT-REPORT]]"
  - "[[../../04-SYSTEMS/DECISIONS-REGISTRY.yaml]]"
  - "[[../../04-SYSTEMS/AGENT-INVENTORY-2026-08-16]]"
---

# ۶۲ — اجرای دستورالعمل Worker Agent (فازهای ۰–۸)

جلسهٔ ZCode/GLM-5.3 روی `F:\backup`، پس از قفلِ [[61-OBSIDIAN-NIGHT-LOCK-2026-08-16|نوت ۶۱]]. مبنای کار: دستورالعملِ پیاده‌سازیِ مالک (مدلِ دستور: DeepSeek V4 Flash) با ۸ تصمیمِ نهایی (D1–D8). گزارشِ کامل: [[../../04-SYSTEMS/AGENT-REPORT|AGENT-REPORT]].

## یک پاراگراف

۹ کامیتِ `agent-checkpoint` (فازهای ۰–۸ + گزارش) با ۷۱ تستِ سبزِ نو، بدون restart ارگانیسم و با stage صریح در هر کامیت. سه سندِ ۰۴-SYSTEMS (دو-مغزی/ارز-حیات/رودمپ) که صبح ساخته شده بودند، به کد وصل شدند: DECISIONS-REGISTRY (ماشین‌خوان) · spine (از قبل زنده بود — فقط تستِ تأیید) · HEARTSTATE audit fix + OFF-heartbeat هر ۱۰ ضربان · life-currency سه‌بعدی + مبادلهٔ آزاد D4 · روترِ provider با کاهشِ پله‌ای D5/D6 · وتوی دوگانهٔ D2/D3 با ثبتِ canonical در spine · W1 فقط‌خواندن 4d با allowlist · سیم‌کشی synapse/chord و دو گیتِ محدودکننده در action-bridge. **A2 خودکار مسلح نشد** — تعارضِ دستورالعمل با رأیِ ثبت‌شدهٔ VQ-SELFGOAL-002 به مالک سپرده شد.

## سه انحرافِ مهمِ طرح→واقعیت (R7)

| فرضِ دستورالعمل | واقعیتِ اندازه‌گیری‌شده | تصمیم |
|---|---|---|
| spine/intel_spine/one-heartbeat خاموش‌اند | هر سه **از قبل در env هر ۵ پروسه روشن**؛ spine.db زنده با ۴۷۷۰ رویداد | تستِ تأیید + صفر initِ جدید (R10 تک‌نویسنده) |
| فلگ‌ها در `.env` | `.env` زیر `.agentignore` ممنوع است | ۶ رأیِ tracked در `owner-verdicts.yaml` (env برنده می‌ماند) |
| ادغامِ وتو در supervisor.py | supervisor منشورِ فقط‌خواندن دارد (تست‌دار) | وتو در مسیرِ واقعیِ اجرا (action_bridge، فاز ۸e) |

## کارِ تحویل‌شده بر اساس فاز

| فاز | commit | یک‌خطی |
|---|---|---|
| ۰ | `c7915e5` | AGENT-INVENTORY (اندازه‌گیری مستقیم) + plan |
| ۱ | `f7e9d84` | DECISIONS-REGISTRY.yaml — D1..D8 |
| ۲ | `3ccf01f` | تستِ spine-wired 5/5 + رویدادِ تولید `evt_638fc31543eb95c4` |
| ۳ | `1f4d942` | `activation_flags` در flags-loaded (باگِ HEARTSTATE بسته) + `off_heartbeat` |
| ۴ | `0fc7df2` | `life_currency.py` + `budget_transfer.py` (۱۱ عضو، رزرو ۲۰٪، سقف ۲×) |
| ۵ | `3520bd9` | `provider_adapter.py` — D5 زنجیره + D6 کاهش A2→propose |
| ۶ | `22bb962` | `dual_brain.py` + `dual_veto_recorded` در spine (canonical) |
| ۷ | `16f614c` | `fourd_access.py` — W1 فقط‌خواندن، allowlist بسته، اثباتِ AST |
| ۸ | `81537a8` | 8a/8b از قبل وصل (تأیید) · 8c مسلح · 8d سایهٔ chord · 8e دو گیتِ محدودکننده |
| گزارش | `cc0a45c` | [[../../04-SYSTEMS/AGENT-REPORT|AGENT-REPORT]] |

## سؤال‌های بازِ مالک (توقفِ عمدی طبقِ §۷ دستورالعمل)

1. **A2**: D7 می‌گوید auto ولی VQ-SELFGOAL-002 می‌گوید BLOCK — A2 مسلح نشد؛ فقط گیت‌های محدودکننده (fallback→propose + وتو) وصل شد. رأیِ نهایی؟
2. **Restart**: اثرهای فاز ۳/۴/۵/۸ (OFF-heartbeat، تخصیصِ life-currency، tickِ روتر، chord) از restart بعدی زنده می‌شوند. چه زمانی؟
3. **پایشِ ۱ هفته‌ای** synapse (۸c) و chord (۸d) از restart شروع می‌شود (roadmap §۳).

## نکته‌های عملیاتی

- **ایجنتِ موازی**: در همین پنجره EQUIP G5/G9/G10 کامیت می‌زد و شاخه را g5→g9→g10 برد؛ کامیت‌های این جلسه سالم روی `equip/g10-cognition-20260816` نشسته‌اند.
- فایل‌های جدیدِ کلیدی: `_ops/off_heartbeat.py` · `_ops/heart/life_currency.py` · `_ops/heart/budget_transfer.py` · `_ops/cortex/provider_adapter.py` · `_ops/control_plane/dual_brain.py` · `_ops/fourd_access.py` · ۷ فایلِ تست در `_ops/tests/`.
- فلگ‌های ثبت‌شده (رأیِ tracked): `OCTOPUS_WIRE_LIFE_CURRENCY` · `OCTOPUS_WIRE_PROVIDER_ROUTER` · `OCTOPUS_WIRE_DUAL_VETO` · `FOURD_DATA_ACCESS` · `OCTOPUS_SYNAPSE_ENABLED` · `OCTOPUS_WIRE_CHORD` — همه با env-override.
- نقطهٔ ورودِ بعدی: [[../../04-SYSTEMS/AGENT-REPORT|AGENT-REPORT]] §Owner Questions.
