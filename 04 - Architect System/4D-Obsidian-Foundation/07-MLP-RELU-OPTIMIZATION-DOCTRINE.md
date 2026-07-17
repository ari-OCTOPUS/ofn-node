---
type: reference
status: ready
tags: [optimization, mlp, relu, numpy, performance, doctrine]
created: 2026-07-16
updated: 2026-07-16
parent: "[[04 - Architect System/4D-Obsidian-Foundation/06-LIVING-OPTIMIZED-SYSTEM-TARGET]]"
---

# MLP/ReLU Optimization Doctrine — خلاصه مهندسی برای سیستم زنده

> این سند بر اساس متن فنی ارسالی مالک درباره‌ی MLP/ReLU با NumPy ساخته شده است. هدف این نیست که همین کد فوراً وارد 4D شود؛ هدف این است که اصول آن به ستون بهینه‌سازی سیستم زنده تبدیل شود.

## 1. قانون مادر Performance

```text
هر عملیات سنگین باید batch-level، vectorized، measured و reproducible باشد.
Loop روی sampleها آخرین گزینه است، نه پیش‌فرض.
```

## 2. Dimension Contract

هر ماژول عددی باید قرارداد ابعاد داشته باشد:

```text
X: [B, d0]
W_l: [d_{l-1}, d_l]
b_l: [d_l]
Z_l/A_l: [B, d_l]
```

برای هر مدل یا pipeline آینده، ایجنت باید قبل از optimization بگوید:

- input shape چیست؟
- output shape چیست؟
- batch axis کدام است؟
- dtype چیست؟
- contiguous layout چیست؟
- bottleneck matrix operation کدام است؟

## 3. Numerical Stability Rules

- softmax باید stable باشد: subtract max per row.
- loss باید epsilon داشته باشد.
- normalization فقط از train set fit شود.
- float32 پیش‌فرض performance است، مگر دقت بالاتر لازم باشد.
- gradient norm باید ثبت و در صورت نیاز clip شود.
- ReLU dead-rate باید اندازه‌گیری شود.

## 4. Optimization Checklist

قبل از هر بهینه‌سازی:

```markdown
## Optimization Proposal
- Current implementation:
- Bottleneck evidence:
- Baseline metrics:
  - latency:
  - throughput:
  - memory:
  - accuracy/loss/quality:
- Delta:
- Preserved behavior:
- Risk class:
- Tests:
- Rollback:
```

بدون baseline، بهینه‌سازی فقط حدس است.

## 5. Metrics اجباری

| Metric | چرا مهم است |
|---|---|
| train/validation loss | تشخیص learning health |
| accuracy یا metric دامنه | کیفیت خروجی |
| epoch/run time | latency کل |
| samples/sec یا artifacts/sec | throughput |
| memory usage | محدودیت واقعی ماشین |
| gradient norm | stability |
| ReLU zero rates | dead ReLU |
| parameter count | complexity |
| MACs estimate | bottleneck نظری |
| cache/allocation count در صورت امکان | overhead پنهان |

## 6. System-Level Translation

| اصل MLP | ترجمه برای کل 4D/Obsidian |
|---|---|
| Batch processing | export و review به‌صورت batch bounded، نه tick-per-note |
| Matrix multiplication | عملیات تکراری به primitiveهای vectorized/compiled سپرده شود |
| He/Xavier init | هر subsystem با baseline سالم شروع شود، نه random config |
| L2 regularization | complexity و overfit عملیاتی کنترل شود |
| Gradient clipping | تغییرات self-improvement سقف داشته باشند |
| Dead ReLU monitoring | subsystem خاموش/بی‌اثر شناسایی شود |
| Early stopping | runهای بی‌فایده متوقف شوند |
| Low-rank factorization | bottleneckهای بزرگ با decomposition/summary کم‌هزینه شوند |
| BLAS threads | منابع ماشین قبل از runtime تنظیم و benchmark شوند |
| C-contiguous float32 | data layout و serialization هزینه پنهان نسازد |

## 7. Architecture Budget Formula

برای هر pipeline عددی یا مدل:

