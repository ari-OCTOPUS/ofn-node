---
type: knowledge
project: "[[04 - Architect System/architect/PROJECT]]"
status: spec
tags: [octopus, deepseek, load-testing, rate-limit, backoff, concurrency, user_id, failover]
created: 2026-08-20
updated: 2026-08-20
created_by: agent
sources:
  - "[[../../02-DECISIONS/DEEPSEEK-AUTOMATIC-ROUTING-01-2026-08-19]]"
  - "[[../../00 - Inbox/2026-08-20 LLM-ARM-VS-JUDGE + VLLM-OPERATIONS]]"
  - "[[../../06-EVIDENCE/HC-WM-MC-WAVE0-2026-08-20/CONTRACTS]]"
---

# ۶۸ — چک‌لیست عملیاتی و مستند فنی تست بار `deepseek-v4-flash` (2026-08-20)

> **وضعیت: SPEC.** این سند قبل از هر اجرای واقعی نوشته شده است. هیچ عددی در آن
> ادعای اندازه‌گیری نیست. هر عدد پارامتر پیش‌فرضِ قابل‌تغییر است تا مالک سقف‌ها را
> ببندد. اجرای تست بار مصرفِ پول دارد → پیش‌فرض `dry_run=True`.

## ۰. قواعد غیرقابل‌نقض (وارث از DEEPSEEK-AUTOMATIC-ROUTING-01)

[FACT] این قواعد از تصمیم مالک ۲۰۲۶-۰۸-۱۹ می‌آیند و تست بار آن‌ها را بدون\Exception لغو نمی‌کند:

1. کلید فقط از env/secret file خوانده می‌شود. در لاگ، receipt، آرتیفکت تست، گزارش
   یا git نمی‌آید. تأیید فقط به‌شکل `DEEPSEEK_KEY_PRESENT=true|false`.
2. هیچ fake success. هر بلاک (بودجه، مدار، کلید غایب) receipt با دلیل دقیق می‌سازد.
3. درخواست‌های ارزیابی (judge/Live-4) هرگز به fallback محلی نمی‌روند.
4. سقف بودجه (token + ساعت دیواری) قبل از هر ارسال چک می‌شود، نه بعد از شکست.
5. خروجی تست باید با `grep` قابل ممیزی باشد: هیچ اثری از الگوی کلید در آرتیفکت‌ها نباشد (گیت G6).

## ۱. معماری harness

```text
LoadConfig (frozen dataclass — همهٔ سقف‌ها یک‌جا)
   ↓
 AIMDTokenBucket ─┐
 CircuitBreaker ──┼─→ worker → send_one(retry/backoff/Retry-After) → RequestRecord
 Budget guard ────┘                                              ↓
                                     requests.jsonl  +  report.json (خلاصه + گیت‌ها)
```

- یک worker = یک virtual user با `user_id` پایدار: `loadtest-{run_tag}-vu{i:04d}`.
- `dry_run=True` → `httpx.MockTransport` با ۴۲۹/۵xx مصنوعی؛ هیچ شبکه‌ای زده نمی‌شود.

### پیکربندی

```python
@dataclass(frozen=True)
class LoadConfig:
    base_url: str
    model: str = "deepseek-v4-flash"
    api_key_env: str = "DEEPSEEK_API_KEY"
    user_field: str = "user_id"        # نام دقیق فیلد isolation سمت provider
                                       # [UNKNOWN] — قبل از اجرا از مستندات provider تأیید شود
    concurrency: int = 2500            # سقف هدف پلهٔ آخر
    ramp_steps: tuple[int, ...] = (10, 50, 100, 500, 1000, 2500)
    step_duration_s: float = 120.0
    total_requests: int = 50_000
    per_request_max_tokens: int = 256
    max_total_tokens: int = 8_000_000  # بودجهٔ سخت — قابل‌بستن توسط مالک
    wall_clock_budget_s: float = 1800.0
    # --- 429 / retry ---
    backoff_base_s: float = 0.5
    backoff_cap_s: float = 30.0
    max_attempts: int = 4              # ۱ تلاش اول + ۳ retry
    retry_budget_ratio: float = 0.20   # سهم مجاز retry از کل درخواست‌ها
    # --- client-side rate limiter ---
    initial_rate_rps: float = 200.0
    min_rate_rps: float = 5.0
    # --- circuit breaker ---
    cb_failure_threshold: int = 25
    cb_window_s: float = 10.0
    cb_open_s: float = 30.0
    # --- mode ---
    thinking: bool = False             # پرچم thinking — نام دقیق پارامتر provider-dependent
    dry_run: bool = True
    timeout_s: float = 120.0
```

