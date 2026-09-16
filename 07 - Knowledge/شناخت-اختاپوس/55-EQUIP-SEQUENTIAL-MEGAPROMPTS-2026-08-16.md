---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, megaprompt, equip, sequential]
created: 2026-08-16
updated: 2026-08-16
created_by: agent
sources:
  - "https://blog.modelcontextprotocol.io/posts/2026-07-28/"
  - "https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.0.0"
  - "https://github.com/langchain-ai/langgraph/releases/tag/1.2.11"
  - "https://github.com/temporalio/temporal/releases/tag/v1.31.2"
  - "https://github.com/open-telemetry/semantic-conventions/releases/tag/v1.42.0"
  - "https://datatracker.ietf.org/doc/draft-klrc-aiagent-auth/"
  - "https://huggingface.co/papers/2608.01964"
  - "https://github.com/vaaraio/vaara"
  - "[[54-GROK-SESSION-SOT-2026-08-16]]"
  - "[[../../agent-prompts/MEGAPROMPT-EQUIP-00-SHARED-CONTRACT-2026-08-16]]"
---

# ۵۵ — مگاپرامپت‌های ترتیبی تجهیز Octopus

اگر می‌خواهی ۱۰ ایجنت قابلیت اضافه کنند، هم‌زمان نده. لانچر:
[[../../00 - Inbox/2026-08-16 MEGAPROMPT — Equip Octopus Sequential|لانچر Inbox]].

## خلاصه یک‌پاراگرافی

برنامهٔ EQUIP ده گروه پیاده‌سازی است به‌ترتیب ۲→۶→۷→۸→۱→۳→۴→۵→۹→۱۰، با اسکن
مستقل بعد از هر دو گروه. قرارداد پایه + مگادیتای تکنولوژی داخل همان فایل‌های
`agent-prompts/MEGAPROMPT-EQUIP-*` است. قدرت از ابزار بیشتر نیست؛ از بستن حلقهٔ
read→reason→act→verify با حداقل دسترسی، اجرای پایدار، حافظهٔ قابل‌اعتماد،
مشاهده‌پذیری و تأیید انسانی است.

## ترتیب و فایل‌ها

| # | گروه | فایل |
|---|---|---|
| 0 | قرارداد مشترک | `MEGAPROMPT-EQUIP-00-SHARED-CONTRACT-2026-08-16.md` |
| 1 | حافظه | `MEGAPROMPT-EQUIP-01-G2-MEMORY-2026-08-16.md` |
| 2 | مشاهده‌پذیری | `MEGAPROMPT-EQUIP-02-G6-OBSERVABILITY-2026-08-16.md` |
| 3 | هویت | `MEGAPROMPT-EQUIP-03-G7-IDENTITY-2026-08-16.md` |
| 4 | کنترل آسیب | `MEGAPROMPT-EQUIP-04-G8-CONTAINMENT-2026-08-16.md` |
| 5 | ارکستراسیون | `MEGAPROMPT-EQUIP-05-G1-ORCHESTRATION-2026-08-16.md` |
| 6 | ادراک | `MEGAPROMPT-EQUIP-06-G3-PERCEPTION-2026-08-16.md` |
| 7 | کدنویسی امن | `MEGAPROMPT-EQUIP-07-G4-CODING-2026-08-16.md` |
| 8 | زیرساخت | `MEGAPROMPT-EQUIP-08-G5-INFRA-2026-08-16.md` |
| 9 | اتصالات شخصی | `MEGAPROMPT-EQUIP-09-G9-CONNECTORS-2026-08-16.md` |
| 10 | شناخت / self-model | `MEGAPROMPT-EQUIP-10-G10-COGNITION-2026-08-16.md` |
| scan | بعد از هر موج | `MEGAPROMPT-EQUIP-SCAN-INDEPENDENT-2026-08-16.md` |

## تصحیح ADR و MCP

- ADR-012 این vault = memory-policy؛ ADR-013 = causal-selfmodel (REJECTED).
- MCP زنده = `_ops/octopus_mcp/server.py` stdio بدون SDK.
- spec MCP `2026-07-28` + python-sdk `v2.0.0` گزینهٔ مهاجرت است نه واقعیت فعلی.
- OTel GenAI پس از v1.42.0 به repo جدا رفت و هنوز Development است.

## قانون طلایی ابزار

Typed I/O · least privilege · timeout · retry limit · idempotency · budget ·
audit · confidence · approval · rollback · kill-switch. یکی کم = اضافه نکن.

## نتایج اجرا (همان روز — ۲۰۲۶-۰۸-۱۶)

برنامه کامل اجرا شد: ۵ موج A–E، هر ۱۰ گروه + ۵ اسکن مستقل، هیچ FAIL،
verdict نهایی **CONDITIONAL PASS** (۷۵۳ تست سبز راستی‌آزمایی‌شده، صفر
dependency جدید). master دست‌نخورده (`8b7e6e8`)؛ کل خروجی روی زنجیرهٔ
شاخه‌های `equip/*` در انتظار رأی merge. جزئیات و لجر یافته‌ها:
[[64-EQUIP-EXECUTION-RESULTS-2026-08-16|نوت ۶۴]] ·
[[../../06-EVIDENCE/OCTOPUS_FINAL_SCAN_REPORT|گزارش اسکن نهایی]].
