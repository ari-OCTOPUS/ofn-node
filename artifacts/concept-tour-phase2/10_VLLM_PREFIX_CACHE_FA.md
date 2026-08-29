# vLLM Prefix Cache و APC

## مفهوم

Automatic Prefix Caching محاسبات KV مربوط به blockهای کامل prefix مشترک را reuse می‌کند. hash هر block از parent hash، token block و extraهایی مانند model/revision/LoRA/cache salt ساخته می‌شود. آخرین block ناقص reuse کامل ندارد. `[DOCUMENTED] /opt/octopus/ofn-l4/docs/SCALE-AND-ACTIVE-INFERENCE.md:238-297`.

stable prefix یعنی بخش invariant درخواست—مانند system contract یا سند ثابت—قبل از tail متغیر قرار گیرد تا blockهای کامل بیشتری مشترک شوند. تغییر کوچک در prefix اولیه chain hash بعدی را نیز تغییر می‌دهد.

### استعارهٔ «قفسهٔ محاسبه»

A) **Vibe Coding:** جمله‌های آغازین یکسان یک‌بار روی قفسه آماده می‌شوند و درخواست بعدی از همان قفسه برمی‌دارد.  
B) **ترجمهٔ مهندسی:** reuse blockهای کامل KV بر پایهٔ hash chain prefix.  
C) **محدودیت:** KV cache خاطره، دانش پایدار یا هویت نیست؛ با eviction/process loss از بین می‌رود.

## پیاده‌سازی آفلاین محلی

`vllm_prefix_cache.py` دو mode را مدل می‌کند:

- `sha256`: Python pickle serialization، سریع‌تر/محلی ولی cross-language canonical نیست.
- `sha256_cbor`: canonical CBOR و reproducibility بهتر، نیازمند `cbor2`.

`[LOCAL-CODE] /opt/octopus/lab/ofn/adapters/vllm_prefix_cache.py:24-30,119-149,323-359`.

extra hash شامل model ID، tokenizer ID، revision، LoRA و در حالت امن `cache_salt` است. `[LOCAL-CODE] vllm_prefix_cache.py:152-161`.

## cache salt و tenant isolation

بدون salt، tenantهایی با prefix یکسان می‌توانند hash مشترک داشته باشند و timing side channel یا cross-tenant reuse ایجاد کنند. با salt متفاوت، فضای hash جدا می‌شود. `[LOCAL-CODE] vllm_prefix_cache.py:251-280`.

artifact آفلاین:

- بدون salt: overlap ratio `1.0`
- با salt: overlap ratio `0.0`
- collision probe: `0/5000`

این فقط workload synthetic کوچک است و security proof یا probability صفر collision نیست. `[LOCAL-OFFLINE-LAB] /opt/octopus/lab/artifacts/prefix-cache/benchmark-report.json:4-44`.

## شواهد دقیق

- `sha256`: status `OK`، benchmark آفلاین اجرا شده. `[LOCAL-OFFLINE-LAB] benchmark-report.md:20-29`.
- `sha256_cbor`: `UNAVAILABLE` چون `cbor2_not_installed`. `[BLOCKED_DEPENDENCY] benchmark-report.md:31-34`.
- test baseline موجود: ۴ test اجرا، ۳ pass و ۱ skip اختیاری برای cbor2. `[LOCAL-OFFLINE-LAB] existing local execution record؛ /opt/octopus/lab/ofn/organism/tests/test_vllm_prefix_cache.py`.
- این مأموریت package نصب نکرد و benchmark را دوباره اجرا نکرد.

پس:

- Prefix Caching: `OFFLINE_TESTED`
- Cache Salt: `OFFLINE_TESTED`
- sha256_cbor: `BLOCKED_DEPENDENCY`
- vLLM runtime/APC واقعی: present نیست

## جداسازی از Event Store

```text
APC/KV:
  source = tokenized prefix
  lifetime = engine/cache eviction
  reader/writer = inference engine
  truth = performance optimization only

Event Store:
  source = validated domain event
  lifetime = SQLite persistence
  reader/writer = EventKernel/replay/memory
  truth = organism event provenance
```

استفاده از hash در هر دو، آن‌ها را یک سامانه نمی‌کند.

## برای اجرای واقعی چه لازم است؟

1. GPU host و vLLM version واقعی.
2. hash algorithm support همان نسخه.
3. tenant-specific secret-derived salt بدون log.
4. stable-prefix contract و tokenizer/model revision pin.
5. metricهای hit/query/latency.
6. canary و owner approval.

ADR محلی می‌گوید core patch نشود، salt multi-tenant الزامی باشد و انتخاب با داده انجام شود. `[DOCUMENTED] /opt/octopus/lab/docs/adr/ADR-VLLM-PREFIX-CACHING.md:15-44`.

block-size در [11_VLLM_BLOCK_SIZE_FA.md](11_VLLM_BLOCK_SIZE_FA.md) و Hybrid/Mamba در [12_HYBRID_MAMBA_CACHE_FA.md](12_HYBRID_MAMBA_CACHE_FA.md).

پاورقی مأموریت: [00_OWNER_ANSWER_FA.md#پاورقی-ماموریت](00_OWNER_ANSWER_FA.md#پاورقی-ماموریت).
