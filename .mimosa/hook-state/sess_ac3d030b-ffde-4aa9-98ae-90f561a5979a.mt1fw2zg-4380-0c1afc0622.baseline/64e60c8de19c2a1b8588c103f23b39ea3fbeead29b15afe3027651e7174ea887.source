#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_model_router_paid_observability — دو تابعِ نوِ ۲۰۲۶-۰۸-۰۹ («پیشرفتِ
واقعی» بعدِ باگِ سقفِ هفتگیِ Fugu که فقط از داشبوردِ Sakana قابلِ‌فهم بود):

  ۱) _error_detail: جزئیاتِ واقعیِ HTTPError (status+body) به‌جایِ فقط اسمِ کلاس،
     با secret-redaction.
  ۲) _log_provider_usage_safe: پلِ fail-soft به owner_cockpit/db.py — هرگز
     مسیرِ اصلیِ مغز را نمی‌شکند، حتی اگر db.py نبود یا خطا داد.

هیچ‌کدام DB واقعی (owner_cockpit.db) را لمس نمی‌کنند — db با فیک جایگزین می‌شود
(DB_PATH خودش hardcode است، env-override ندارد، پس فیک تنها راهِ ایزوله است).
"""
import sys
import urllib.error
from pathlib import Path

import harness

ENV = harness.setup("model-router-paid-observability")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "cortex"))
import model_router as MR  # noqa: E402


# ── _error_detail ────────────────────────────────────────────────────────────

def t_http_error_status_and_reason_are_captured():
    exc = urllib.error.HTTPError("https://api.sakana.ai/v1/chat/completions",
                                  429, "Too Many Requests", {}, None)
    d = MR._error_detail(exc)
    assert "429" in d, d
    assert "Too Many Requests" in d, d


def t_http_error_body_is_captured_when_readable():
    import io
    body = b'{"error":"weekly limit exceeded","code":"rate_limited"}'
    exc = urllib.error.HTTPError("https://api.sakana.ai/v1/chat/completions",
                                  429, "Too Many Requests", {}, io.BytesIO(body))
    d = MR._error_detail(exc)
    assert "weekly limit exceeded" in d, d


def t_non_http_error_still_gets_class_and_message():
    d = MR._error_detail(TimeoutError("read timed out after 20s"))
    assert "TimeoutError" in d and "20s" in d, d


def t_bearer_token_in_message_is_redacted():
    exc = ValueError("auth failed: Bearer <REDACTED-OPENAI-KEY>")
    d = MR._error_detail(exc)
    assert "<REDACTED-OPENAI-KEY>" not in d, d
    assert "REDACTED" in d, d


def t_output_is_length_capped():
    exc = ValueError("x" * 5000)
    d = MR._error_detail(exc, limit=300)
    assert len(d) <= 300, len(d)


# ── _log_provider_usage_safe ─────────────────────────────────────────────────

class _FakeOwnerDB:
    def __init__(self):
        self.calls = []

    def log_provider_usage(self, **kwargs):
        self.calls.append(kwargs)
        return 1


def t_delegates_correct_args_to_owner_cockpit_db():
    fake = _FakeOwnerDB()
    sys.modules["db"] = fake
    try:
        MR._log_provider_usage_safe(model="fugu", task="deep", tier="primary",
                                    usage={"input_tokens": 10, "output_tokens": 5,
                                           "total_cost_usd": 0.0},
                                    latency_ms=850, status="ok")
        assert len(fake.calls) == 1, fake.calls
        c = fake.calls[0]
        assert c["model"] == "fugu" and c["task"] == "deep" and c["tier"] == "primary"
        assert c["status"] == "ok" and c["latency_ms"] == 850
    finally:
        sys.modules.pop("db", None)


def t_error_status_and_detail_pass_through_on_failure():
    fake = _FakeOwnerDB()
    sys.modules["db"] = fake
    try:
        MR._log_provider_usage_safe(model="fugu", task="deep", tier="primary",
                                    latency_ms=900, status="error",
                                    error="HTTPError: 429 Too Many Requests")
        assert fake.calls[0]["status"] == "error"
        assert "429" in fake.calls[0]["error"]
    finally:
        sys.modules.pop("db", None)


def t_never_raises_when_db_module_is_broken():
    class _BrokenDB:
        def log_provider_usage(self, **kwargs):
            raise RuntimeError("db locked")
    sys.modules["db"] = _BrokenDB()
    try:
        MR._log_provider_usage_safe(model="fugu", task="x", tier="primary", status="ok")
    except Exception as e:  # noqa: BLE001
        raise AssertionError(f"باید fail-soft باشد، استثنا داد: {e}")
    finally:
        sys.modules.pop("db", None)


def t_never_raises_when_db_module_is_missing_entirely():
    sys.modules.pop("db", None)
    # owner_cockpit/db.py واقعاً import-پذیر است (فایل هست)، پس این فقط اثبات
    # می‌کند که import موفق هم اگر بشود، صدازدنِ واقعی هرگز مسیر را نمی‌شکند —
    # چون DB_PATH hardcode است، این call روی دیسکِ واقعی هم fail-soft امتحان
    # می‌شود (فلگِ OCTOPUS_WIRE_OWNER_DB در محیطِ تست روشن نیست → واقعاً no-op).
    MR._log_provider_usage_safe(model="fugu", task="x", tier="primary", status="ok")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_") and callable(v)]
    fails = []
    for t in tests:
        try:
            t()
            print("  ✅", t.__name__)
        except Exception as e:  # noqa: BLE001
            fails.append((t.__name__, e))
            print("  ❌", t.__name__, "-", e)
    print(("PASS" if not fails else "FAIL"), f"— test_model_router_paid_observability — {len(fails)} failures")
    sys.exit(1 if fails else 0)
