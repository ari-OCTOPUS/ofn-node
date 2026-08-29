# vLLM KV Block Size: برنامهٔ اندازه‌گیری، نه برنده

## block چیست؟

vLLM tokenهای KV را در blockهای منطقی تخصیص می‌دهد. برای طول `L` و block size `b`:

```text
allocated = ceil(L / b) * b
tail_waste = allocated - L
fragmentation = sum(tail_waste) / sum(allocated)
```

`[LOCAL-CODE] /opt/octopus/lab/ofn/benchmarks/vllm_block_size.py:48-106؛ /opt/octopus/lab/docs/adr/ADR-VLLM-KV-BLOCK-SIZE.md:39-68`.

block کوچک‌تر همیشه برای هر `L` waste کمتری از هر block بزرگ‌تر ندارد؛ guarantee فقط وقتی small مقسوم‌علیه large باشد تعریف شده است. estimator تئوریک metadata، hybrid grouping، replication و page padding را پوشش نمی‌دهد. `[LOCAL-CODE] vllm_block_size.py:109-201`.

### استعارهٔ «جعبهٔ کانتینر»

A) **Vibe Coding:** tokenها در جعبه‌های اندازه‌ثابت چیده می‌شوند؛ جعبهٔ خیلی بزرگ فضای خالی و جعبهٔ خیلی کوچک overhead دارد.  
B) **ترجمهٔ مهندسی:** trade-off میان fragmentation، allocator/scheduler overhead، throughput و cache reuse.  
C) **محدودیت:** این جعبه‌ها حافظهٔ episodic یا container واقعی نیستند؛ «اندازهٔ بهتر» فقط با workload/GPU/version مشخص معنا دارد.

## baseline و candidate

- platform auto باید baseline باشد؛ flag block-size حذف می‌شود.
- candidate فقط از capability evidence همان version/backend می‌آید.
- برای CUDA، intersection پیشنهادی `8,16,32` است؛ بالاتر از 32 تولید نمی‌شود.
- size 1 فقط diagnostic و owner-opt-in است.
- هر candidate process/cache/data path جدا و fresh می‌خواهد.

`[LOCAL-CODE] vllm_block_size.py:205-333,336-455`.

## W1–W5

- W1 Short Interactive: latency-sensitive، prefix sharing کم.
- W2 Multi-turn Agent: history طولانی‌تر، sharing بالا.
- W3 Long Document QA: سند ثابت بزرگ + query tail.
- W4 Mixed Production Trace: **blocked** تا histogram ناشناس مالک؛ distribution حدس زده نمی‌شود.
- W5 Long Generation Control: decode-heavy برای نشان‌دادن جایی که APC/block کمک نمی‌کند.

هر workload cold و warm جدا دارد و artifact فقط length/prefix-pattern synthetic نگه می‌دارد؛ raw prompt، token ID، secret، endpoint و tenant identity ندارد. `[LOCAL-CODE] /opt/octopus/lab/ofn/benchmarks/workload_manifest.py:1-31,136-207,424-496`.

## metric و result store

metrics parser caller-supplied text را بدون HTTP client parse و labelهای حساس را redact می‌کند. semantics لازم شامل TTFT، TPOT، ITL، E2E، queue، prefill/decode، throughput، APC hit/query، KV usage، preemption و waiting است. `[LOCAL-CODE] /opt/octopus/lab/ofn/adapters/vllm_metrics.py:1-5,32-66,278-346`.

result CSV schema برای safety و performance تعریف شده؛ Pareto:

- TTFT/E2E/preemption/fragmentation/queue/memory را minimize
- throughput/APC hit را maximize
- حداقل سه repetition
- confidence interval و حداقل ۵٪ improvement
- fragmentation تئوریک به‌تنهایی winner انتخاب نمی‌کند

`[LOCAL-CODE] /opt/octopus/lab/ofn/benchmarks/result_store.py:13-69,348-388,503-670`.

## owner gate و abort

canary authorization بدون این‌ها fail می‌شود:

- explicit owner approval
- reference غیرحساس
- owner thermal limit
- metrics available
- non-production endpoint

abort conditionها شامل OOM، reset/Xid، crash loop، error rate بالاتر از ۱٪، thermal limit، host memory/disk critical، production impact، دو metric failure متوالی و identity/safety failure هستند. `[LOCAL-CODE] vllm_block_size.py:498-597`.

## شواهد دقیق فاز آفلاین

- ۵۱ test جدید harness در execution record محلی پاس شده‌اند؛ failure/skip صفر. `[LOCAL-OFFLINE-LAB] local execution record /root/.cursor/projects/root/agent-transcripts/ccec7392-b4a7-42f7-97c0-b400b637236e/subagents/2477326a-b3ed-4651-8a24-ec821041cb69.jsonl:73-78؛ شش test module در /opt/octopus/lab/ofn/organism/tests/test_vllm_*`.
- baseline prefix suite: ۳ pass و ۱ skip cbor2. `[LOCAL-OFFLINE-LAB] همان execution record:75-78`.
- preflight: no vLLM، no NVIDIA/ROCm compute device، generic DRI/NPU کافی نیست. `[BLOCKED] /opt/octopus/lab/artifacts/vllm-block-size/preflight.json:15-29,67-93`.
- GPU benchmark اجرا نشده. `results.csv` فقط header دارد. `[LOCAL-OFFLINE-LAB] pareto-report.md:1-14؛ results.csv:1`.
- Pareto frontier محاسبه نشده؛ winner وجود ندارد. `[LOCAL-OFFLINE-LAB] pareto-report.md:3-9`.
- selected profile `none` و selected block size `unknown`. `[LOCAL-OFFLINE-LAB] recommendation.md:1-10`.
- canary اجرا نشده؛ deployment انجام نشده. `[LOCAL-OFFLINE-LAB] ADR-VLLM-KV-BLOCK-SIZE.md:150-158`.

نتیجهٔ مجاز و دقیق: `BLOCKED_NO_GPU`.

## چرا RKNPU کافی نیست؟

برد DRM nodeهای Rockchip display و RKNPU دارد، اما preflight فقط CUDA/ROCm را vLLM-compatible می‌شناسد؛ vLLM package، CUDA، ROCm و torch نیز present نیستند. بنابراین `GPU_PRESENT=false_for_vLLM`، نه این‌که silicon accelerator مطلقاً وجود ندارد. `[RUNTIME-VERIFIED] /sys/class/drm/*/device/uevent؛ package/tool snapshot`.

## مرحلهٔ بعد فقط با تأیید مالک

GPU host evidence، version/backend/model config، W4 histogram ناشناس، metric completeness، thermal limit و canary reference لازم‌اند. حتی در آن صورت harness فقط می‌تواند `READY_FOR_OWNER_APPROVED_CANARY` بدهد، نه deployment خودکار.

Hybrid/Mamba در [12_HYBRID_MAMBA_CACHE_FA.md](12_HYBRID_MAMBA_CACHE_FA.md) است.

پاورقی مأموریت: [00_OWNER_ANSWER_FA.md#پاورقی-ماموریت](00_OWNER_ANSWER_FA.md#پاورقی-ماموریت).
