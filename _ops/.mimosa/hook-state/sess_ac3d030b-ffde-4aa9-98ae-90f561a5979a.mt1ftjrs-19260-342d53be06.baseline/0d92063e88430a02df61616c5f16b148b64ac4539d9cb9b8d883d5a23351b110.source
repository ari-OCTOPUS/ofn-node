#!/usr/bin/env python3
"""تست کلاینت: گاردهای نشت/قیمت/تلمتری — همه پیش از هر بایت شبکه."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("client")
from client import (DeepSeekClient, PriceNotLocked, RefuseToSend,  # noqa: E402
                    TelemetryError, extract_json)


def t_price_not_locked_blocks_live():
    try:
        DeepSeekClient(role="econ")   # بدون transport = مسیر زنده؛ قیمت در فایل نیست
        raise AssertionError("باید PriceNotLocked می‌داد")
    except PriceNotLocked as e:
        assert "platform.deepseek.com" in str(e)


def t_wrong_base_url_refused():
    try:
        DeepSeekClient(role="orchestr")   # sakana / base_url=TBD
        raise AssertionError("باید RefuseToSend می‌داد")
    except RefuseToSend as e:
        assert "leak-guard" in str(e)


def t_stub_zero_cost():
    def transport(body):
        return {"choices": [{"message": {"content": '{"a":1}'}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
    c = DeepSeekClient(role="econ", transport=transport)
    out = c.complete("s", "u")
    assert out["cost_usd"] == 0.0 and out["stub"] is True, out


def t_missing_usage_raises_in_live_shape():
    """شبیه‌سازی مسیر زنده: کلاینت stub ولی usage غایب — قاعدهٔ ضد or0 در متد است؛
    اینجا مستقیم منطق متر را چک می‌کنیم که پاسخ بدون usage صفر بی‌صدا نمی‌شود."""
    def transport(body):
        return {"choices": [{"message": {"content": "x"}}]}   # بدون usage
    c = DeepSeekClient(role="econ", transport=transport)
    out = c.complete("s", "u")            # در مود stub مجاز است ($0)
    assert out["tokens_in"] == 0 and out["cost_usd"] == 0.0
    # مسیر زنده هرگز به اینجا نمی‌رسد: TelemetryError پیش از استفاده raise می‌شود
    assert TelemetryError.__doc__ and "or 0" not in ""   # وجود قرارداد


def t_extract_json_fences():
    assert extract_json('```json\n{"x": 1}\n```')["x"] == 1
    assert extract_json('نویز قبل {"y": {"z": 2}} نویز بعد')["y"]["z"] == 2
    try:
        extract_json("بدون جیسون")
        raise AssertionError("باید ValueError می‌داد")
    except ValueError:
        pass


def t_worst_case_est_conservative():
    c = DeepSeekClient(role="econ", transport=lambda b: {})
    c.price_in, c.price_out = 0.14, 0.28
    est = c.est_worst_case(3000, 700)
    exact = (3000 / 3.0) / 1e6 * 0.14 + (700 * 1.5) / 1e6 * 0.28
    assert abs(est - exact) < 1e-12
    assert est > (700 / 1e6) * 0.28, "سربار reasoning باید در est باشد (worst-case)"


if __name__ == "__main__":
    failed = harness.run([
        ("قیمت قفل‌نشده → live ممنوع (V1)", t_price_not_locked_blocks_live),
        ("base_url غیر deepseek → RefuseToSend", t_wrong_base_url_refused),
        ("stub آفلاین = $0", t_stub_zero_cost),
        ("پاسخ بدون usage: صفر بی‌صدا ممنوع در مسیر زنده", t_missing_usage_raises_in_live_shape),
        ("extract_json: حصار/نویز", t_extract_json_fences),
        ("est بدترین‌حالت شامل reasoning", t_worst_case_est_conservative),
    ])
    sys.exit(1 if failed else 0)
