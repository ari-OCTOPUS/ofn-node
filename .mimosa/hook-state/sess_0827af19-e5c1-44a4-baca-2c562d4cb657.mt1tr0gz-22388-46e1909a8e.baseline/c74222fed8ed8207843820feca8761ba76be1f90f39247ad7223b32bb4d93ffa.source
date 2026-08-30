#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_budgets_resilience_config.py — اعتبارسنجیِ بخشِ resilience.circuit_breaker در
budgets.yaml (پسوندِ additive، ۲۰۲۶-۰۷-۲۵).

زمینه: circuit_breaker._cfg() بخشِ resilience.circuit_breaker را از budgets.yaml
می‌خواند. تا پیش از این تست هیچ بخشی وجود نداشت و breaker با defaultها کار می‌کرد.
وقتی ناپایداریِ fugu (timeoutهای مکرر) رخ داد، سقفِ شکستِ سراسری (FUGU_FAIL_CEILING=3
در flags.cmd) به STOP-FUGU رسید و مغزِ primary کل ماه را مسدود کرد. این بخشِ
resilience به breakerِ per-provider می‌گوید زودتر fail-fast کند تا سهمیه نسوزد.

این تست سه چیز را ثابت می‌کند:
  ۱) بخشِ resilience.circuit_breaker در budgets.yamlِ زنده وجود دارد و قابلِ parse است.
  ۲) circuit_breaker._cfg() آن را می‌خواند (نه default) — failure_threshold ≤ ۵.
  ۳) مقادیر در محدودهٔ معقول‌اند (cooldown ۳۰–۱۲۰s، threshold ۲–۸).

توجهِ صداقت: تست‌های دیگر (test_cortex_circuit_breaker) با TEST_BUDGETSِ harness
(بدون resilience) کار می‌کنند و default=۵ را می‌بینند — این تست فقط فایلِ زنده را
می‌خواند تا کوکِ production را اعتبارسنجی کند.

$0 و آفلاین. صفر نوشتن در درختِ زنده.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("budgets-resilience")
_OPS = Path(__file__).resolve().parent.parent

# فایلِ budgets.yamlِ زنده (نه sandboxِ harness) — production config.
_LIVE_BUDGETS = _OPS / "budget" / "budgets.yaml"


# ═══ ۱) بخشِ resilience در فایلِ زنده موجود و parseشدنی است ═════════════════
def t1_resilience_section_present_and_parseable():
    assert _LIVE_BUDGETS.exists(), f"budgets.yaml باید وجود داشته باشد: {_LIVE_BUDGETS}"
    try:
        import yaml
    except ImportError as e:  # pragma: no cover
        raise AssertionError(f"PyYAML لازم است: {e}")
    data = yaml.safe_load(_LIVE_BUDGETS.read_text("utf-8"))
    assert isinstance(data, dict), "budgets.yaml باید dict باشد"
    res = data.get("resilience")
    assert isinstance(res, dict), \
        "بخشِ resilience باید وجود داشته باشد (افزودهٔ ۲۰۲۶-۰۷-۲۵)"
    cb = res.get("circuit_breaker")
    assert isinstance(cb, dict), "resilience.circuit_breaker باید dict باشد"


# ═══ ۲) مقادیر در محدودهٔ معقول ═════════════════════════════════════════════
def t2_resilience_values_in_sane_range():
    import yaml
    data = yaml.safe_load(_LIVE_BUDGETS.read_text("utf-8"))
    cb = data["resilience"]["circuit_breaker"]

    ft = int(cb.get("failure_threshold"))
    assert 2 <= ft <= 8, \
        f"failure_threshold باید ۲–۸ باشد (got {ft})؛ بالا=آرام‌بسته، پایین=سریع‌بسته"
    # هدفِ پسوندِ ۲۰۲۶-۰۷-۲۵: reducer سریع‌تر از default (۵) به ناپایداری واکنش دهد.
    assert ft <= 5, \
        f"هدف: failure_threshold ≤ ۵ برای پاسخِ سریع به ناپایداری (got {ft})"

    cd = float(cb.get("cooldown_seconds"))
    assert 30.0 <= cd <= 120.0, \
        f"cooldown_seconds باید ۳۰–۱۲۰ باشد (got {cd})"

    hom = int(cb.get("half_open_max"))
    assert 1 <= hom <= 5, \
        f"half_open_max باید ۱–۵ باشد (got {hom})"

    stc = int(cb.get("success_to_close"))
    assert 1 <= stc <= 3, \
        f"success_to_close باید ۱–۳ باشد (got {stc})"


# ═══ ۳) circuit_breaker._cfg() مقادیر را از yaml می‌خواند ════════════════════
def t3_cfg_reads_from_yaml():
    """اگر load_budgets() بخشِ resilience را برگرداند، _cfg() باید آن را ببیند.
    این تست فقط قراردادِ خواندن را ثابت می‌کند — در sandboxِ harness،
    TEST_BUDGETS بخشِ resilience ندارد، پس ما yamlِ زنده را به طور موقت جای‌گزین
    می‌کنیم تا خواندن واقعی را ببینیم."""
    import yaml
    import opslib
    # opslib.BUDGETS_YAML در sandbox به TEST_BUDGETS اشاره می‌کند؛ ما فایلِ زنده را
    # روی sandbox کپی می‌کنیم تا _cfg() بخشِ resilience واقعی را بخواند.
    live_data = yaml.safe_load(_LIVE_BUDGETS.read_text("utf-8"))
    assert "resilience" in live_data, "precondition: فایلِ زنده resilience دارد"
    # کپیِ فایلِ زنده روی sandbox
    import shutil
    shutil.copy2(_LIVE_BUDGETS, opslib.BUDGETS_YAML)
    # force re-read
    try:
        opslib._budgets_cache = None  # اگر کش بود
    except AttributeError:
        pass
    sys.path.insert(0, str(_OPS / "budget"))
    import circuit_breaker as cb
    cfg = cb._cfg()
    assert cfg.get("tag", "").startswith("FACT"), \
        f"وقتی yaml بخشِ resilience دارد، tag باید FACT باشد (got {cfg.get('tag')})"
    ft = int(cfg["failure_threshold"])
    assert ft == int(live_data["resilience"]["circuit_breaker"]["failure_threshold"]), \
        f"_cfg باید failure_threshold را از yaml بخواند (yaml={live_data['resilience']['circuit_breaker']['failure_threshold']}, cfg={ft})"


if __name__ == "__main__":
    failed = harness.run([
        ("۱ بخشِ resilience موجود و parseشدنی", t1_resilience_section_present_and_parseable),
        ("۲ مقادیر در محدودهٔ معقول", t2_resilience_values_in_sane_range),
        ("۳ _cfg از yaml می‌خواند", t3_cfg_reads_from_yaml),
    ])
    sys.exit(1 if failed else 0)
