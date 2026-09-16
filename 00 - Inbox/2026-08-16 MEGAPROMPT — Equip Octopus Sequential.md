---
type: knowledge
status: inbox
updated: 2026-08-16
created: 2026-08-16
created_by: agent
tags: [octopus, megaprompt, equip, sequential]
sources:
  - "[[../agent-prompts/MEGAPROMPT-EQUIP-00-SHARED-CONTRACT-2026-08-16]]"
  - "[[../07 - Knowledge/شناخت-اختاپوس/54-GROK-SESSION-SOT-2026-08-16]]"
---

# لانچر — EQUIP ترتیبی Octopus (۱۰ گروه + اسکن)

به ایجنت‌ها **ترتیبی** بده، نه هم‌زمان. هر پیام = قرارداد پایه + یک گروه.

نسخهٔ کامل قرارداد: `agent-prompts/MEGAPROMPT-EQUIP-00-SHARED-CONTRACT-2026-08-16.md`

## چرا این ترتیب

حافظهٔ write-without-read قبلاً C-012 فاز صفر گرفته؛ هنوز provenance/Write Gate
و دیدپذیری کم است. اول حلقهٔ read→reason→act→verify، بعد مرز امنیتی، بعد قابلیت نو.

| موج | بده به ایجنت | فایل | بعدش |
|---|---|---|---|
| A1 | پیاده‌ساز ۱ | `MEGAPROMPT-EQUIP-01-G2-MEMORY-2026-08-16.md` | صبر تا شواهد |
| A2 | پیاده‌ساز ۲ | `MEGAPROMPT-EQUIP-02-G6-OBSERVABILITY-2026-08-16.md` | اسکن A |
| A scan | **ایجنت دیگر** | `MEGAPROMPT-EQUIP-SCAN-INDEPENDENT-2026-08-16.md` + بگو Wave A | اگر FAIL نرو جلو |
| B1 | پیاده‌ساز ۳ | `MEGAPROMPT-EQUIP-03-G7-IDENTITY-2026-08-16.md` | |
| B2 | پیاده‌ساز ۴ | `MEGAPROMPT-EQUIP-04-G8-CONTAINMENT-2026-08-16.md` | اسکن B |
| C1 | پیاده‌ساز ۵ | `MEGAPROMPT-EQUIP-05-G1-ORCHESTRATION-2026-08-16.md` | |
| C2 | پیاده‌ساز ۶ | `MEGAPROMPT-EQUIP-06-G3-PERCEPTION-2026-08-16.md` | اسکن C |
| D1 | پیاده‌ساز ۷ | `MEGAPROMPT-EQUIP-07-G4-CODING-2026-08-16.md` | |
| D2 | پیاده‌ساز ۸ | `MEGAPROMPT-EQUIP-08-G5-INFRA-2026-08-16.md` | اسکن D |
| E1 | پیاده‌ساز ۹ | `MEGAPROMPT-EQUIP-09-G9-CONNECTORS-2026-08-16.md` | |
| E2 | پیاده‌ساز ۱۰ | `MEGAPROMPT-EQUIP-10-G10-COGNITION-2026-08-16.md` | اسکن E نهایی |

## طرز پیست هر ایجنت

```
[کل فایل SHARED]
[کل فایل گروه]
```

برای اسکن:

```
[کل فایل SHARED]
[کل فایل SCAN]
موج: A   (یا B/C/D/E)
baseline SHA: <از git rev-parse HEAD قبل از آن موج>
```

اجازه نده روی master بنویسد. خروجی هر مرحله: branch + گزارش `06-EVIDENCE/EQUIP-*` + تست + rollback. merge فقط بعد از اسکن همان موج و رأی تو.

## تصحیح مهم (در SHARED هم هست)

در این vault **ADR-012 = memory-policy** و **ADR-013 = causal-selfmodel**.
sandbox/kill را از ADR-039 و PolicyGate/`halted`/STOP/`kill.switch` کشف کنند.
MCP فعلی SDK v2 نیست؛ `_ops/octopus_mcp/server.py` stdio دست‌ساز است.

## تحقیق کنار هر پرامپت

مگادیتای هر گروه داخل همان فایل است (بخش TECHNOLOGY OPTIONS)، تحقیق‌شده
2026-08-16 از صفحات عمومی GitHub/HF/IETF/OTel. کانکتور MCP گیت‌هاب/HF در
آن نشست Cursor در کاتالوگ نبود؛ HealthKit/Finance ابزار پژوهشی معماری نیستند.

هیچ ابزاری را کورکورانه نصب نکنند. اول discovery، فقط gap.

نوت ماندگار: [[../07 - Knowledge/شناخت-اختاپوس/55-EQUIP-SEQUENTIAL-MEGAPROMPTS-2026-08-16|نوت ۵۵]]