## ۲. مدیریت ۴۲۹ (Rate Limit)

قاعدهٔ کلی: **۴۲۹ پیام کنترل ترافیک است، نه خطای منطقی.** پاسخ صحیح: کم‌کردن
نرخِ خودمان + احترام به سرور + retry منظم — نه retry خشمگانه.

1. **تفکیک خطا.** retryable: `408, 409, 425, 429, 500, 502, 503, 504, timeout,
   connection-reset`. non-retryable: `400, 401, 403, 404, 422` → receipt فوری، بدون retry
   (۴۰۱ در تست بار یعنی کلید/سطح دسترسی — ادامهٔ رَمپ بی‌معنی است).
2. **Retry-After مقدم است.** اگر هدر آمد (ثانیه یا HTTP-date)، همان مقدار + ۱ ثانیه
   حاشیه ملاک sleep است، نه فرمول خودمان.
3. **Exponential backoff با full jitter.** `sleep = uniform(0, min(cap, base * 2**attempt))`.
   jitter کامل لازم است وگرنه ۲۵۰۰ کلاینتِ هم‌زمانِ بازپخش‌شده دوباره همان قله را می‌سازند.
4. **سقف retry.** `max_attempts=4` و سهم retry از کل ≤ `retry_budget_ratio`؛ عبور از
   آن → receipt با `BLOCKED_RETRY_BUDGET` (نه loop بی‌نهایت).
5. **AIMD سمت کلاینت.** هر ۴۲۹ نرخ توکن‌باکِت را نصف می‌کند؛ رشتهٔ موفقیت‌ها آن را
   به‌آرامی برمی‌گرداند. این یعنی سیستم بعد از فشار خودش به تعادل می‌رسد.
6. **Circuit breaker.** ≥ ۲۵ خطا در ۱۰ ثانیه → OPEN به مدت ۳۰ ثانیه (هیچ ارسالی
   نمی‌پذیرد) → half-open با یک probe → CLOSED/OPEN دوباره. جلوگیری از «کوبیدن
   درِ قفل‌شده».
7. **هدرهای نرخ.** اگر provider هدرهای `X-RateLimit-*-Remaining` بدهد، قبل از صفر
   شدن داوطلبانه عقب‌بکش؛ ثبتشان در receipt لازم است.

### قطعه‌های هستهٔ ۴۲۹

```python
RETRYABLE_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


def backoff_delay(attempt: int, *, base: float, cap: float) -> float:
    """Full jitter: کشیدن یکنواخت از [0, سقف نمایی). بدون jitter،
    2500 کلاینتِ هم‌زمان دوباره همان قلهٔ ترافیکی را می‌سازند."""
    return random.uniform(0, min(cap, base * 2 ** attempt))


def retry_after_seconds(resp: httpx.Response) -> float | None:
    """Retry-After مقدم بر backoff خودمانست. دو فرم مجاز: ثانیه یا HTTP-date."""
    value = resp.headers.get("Retry-After")
    if value is None:
        return None
    if value.isdigit():
        return float(value)
    try:
        target = parsedate_to_datetime(value).timestamp()
        return max(0.0, target - time.time())
    except (TypeError, ValueError):
        return None
```

## ۳. کانکارنسی ۲۵۰۰ — نظارت و ایزولاسیون

[UNKNOWN] عدد ۲۵۰۰ سقف ادعایی سرویس است و در این vault هنوز راستی‌آزمایی نشده؛
پلهٔ آخرِ رَمپ باید آن را **آزمون** کند، نه فرض کند. اگر provider قبل از ۲۵۰۰
شکست پایدار داد، همان نقطه سقف واقعی است و در report ثبت می‌شود.

