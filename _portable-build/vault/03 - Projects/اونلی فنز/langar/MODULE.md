# langar/ — کاکپیت تلگرامی Operator

> نقشهٔ ماژول · ۲۰۲۶-۰۸-۰۳

## نقش
کاکپیتِ تلگرامیِ آری (Operator). propose-only: تأیید/رد، DM management، fan admin، vault admin. لاگِ append-onlyِ تأییدهای انسانی (HITL).

## Entry points
| فایل | دستور | flag | نقش |
|---|---|---|---|
| `langar_bot.py` | `python langar/langar_bot.py` | (token-driven) | باتِ تلگرام |
| `run-langar.bat` | `.bat` | | بوتِ ویندوزی |
| `install-scheduled-task.ps1` | PowerShell | | نصبِ Windows Task |

## کتابخانه‌ها
`dm_admin` · `fan_admin` · `pf_admin` · `vault_admin` (همه admin modules)

## فایل‌های state
- `approvals.jsonl` — لاگِ تأییدهای انسانی (HITL، تولیدی، gitignored)
- `vault.json` — VaultBank state
- `reddit_state.json` — state اکتساب reddit
- `cost_meter.json` — مترِ هزینه
- `octopus.json` — config ارگانیسم

## Env vars
| کلید | نقش |
|---|---|
| `PF_AUDIT_FILE` | مسیرِ approvals.jsonl (تست) |
| `PF_AUDIT_ORIGIN` | `live` \| `test` مهرِ منشأ |

## وابستگی‌ها
- **درون‌پروژه‌ای**: `brain/*` (acquisition، dm_pipeline، dual_brain_v3، guards، audit، store، faq_engine)، `pf_os/*` (actuator، event_bus، telemetry، orchestrator)
- **خارجی**: telegram bot API (در live mode)

## توجه
`conftest.py` در ریشهٔ پروژه هر تست را به tmp می‌برد تا `approvals.jsonl` تولیدی آلوده نشود (درسِ ۲۰۲۶-۰۷-۲۵).

## تست‌ها
`test_dm_inbox_wiring` · `test_langar` · `test_pf_admin` + تست‌های سراسری
