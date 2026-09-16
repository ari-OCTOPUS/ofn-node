# Golden Traces — P2.d

> این فهرست توضیحی است. خودِ traceها از sessionهای واقعیِ shadow (پس از P1 arm) استخراج می‌شوند.

## روش

۱. پس از ۷ روز shadow (P1 gate سبز)، از `state/telegram/miniapp-hits.jsonl` و
   `collab-memory.jsonl` پنج بهترین و پنج بدترین تعامل را انتخاب کن.

۲. هر trace را به این شکل ذخیره کن (digest + route + outcome):

```json
{
  "trace_id": "golden-001",
  "classification": "best",
  "input_digest": "sha256:...",
  "route": {"tier": "local", "model": "qwen2.5:1.5b"},
  "outcome": "ok",
  "external_effect": false,
  "fallback_from": null,
  "note": "clean local answer for daily intent"
}
```

۳. نام فایل: `golden-{NNN}-{best|worst}.json`

۴. هیچ prompt/raw text در trace نیست — فقط digest.

## وضعیت

```text
BLOCKED: P1 arm هنوز انجام نشده — sessionهای واقعی موجود نیستند.
پس از ۷ روز shadow، این پوشه پر می‌شود.
```

## تست regression

پس از جمع‌آوری، یک تست script-native می‌سازد که با mock provider هر ۱۰ trace را
replay می‌کند و تأیید می‌کند که path پایدار است (همان tier، همان outcome).