- **رَمپ پله‌ای:** `10 → 50 → 100 → 500 → 1000 → 2500`، هر پله ۱۲۰ ثانیه پایدار.
  پرش مستقیم به ۲۵۰۰ آزمونِ DDoS است نه آزمونِ ظرفیت.
- **`user_id` برای ایزولاسیون:** هر virtual user یک شناسهٔ پایدار و قابل‌فیلتر
  (`loadtest-{run}-vu{i}`) دارد. اثر: حسابداری نرخ/سهمیه و گروه‌بندی لاگ سمت
  provider جدا می‌شود؛ بعد از تست، ردیف‌های این run با یک prefix قابل قرنطینه/حذف‌اند.
  `user_id` هرگز حاوی اطلاعات شخصی یا هر چیزی شبیه کلید نیست — فقط رشتهٔ ثابت.
- **متریک‌های لحظه‌ای:** in-flight gauge، شمارندهٔ 429/5xx/timeout/retry،
  histogram تأخیر، توکن مصرفی، وضعیت مدار. هر درخواست یک ردیف JSONL:
  `ts, user_id, attempt, status, outcome, latency_s, prompt_tokens,
  completion_tokens, reasoning_tokens, error_class` — **بدون متن پرامپت کامل**
  (فقط طول/هش) تا آرتیفکت سبک و امن بماند.
- **جمع‌آوری:** عملیات موفق از `message.content` خوانده می‌شود؛
  `message.reasoning_content` فقط جداگانه لاگ می‌شود — هرگز به‌جای پاسخ
  (درس field-split سند vLLM امروز؛ [[../../00 - Inbox/2026-08-20 LLM-ARM-VS-JUDGE + VLLM-OPERATIONS]]).

## ۴. Harness پایتونیک (پیاده‌سازی مرجع)

وابستگی فقط `httpx`. اجرا: `DEEPSEEK_BASE_URL=... python loadtest.py` — کلید فقط از env.

