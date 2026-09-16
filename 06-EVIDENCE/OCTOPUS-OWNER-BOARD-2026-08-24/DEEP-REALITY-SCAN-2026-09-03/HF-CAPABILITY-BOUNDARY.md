# HF-CAPABILITY-BOUNDARY — 2026-09-03 (فقط PROPOSAL؛ بدون هیچ تماس خارجی)

**واقعیت پایه (grep امروز):** صفر ارجاع به huggingface/transformers/hf_hub در ofn/، _ops/، 4d brain → هیچ integration موجود نیست؛ هیچ credential HF روی هیچ نود دیده نشد. همهٔ موارد زیر از صفر شروع می‌شوند و status: PROPOSAL_ONLY.

```yaml
capability: log/event triage
hf_asset: مدل‌های سبک classifier (مثلاً distilbert-family) — انتخاب در فاز research
input_data_classification: internal-logs-redacted (بدون مشتری/ایمیل/مبلغ)
may_leave_local_network: false (فقط inference لوکال یا پس از redact دو-مرحله‌ای)
tool_permissions: none
cost_limit: $0 (لوکال) · سقف API در صورت رأی
latency_limit: offline batch
evaluation_metric: توافق با برچسب دستی روی ۵۰ نمونهٔ redact‌شده
failure_mode: برچسب غلط بی‌صدا → همیشه خروجی با confidence + نمونه برای بازبینی
rollback: حذف ماژول (additive)
human_gate: رأی مالک برای هر خروج داده + انتخاب مدل
recommended_phase: research
status: PROPOSAL_ONLY
```

```yaml
capability: Obsidian embedding/RAG جست‌وجو
hf_asset: embedding چندزبانهٔ لوکال (bge-m3/E5-family)
input_data_classification: vault-markdown (شامل دادهٔ عملیاتی → فقط لوکال)
may_leave_local_network: false — مطلق
tool_permissions: read-only vault index
cost_limit: $0 (CPU inference)
evaluation_metric: recall@10 روی ۲۰ پرسش معیار داخلی
failure_mode: بازیابی گمراه‌کننده → همیشه pointer به فایل اصلی نمایش داده شود
rollback: حذف ایندکس
human_gate: تایید فهرست فایل‌های مجاز به ایندکس
recommended_phase: sandbox
status: PROPOSAL_ONLY
```

```yaml
capability: eval dataset برای پیشنهادهای agent (doctor/learning)
hf_asset: دیتاست خصوصیِ ساخته‌شده از تست‌های عمومی + سناریوهای ساختگی (هیچ دادهٔ واقعی)
may_leave_local_network: true فقط اگر ۱۰۰٪ synthetic — و با رأی مالک
tool_permissions: none
evaluation_metric: نرخ رد صحیح پیشنهادهای بد (falsifier-pass)
recommended_phase: research
status: PROPOSAL_ONLY
```

```yaml
capability: Space/MCP ابزار غیرحساس (مثلاً فرمت‌کنندهٔ CSV عمومی)
input_data_classification: public-synthetic only
may_leave_local_network: true (فایل synthetic)
human_gate: مالک؛ kill = عدم استفاده (بدون state)
recommended_phase: internal_readonly
status: PROPOSAL_ONLY
```

**ممنوعِ همیشگی:** دادهٔ مشتری/ایمیل/لجر/کلید به HF؛ دسترسی write گیت‌هاب/SSH/DB به مدل؛ مدل به‌عنوان مرجع حقیقت یا مجوز.
**ترتیب پیشنهادی:** RAG لوکال (بیشترین بازده، صفر خروج داده) → eval dataset synthetic → log triage لوکال → Space.
