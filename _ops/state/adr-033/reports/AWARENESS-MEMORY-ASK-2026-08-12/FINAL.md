# AWARENESS-MEMORY-ASK — FINAL (2026-08-12)

## Baseline → After

| item | before | after |
|------|--------|-------|
| `_self_context` | organism+truth+blockers | + دو مغز + 4d note + حافظه cite |
| `data.facts` | غالباً absent | collaborator پر می‌کند (cite-only) |
| `/api/ask` vault miss | escalate بی‌صدا | `vault_empty` / `vault_flag` صادق |
| selfmap in chat | نه | intent `selfmap` / «نقشه خودت» |
| ingest→cite | شکاف | improve 395→403 lines → collab facts_n=3 |

## پیاده‌سازی

| فایل | رفتار |
|------|--------|
| `_ops/memory/owner_recall.py` | `recall_for_owner_ask` fail-soft |
| `collab_model_adapter._self_context` | brains + memory block |
| `conversation.py` | intro witness + selfmap intent |
| `collaborator.py` | `data.facts` + خط شاهد |
| `miniapp_gateway.py` | vault_empty meta |
| tests | awareness 6/6 · memory_ask 6/6 · gateway vault_empty+403 |

## AC

- [x] AC-Ask-SelfAware — intro با cortex/business_brain + witness
- [x] AC-Ask-MemoryCite — facts از self-loop مسیر واقعی
- [x] AC-Ask-VaultTruth — vault_empty در پاسخ
- [x] AC-Collab-NoHang — timeouts قبلی حفظ
- [x] AC-Auth-FailClosed — unauth 403
- [x] AC-Selfmap-Visible — intent + API موجود
- [x] AC-Ingest-RoundTrip — 395→403 سپس cite
- [x] AC-NoAuthorityCreep — may_authorize=false

## دستور مالک

1. مینی‌اپ را کامل ببند  
2. دوباره باز کن  
3. پرسش → همکار → سه سؤال جدول 07  
4. Ask → یک سؤال vault  
5. System/selfmap را نگاه کن  

## تست‌های نو (ثبت در run_all — WORKLOCK)

- `test_awareness_ask_bridge.py`
- `test_memory_ask_recall.py`
- گسترش `test_miniapp_gateway.py` (vault_empty + unauth)