```python
"""deepseek-v4-flash load-test harness — SPEC reference implementation.

Vault rules: key only from env · every block emits a receipt row ·
no fake success · budget checked before each send · dry_run default ON.
"""
from __future__ import annotations

import asyncio
import json
import os
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

RETRYABLE_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


def backoff_delay(attempt: int, *, base: float, cap: float) -> float:
    return random.uniform(0, min(cap, base * 2 ** attempt))


def retry_after_seconds(resp: httpx.Response) -> float | None:
    value = resp.headers.get("Retry-After")
    if value is None:
        return None
    if value.isdigit():
        return float(value)
    try:
        return max(0.0, parsedate_to_datetime(value).timestamp() - time.time())
    except (TypeError, ValueError):
        return None


class AIMDTokenBucket:
    """توکن‌باکِت با کاهش ضربی (429) و افزایش جمعی (موفقیت)."""

    def __init__(self, rate: float, min_rate: float, capacity: float | None = None):
        self.rate = rate
        self.initial_rate = rate
        self.min_rate = min_rate
        self.capacity = capacity or max(rate, 1.0)
        self.tokens = self.capacity
        self.updated = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        while True:
            async with self._lock:
                now = time.monotonic()
                self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.rate)
                self.updated = now
                if self.tokens >= 1:
                    self.tokens -= 1
                    return
                wait = (1 - self.tokens) / self.rate
            await asyncio.sleep(wait)

    def on_rate_limited(self) -> None:
        self.rate = max(self.min_rate, self.rate * 0.5)

    def on_success(self) -> None:
        self.rate = min(self.initial_rate, self.rate + 1.0)


class CircuitBreaker:
    """CLOSED → OPEN (آستانه در پنجره) → HALF_OPEN (یک probe) → CLOSED/OPEN."""

    def __init__(self, threshold: int, window_s: float, open_s: float):
        self.threshold, self.window_s, self.open_s = threshold, window_s, open_s
        self.failures: list[float] = []
        self.opened_at: float | None = None
        self._lock = asyncio.Lock()

    def allow(self) -> bool:
        if self.opened_at is None:
            return True
        if time.monotonic() - self.opened_at >= self.open_s:
            self.opened_at = None  # half-open: همه مجازند، اولین نتیجه حکم می‌دهد
            return True
        return False

    async def record(self, ok: bool) -> None:
        async with self._lock:
            if ok:
                self.failures.clear()
                return
            now = time.monotonic()
            self.failures = [t for t in self.failures if now - t < self.window_s]
            self.failures.append(now)
            if len(self.failures) >= self.threshold:
                self.opened_at = now


@dataclass
class Budget:
    max_total_tokens: int
    wall_clock_budget_s: float
    spent_tokens: int = 0
    retries: int = 0
    started: float = field(default_factory=time.monotonic)
    halted_reason: str = ""

    def check(self, cfg: "LoadConfig") -> str | None:
        if self.halted_reason:
            return self.halted_reason
        if self.spent_tokens >= self.max_total_tokens:
            self.halted_reason = "BLOCKED_BUDGET_TOKENS"
        elif time.monotonic() - self.started > self.wall_clock_budget_s:
            self.halted_reason = "BLOCKED_BUDGET_WALLCLOCK"
        # سهم retry نرخ است نه حد مطلق → در summarize/گیت G5 بررسی می‌شود
        return self.halted_reason or None


class ResizableSemaphore:
    """سمافوری که ظرفیتش بین پله‌های رَمپ عوض می‌شود."""

    def __init__(self, capacity: int):
        self._capacity, self._in_flight = capacity, 0
        self._cond = asyncio.Condition()

    async def __aenter__(self) -> None:
        async with self._cond:
            await self._cond.wait_for(lambda: self._in_flight < self._capacity)
            self._in_flight += 1

    async def __aexit__(self, *exc: Any) -> None:
        async with self._cond:
            self._in_flight -= 1
            self._cond.notify_all()

    async def resize(self, capacity: int) -> None:
        async with self._cond:
            self._capacity = capacity
            self._cond.notify_all()


@dataclass
class RequestRecord:
    ts: str
    user_id: str
    attempt: int
    status: int | None
    outcome: str          # OK | RATE_LIMITED | RETRIED_THEN_OK | FAILED | TIMEOUT | BLOCKED_*
    latency_s: float
    prompt_tokens: int
    completion_tokens: int
    reasoning_tokens: int
    error_class: str = ""


@dataclass(frozen=True)
class LoadConfig:
    base_url: str
    model: str = "deepseek-v4-flash"
    api_key_env: str = "DEEPSEEK_API_KEY"
    user_field: str = "user_id"          # نام دقیق فیلد isolation — از provider تأیید شود
    concurrency: int = 2500
    ramp_steps: tuple[int, ...] = (10, 50, 100, 500, 1000, 2500)
    step_duration_s: float = 120.0
    total_requests: int = 50_000
    per_request_max_tokens: int = 256
    max_total_tokens: int = 8_000_000
    wall_clock_budget_s: float = 1800.0
    backoff_base_s: float = 0.5
    backoff_cap_s: float = 30.0
    max_attempts: int = 4
    retry_budget_ratio: float = 0.20
    initial_rate_rps: float = 200.0
    min_rate_rps: float = 5.0
    cb_failure_threshold: int = 25
    cb_window_s: float = 10.0
    cb_open_s: float = 30.0
    thinking: bool = False
    dry_run: bool = True
    timeout_s: float = 120.0


def synth_prompt(i: int) -> str:
    """پرامپت مصنوعی قطعی (seed=index) — بازپخش‌پذیر و بدون داده واقعی."""
    rng = random.Random(i)
    tail = " ".join(rng.choice(["signal", "drift", "spine", "beat", "ledger"]) for _ in range(24))
    return f"[loadtest {i}] Summarize in one sentence: {tail}."


def dry_run_transport(request: httpx.Request) -> httpx.Response:
    """۴۲۹/۵xx مصنوعی با نرخ ثابت — مسیر retry/backoff/circuit را بدون پول می‌آزماید."""
    roll = random.random()
    if roll < 0.06:
        return httpx.Response(429, headers={"Retry-After": "1"}, json={"error": "mock rate limit"})
    if roll < 0.08:
        return httpx.Response(503, json={"error": "mock unavailable"})
    usage = {"prompt_tokens": 40, "completion_tokens": 12}
    return httpx.Response(200, json={
        "choices": [{"message": {"role": "assistant", "content": f"mock-ok {roll:.3f}"}}],
        "usage": usage,
    })


@dataclass
class Ctx:
    cfg: LoadConfig
    budget: Budget
    bucket: AIMDTokenBucket
    breaker: CircuitBreaker
    records: list[RequestRecord] = field(default_factory=list)
    key_present: bool = False


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


async def send_one(ctx: Ctx, client: httpx.AsyncClient, user_id: str, prompt: str) -> None:
    cfg = ctx.cfg
    payload: dict[str, Any] = {
        "model": cfg.model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": cfg.per_request_max_tokens,
        "stream": False,
        cfg.user_field: user_id,
    }
    # پرچم thinking نام دقیقش provider-dependent است؛ تا تأیید، ارسال نمی‌شود.
    if cfg.thinking:
        payload["thinking"] = {"type": "enabled"}   # [UNKNOWN] — نام فیلد را verify کن

    attempt = 0
    while True:
        block = ctx.budget.check(cfg)
        if block:
            ctx.records.append(RequestRecord(now_iso(), user_id, attempt, None, block, 0.0, 0, 0, 0))
            return
        if not ctx.breaker.allow():
            await asyncio.sleep(0.5)
            continue

        await ctx.bucket.acquire()
        started = time.monotonic()
        status: int | None = None
        error_class = ""
        try:
            resp = await client.post("/chat/completions", json=payload)
            status = resp.status_code
            if status == 200:
                data = resp.json()
                usage = data.get("usage", {})
                pt = usage.get("prompt_tokens", 0)
                ct = usage.get("completion_tokens", 0)
                rt = usage.get("completion_tokens_details", {}).get("reasoning_tokens", 0)
                ctx.budget.spent_tokens += pt + ct
                ctx.bucket.on_success()
                await ctx.breaker.record(ok=True)
                ctx.records.append(RequestRecord(
                    now_iso(), user_id, attempt, 200,
                    "OK" if attempt == 0 else "RETRIED_THEN_OK",
                    time.monotonic() - started, pt, ct, rt))
                return
            if status in RETRYABLE_STATUS and attempt < cfg.max_attempts - 1:
                delay = retry_after_seconds(resp)
                if delay is None and status == 429:
                    ctx.bucket.on_rate_limited()
                delay = (delay + 1.0) if delay is not None else backoff_delay(
                    attempt, base=cfg.backoff_base_s, cap=cfg.backoff_cap_s)
                await ctx.breaker.record(ok=False)
                ctx.budget.retries += 1
                attempt += 1
                await asyncio.sleep(delay)
                continue
            error_class = f"http_{status}"
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            error_class = type(exc).__name__
            if attempt < cfg.max_attempts - 1:
                await ctx.breaker.record(ok=False)
                ctx.budget.retries += 1
                attempt += 1
                await asyncio.sleep(backoff_delay(attempt, base=cfg.backoff_base_s, cap=cfg.backoff_cap_s))
                continue
        ctx.records.append(RequestRecord(
            now_iso(), user_id, attempt, status, "FAILED", time.monotonic() - started,
            0, 0, 0, error_class))
        return


async def worker(ctx: Ctx, client: httpx.AsyncClient, wid: int, gate: ResizableSemaphore,
                 queue: asyncio.Queue[int]) -> None:
    user_id = f"loadtest-{ctx.cfg.model}-vu{wid:04d}"
    while True:
        try:
            i = queue.get_nowait()
        except asyncio.QueueEmpty:
            return
        async with gate:
            await send_one(ctx, client, user_id, synth_prompt(i))
        queue.task_done()


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    k = min(len(values) - 1, int(round((p / 100.0) * (len(values) - 1))))
    return values[k]


def summarize(ctx: Ctx, duration_s: float) -> dict[str, Any]:
    ok = [r.latency_s for r in ctx.records if r.outcome in ("OK", "RETRIED_THEN_OK")]
    n_429 = sum(1 for r in ctx.records if r.status == 429)
    n_failed = sum(1 for r in ctx.records if r.outcome == "FAILED")
    n_blocked = sum(1 for r in ctx.records if r.outcome.startswith("BLOCKED"))
    retry_ratio = ctx.budget.retries / max(1, len(ctx.records))
    return {
        "ts": now_iso(),
        "model": ctx.cfg.model,
        "dry_run": ctx.cfg.dry_run,
        "key_present": ctx.key_present,
        "duration_s": round(duration_s, 1),
        "requests": len(ctx.records),
        "ok": len(ok),
        "failed": n_failed,
        "blocked": n_blocked,
        "http_429": n_429,
        "retries": ctx.budget.retries,
        "retry_ratio": round(retry_ratio, 4),
        "tokens_spent": ctx.budget.spent_tokens,
        "latency_s": {"p50": percentile(ok, 50), "p95": percentile(ok, 95), "p99": percentile(ok, 99)},
        "halted_reason": ctx.budget.halted_reason,
    }


async def run(cfg: LoadConfig) -> dict[str, Any]:
    key = os.environ.get(cfg.api_key_env, "")
    ctx = Ctx(
        cfg=cfg,
        budget=Budget(max_total_tokens=cfg.max_total_tokens, wall_clock_budget_s=cfg.wall_clock_budget_s),
        bucket=AIMDTokenBucket(cfg.initial_rate_rps, cfg.min_rate_rps),
        breaker=CircuitBreaker(cfg.cb_failure_threshold, cfg.cb_window_s, cfg.cb_open_s),
        key_present=bool(key),
    )
    if not cfg.dry_run and not ctx.key_present:
        ctx.budget.halted_reason = "PROVIDER_KEY_MISSING"   # receipt، بدون شبکه

    transport = httpx.MockTransport(dry_run_transport) if cfg.dry_run else None
    headers = {"Authorization": f"Bearer {key}"} if ctx.key_present else {}
    limits = httpx.Limits(max_connections=cfg.concurrency, max_keepalive_connections=cfg.concurrency)

    started = time.monotonic()
    queue: asyncio.Queue[int] = asyncio.Queue()
    for i in range(cfg.total_requests):
        queue.put_nowait(i)
    gate = ResizableSemaphore(cfg.ramp_steps[0])

    async with httpx.AsyncClient(base_url=cfg.base_url, timeout=cfg.timeout_s,
                                 headers=headers, limits=limits, transport=transport) as client:
        workers = [asyncio.create_task(worker(ctx, client, w, gate, queue))
                   for w in range(max(cfg.ramp_steps))]

        async def ramp() -> None:
            for step in cfg.ramp_steps:
                await gate.resize(step)
                await asyncio.sleep(cfg.step_duration_s)
            await gate.resize(cfg.concurrency)

        await asyncio.gather(ramp(), asyncio.gather(*workers))

    return summarize(ctx, time.monotonic() - started)


if __name__ == "__main__":
    cfg = LoadConfig(base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://invalid.example"))
    report = asyncio.run(run(cfg))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    with open(f"loadtest-report-{stamp}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))   # فقط اعداد؛ هرگز کلید
```

