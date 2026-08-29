# Hybrid KV و Mamba Cache: طراحی روی کاغذ

## مسئله

مدل‌های hybrid ممکن است لایه‌های full attention، sliding-window/local attention و Mamba/SSM را با نیاز حافظهٔ متفاوت ترکیب کنند. یک block-size واحد روی همهٔ لایه‌ها، بدون grouping، می‌تواند padding و fragmentation پنهان بسازد.

`[DOCUMENTED] /opt/octopus/ofn-l4/docs/SCALE-AND-ACTIVE-INFERENCE.md:299-317`.

## طرح vLLM

- page size فیزیکی باید میان KV groupها uniform باشد.
- لایه‌هایی که تعداد block مشابه می‌خواهند group می‌شوند.
- full attention prefix scan از چپ به راست و در اولین miss متوقف می‌شود.
- sliding-window نیاز اخیر را نگه می‌دارد و rule hit متفاوت دارد.
- hybrid coordinator طول hit full-attention را با hit گروه دوم محدود می‌کند.
- key hybrid عملاً `(block_hash, group_id)` است.
- Mamba+full prefix behavior در سند «evolving» است و باید با version واقعی resolve شود.

`[DOCUMENTED] SCALE-AND-ACTIVE-INFERENCE.md:299-317`.

### استعارهٔ «انبار چندکالا»

A) **Vibe Coding:** یک انبار هم جعبه‌های استاندارد، هم قفسهٔ کشویی و هم مخزن پیوسته دارد؛ چیدن همه با یک قالب هدررفت می‌سازد.  
B) **ترجمهٔ مهندسی:** KV grouping برای attention typeهای مختلف با page-size مشترک و cache-key گروهی.  
C) **محدودیت:** Mamba state و KV page اندام یا حافظهٔ خودزندگی‌نامه‌ای نیستند؛ فقط state محاسبات inference هستند.

## آنچه محلی حاضر است

- توضیح معماری در سند OFN-L4.
- preflight fieldهای جدا برای full، sliding/local، Mamba SSM، group count، page size و padding overhead.
- estimator full-attention با limitations صریح.

`[LOCAL-SCAFFOLD] /opt/octopus/lab/artifacts/vllm-block-size/preflight.json:40-49؛ /opt/octopus/lab/ofn/benchmarks/vllm_block_size.py:152-201,732-745`.

## آنچه حاضر نیست

- فایل implementation با نام hybrid یا mamba در `/opt/octopus`
- مدل واقعی hybrid و architecture metadata
- vLLM same-version cache config
- GPU worker و profiler
- resolved group count/page size
- metric تجربی padding/group overhead
- test روی runtime vLLM

`[UNKNOWN/BLOCKED] recursive filename search zero؛ preflight fields null`.

بنابراین:

- `Hybrid KV Cache = DOCUMENT_ONLY`
- `Mamba Cache = DOCUMENT_ONLY`
- full-attention estimator = `OFFLINE_TESTED` اما تصمیم‌گیر نیست
- runtime = absent

## چرا block-size را از full attention تعمیم ندهیم؟

فرمول تقریبی:

```text
bytes_per_token ≈
  2 * layers * kv_heads * head_dim * bytes_per_element / TP
bytes_per_block ≈ block_size * bytes_per_token
```

این replication، metadata، GQA/MQA details، group padding، backend و state خاص Mamba را حذف می‌کند. `[LOCAL-CODE] vllm_block_size.py:160-201`.

پس candidate خوب برای full attention ممکن است در hybrid:

- page padding بیشتری بسازد؛
- group count را تغییر دهد؛
- hit length گروه دوم را محدود کند؛
- throughput/latency متفاوتی داشته باشد.

## پروتکل آینده

1. model architecture و attention type هر layer را از runtime همان نسخه resolve کن.
2. cache config، groupها، page size و block count را ثبت کن.
3. baseline auto را نگه دار.
4. W1–W5 cold/warm را اجرا کن.
5. memory/padding/APC/latency را برای هر group مشاهده کن.
6. اگر Mamba connector semantics version-dependent است، status را `UNKNOWN` نگه دار.
7. فقط با owner-approved canary و بدون production impact نتیجه بگیر.

تا قبل از این شواهد، «Hybrid/Mamba optimization» یک طرح مفهومی محلی است، نه feature فعال.

پاورقی مأموریت: [00_OWNER_ANSWER_FA.md#پاورقی-ماموریت](00_OWNER_ANSWER_FA.md#پاورقی-ماموریت).