```text
Parameters = Σ(d_in*d_out + d_out)
Forward MACs ≈ B * Σ(d_in*d_out)
Training MACs ≈ 3B * Σ(d_in*d_out)
Weight memory float32 ≈ 4 * Parameters bytes
Momentum memory ≈ +1x parameters
Adam memory ≈ +2x parameters
```

برای سیستم کلی نیز مشابه فکر کن:

```text
Cost = data_size × transform_complexity × frequency
```

اگر هزینه زیاد شد:

- batch size را تنظیم کن؛
- frequency را کم کن؛
- summary layer بساز؛
- cached/replayable output استفاده کن؛
- مدل کوچک‌تر یا local-first انتخاب کن؛
- action را از live به shadow برگردان.

## 8. NumPy/CPU Rules

- `OMP_NUM_THREADS`، `MKL_NUM_THREADS` و `OPENBLAS_NUM_THREADS` قبل از import NumPy تنظیم شوند.
- تعداد thread با benchmark تعیین شود، نه حدس.
- `np.ascontiguousarray(..., dtype=np.float32)` برای ورودی‌های سنگین.
- از `@` و `np.dot` برای GEMM استفاده شود.
- gradientها و bufferها در صورت امکان preallocate شوند.
- in-place فقط وقتی مجاز است که مقدار قبلی لازم نیست.
- advanced indexing ممکن است copy بسازد؛ هزینه آن باید فهمیده شود.

## 9. Training Decision Rules

### Underfitting

اگر train و validation هر دو بد هستند:

- width/depth را افزایش بده؛
- L2 را کم کن؛
- epoch یا learning-rate schedule را تنظیم کن؛
- normalization را بررسی کن.

### Overfitting

اگر train خوب و validation بد است:

- width/depth را کم کن؛
- L2 را زیاد کن؛
- early stopping؛
- pruning یا low-rank؛
- داده/feature را بهتر کن.

### Dead ReLU

اگر `zero_rate > 0.9` پایدار است:

- learning rate را کم کن؛
- normalization را بررسی کن؛
- He init و bias کوچک مثبت؛
- در صورت نیاز LeakyReLU، اما با تست و benchmark.

## 10. Gradient Check Rule

هر backprop جدید باید روی مدل کوچک gradient check داشته باشد:

```text
g_num = (J(theta + eps) - J(theta - eps)) / (2 eps)
relative_error = |g_num - g_analytic| / max(1, |g_num|, |g_analytic|)
```

برای float32 حدود `1e-3` تا `1e-4` قابل قبول است؛ threshold دقیق باید با تست کوچک تعیین شود.

## 11. Integration با 4D

این دکترین فعلاً سه کاربرد دارد:

1. **اگر 4D یک مدل MLP/embedding/feature-classifier اضافه کرد:** همین قواعد پایه‌اند.
2. **اگر export bridge کند شد:** batch، vectorization، idempotency و profiling از همین‌جا می‌آید.
3. **اگر سیستم self-improvement پیشنهاد performance داد:** باید با این چک‌لیست اثبات شود.

## 12. Done Criteria برای هر optimization

یک optimization فقط وقتی قبول است که:

- metric قبل/بعد دارد؛
- کیفیت علمی/کارکردی افت نکرده یا افتش آگاهانه و پذیرفته‌شده است؛
- safety و provenance ضعیف نشده؛
- تست مثبت و منفی دارد؛
- rollback روشن دارد؛
- behavior قبلی یا نسخه قبلی حفظ شده؛
- owner برای actionهای حساس verdict داده است.

## 13. Prompt مخصوص Performance Agent

```text
You are the Performance & Numerical Optimization Agent. Use the MLP/ReLU NumPy doctrine as your engineering law. Your job is not to rewrite the system; it is to find measurable bottlenecks and propose small verified improvements. First establish shapes, dtypes, memory layout, parameter counts, MACs/cost estimates, batch sizes, runtime metrics, and safety boundaries. Then propose one optimization at a time. Do not weaken tests, guardrails, provenance, or human gates for speed. Any optimization without baseline metrics is invalid. If implementing code is approved, add tests first, keep old behavior/version, and provide rollback.
```