## ۵. چک‌لیست عملیاتی (فاز به فاز)

| فاز | کنترل | انتظار PASS |
|---|---|---|
| P0 پیش‌نیاز | کلید از env، بدون چاپ؛ سقف‌ها بسته؛ kill-switch | `key_present` صحیح؛ صفر network در dry-run |
| P1 دود-ران | mock transport با ۶٪ ۴۲۹ و ۲٪ ۵۰۳ | retry/backoff/circuit مسیرشان کار می‌کند؛ صفر تلاش بی‌سقف |
| P2 baseline | ۱ درخواست واقعی، non-thinking | پاسخ schema درست؛ جداسازی `content`/`reasoning_content` |
| P3 رَمپ | پله‌های ۱۰→۲۵۰۰، هر پله ۱۲۰s | نرخ خطا در هر پله هم‌روند؛ لاگ نرخ per-step |
| P4 soak | ماندن در ۲۵۰۰ تا سقف بودجه | بدون memory-leak کلاینت؛ throughput پایدار؛ 429→recovery خودکار |
| P5 fail-over | تزریق خطا (§۶) | receipt دقیق برای هر نوع؛ هیچ fake success |
| P6 مقایسه | thinking vs non-thinking (§۷) | متریک‌ها دو ستونه + confounder خودگزار گزارش شود |

