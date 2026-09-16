# Mining Pre-Execution MVP

> وضعیت: **read-only / INFORM-only**. این کد برای طراحی، اعتبارسنجی، گزارش و برنامه‌ریزی است؛ نه اجرای ماینینگ.

این بسته یک اسکلت پایه برای پروژه Mining می‌سازد که قبل از ورود به execution بتواند:

- VERDICT_QUEUE را چک کند.
- رجیستری سخت‌افزار را validate کند.
- قید برق `<$0.05/kWh یا solar` را enforce کند.
- سیاست `zero agent wallet access` را به‌صورت gate بررسی کند.
- کاندیدهای کوین را فقط در قالب draft report امتیازدهی کند.
- death-watch را طبق D2 ارزیابی کند.
- گزارش Markdown بسازد.

## Octopus leg integration

این بسته علاوه‌بر ابزارهای pre-execution، طرح اتصال Mining به اختاپوس را هم نگه می‌دارد:

- `docs/OCTOPUS_LEG_DESIGN.md` — طرح و پلن پای Mining به‌عنوان زیرمجموعه Octopus، با دو مغز: سخت‌افزار + کشف کوین.
- `docs/OCTOPUS_LEG_REQUIREMENTS_MATRIX.md` — ماتریس نیازمندی‌ها، edge caseها و verification.
- runtime نازک Octopus در `_ops/legs/mining_leg.py` قرار دارد و از طریق `_ops/wiring.py` و `ORGANISM-STATE.mining` به Telegram Center وصل می‌شود.

نکته: `OCTOPUS_WIRE_MINING` عمداً پیش‌فرض خاموش است و داخل `PAPER_FULL_FLAGS` نیست؛ فعال‌سازی فقط بعد از verdict مالک و باز شدن Security Gate.

## کارهایی که عمداً انجام نمی‌دهد

- SSH به نودها
- deploy
- start/stop miner
- wallet/seed/private key access
- buy/sell/withdraw
- اتصال به pool
- اجرای XMRig/cpuminer

## نصب محلی

```bash
cd "02 - Code/mining_preexec_mvp"
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## نمونه اجرا

### گزارش readiness

```bash
python -m mining_preexec_mvp.cli readiness \
  --hardware examples/hardware_registry.example.yaml \
  --verdicts examples/verdict_queue.example.yaml \
  --wallet-zero-access \
  --output output/readiness.md
```

### گزارش coin scout draft

```bash
python -m mining_preexec_mvp.cli scout \
  --candidates examples/coin_candidates.example.yaml \
  --output output/coin_scout.md
```

## فلسفه طراحی

این MVP با وضعیت فعلی پروژه هماهنگ است:

```yaml
phase: pre-execution
execution_state: ZERO mining active
autonomy_floor: INFORM-only
```

پس همه چیز fail-closed طراحی شده. هر چیزی که به execution نزدیک شود باید با human verdict انجام شود.