## ۶. تست وضعیت‌های شکست (Fail-over)

هر سناریو یک‌بار تزریق می‌شود و رفتار observable ثبت می‌شود:

| تزریق | انتظار رفتار سیستم |
|---|---|
| timeout | retry با backoff؛ پس از `max_attempts` receipt `FAILED/TimeoutException` |
| 429 پیوسته | AIMD تا `min_rate`؛ مدار OPEN؛ هیچ بازپخش هم‌قله‌ای |
| 5xx پشت‌سرهم | مدار OPEN پس از آستانه؛ half-open probe بعد از ۳۰s؛ recovery خودکار |
| قطع شبکه | `TransportError` → همان مسیر retry؛ بدون crash کل process |
| 401 (کلید باطل) | non-retryable → توقف رَمپ؛ receipt صریح؛ ادامهٔ تست بی‌معنی |
| judge UNREADABLE | یک receipted re-ask؛ دومی = VOID (قرارداد V3) — نه حدس |

## ۷. thinking در برابر non-thinking

- **روش:** همان مجموعهٔ prompt (دسته‌های coding/retrieval/causal)، همان seed و
  temperature، دو اجرا فقط با پرچم thinking. نام دقیق پارامتر provider-dependent
  است [UNKNOWN] — در P2 راستی‌آزمایی شود.
- **متریک‌ها:** TTFT/TTLB (p50/95/99)، توکن‌ها (reasoning جدا از completion)،
  نرخ UNREADABLE، نرخ 429 (thinking معمولاً bucket سنگین‌تری دارد).
- **کیفیت:** قضاوت با جابه‌جایی متقابل (هر جفت در هر دو ترتیب) تا position bias
  خنثی شود؛ داور = DeepSeek خودش → `judge_independence_limited` به‌عنوان confounder
  در گزارش می‌آید (نتیجهٔ probe امروزی: flip rate ۲۵٪؛
  [[../../00 - Inbox/2026-08-20 LLM-ARM-VS-JUDGE + VLLM-OPERATIONS]]).
- **تفسیر:** هدف، حکم «بهتر بودن» نیست؛ هدف جداسازی هزینه/تأخیر/قابلیت اطمینان
  دو حالت زیر بار است.

## ۸. گیت‌های قبولی نهایی

```text
G1  key leakage در آرتیفکت‌ها (grep الگوی کلید)   = 0 مورد
G2  پوشش receipt (هر درخواست یک ردیف)              = 100%
G3  fake success                                   = 0
G4  recovery از 429 بدون دخالت دستی                = PASS
G5  retry_ratio                                    ≤ 0.20
G6  tokens_spent                                   ≤ max_total_tokens
G7  evaluation request با fallback محلی            = 0
G8  ارزیابی کیفیت با confounder سوگیری داور        گزارش شد
G9  سقف واقعی concurrency کشف و ثبت شد (≠ فرض)     ثبت شد
```

تا پیش از اجرا، وضعیت این سند `spec` است؛ بعد از اجرای واقعی، report کنار
گیت‌ها در `06-EVIDENCE/` می‌رود و این نوت به آن لینک می‌دهد.

## ۹. ریسک‌ها

- [RISK] تست بار پول می‌سوزاند — پیش‌فرض dry-run؛ سقف‌ها را مالک ببندد.
- [RISK] ۲۵۰۰ فرض است؛ سقف واقعی ممکن است پایین‌تر باشد — G9 صریحاً می‌سنجد.
- [RISK] محیط تست (prompt مصنوعی، یک مسیر شبکه) ≠ ترافیک production واقعی.
- [RISK] نرخ‌محورِ شبیه‌سازی‌شدهٔ کلاینت الگوی burst کاربران واقعی را کامل بازنمایی نمی‌کند.
- [RISK] مقایسه کیفیت با داور هم‌خانواده سوگیر است؛ فقط با برچسب confounder معتبر است.
