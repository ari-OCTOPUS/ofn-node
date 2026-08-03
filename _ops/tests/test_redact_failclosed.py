"""test_redact_failclosed.py — blindspot #131 (CRITICAL): _redact و _redact_pii
در صورتِ خطا هرگز متنِ خام برنمی‌گردانند (fail-closed).

پوشش:
- _redact: وقتی cockpit_readmodel.redact خطا می‌دهد → placeholder (نه متنِ خام)
- _redact_pii: وقتی sensory_bus import نمی‌شود → placeholder (نه متنِ خام)
- _redact: در شرایطِ عادی (بدونِ خطا) → رفتارِ طبیعی حفظ می‌شود

توجه: _redact و _redact_pii متدهای TelegramApprovalChannel (subclass) هستند.
برای تست، آن‌ها را به‌عنوان unbound با یک mock-self صدا می‌زنیم تا از
ساختنِ کلِ کانال (که token/owner/live-gate لازم دارد) بی‌نیاز شویم.
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

# ⚠️ `harness` تا ۲۰۲۶-۰۸-۰۳ فقط داخلِ `__main__` (پایینِ فایل) import می‌شد — یعنی
# **بعد از** import ِ opslib. ولی `opslib.STATE_DIR` در زمانِ import بسته می‌شود، پس
# `opslib.alert()` چهار بار روی `state/alert-signatures.json` ِ **زنده** می‌نوشت.
# ترتیب باربر است: setup قبل از اولین import ِ ماژولِ ارگانیسم.
import harness  # noqa: E402
ENV = harness.setup("redact-failclosed")

import opslib  # noqa: E402
import approval_channel as _ac  # noqa: E402

SECRET_INPUT = "this has a bot token 1234567890:AAdeadbeefdeadbeefdeadbeefdeadbeef inside"
PLAIN_INPUT = "just a normal message without secrets"
PII_INPUT = "my phone is 09121234567 call me"


def _redact(text):
    """صدا زدنِ unbound متد _redact با یک mock-self حداقلی."""
    return _ac.TelegramApprovalChannel._redact(MagicMock(), text)


def _redact_pii(text):
    """صدا زدنِ unbound متد _redact_pii با یک mock-self حداقلی."""
    return _ac.TelegramApprovalChannel._redact_pii(MagicMock(), text)


def test_redact_fail_closed_on_exception():
    """وقتی cockpit_readmodel.redact پرتاب می‌کند → متنِ خام هرگز برگردانده نمی‌شود."""
    with patch.dict("sys.modules", {"cockpit_readmodel": MagicMock()}):
        import cockpit_readmodel as _crm
        _crm.redact = MagicMock(side_effect=RuntimeError("scrub layer crashed"))
        result = _redact(SECRET_INPUT)
    assert "1234567890:AA" not in result, (
        f"FAIL-OPEN detected: raw token leaked: {result!r}")
    assert result == "[redacted: error in scrub layer]", (
        f"Unexpected placeholder: {result!r}")


def test_redact_fail_closed_on_import_error():
    """وقتی cockpit_readmodel اصلاً import نمی‌شود → placeholder."""
    with patch.dict("sys.modules", {"cockpit_readmodel": None}):
        result = _redact(SECRET_INPUT)
    assert "1234567890:AA" not in result, (
        f"FAIL-OPEN on ImportError: {result!r}")
    assert result == "[redacted: error in scrub layer]", (
        f"Unexpected on ImportError: {result!r}")


def test_redact_pii_fail_closed_on_import_error():
    """وقتی sensory_bus در دسترس نیست → متنِ خام برگردانده نمی‌شود."""
    with patch.dict("sys.modules", {"sensory_bus": None}):
        result = _redact_pii(PII_INPUT)
    assert "09121234567" not in result, (
        f"FAIL-OPEN: PII leaked: {result!r}")
    assert result == "[redacted: PII guard unavailable]", (
        f"Unexpected placeholder: {result!r}")


def test_redact_pii_fail_closed_on_attribute_error():
    """وقتی sensory_bus._contains_pii وجود ندارد → placeholder."""
    fake_bus = MagicMock(spec=[])  # بدونِ _contains_pii
    with patch.dict("sys.modules", {"sensory_bus": fake_bus}):
        result = _redact_pii(PII_INPUT)
    assert "09121234567" not in result, (
        f"FAIL-OPEN: PII leaked on missing _contains_pii: {result!r}")
    assert result == "[redacted: PII guard unavailable]", (
        f"Unexpected placeholder: {result!r}")


def test_redact_normal_operation():
    """در شرایطِ عادی (بدونِ خطا) → redact crash نمی‌کند و یک str برمی‌گرداند.

    ⚠️ نسخهٔ قدیمی فقط `isinstance(result, str)` را چک می‌کرد — یک type-assert که
    سبز می‌ماند حتی اگر `_redact` به یک pass-through تبدیل می‌شد (`return text`).
    حالا شاهدِ واقعی: یک توکنِ شناخته‌شده در ورودی باید در خروجی غایب باشد.
    این هم behavior assert است، نه فقط type assert."""
    result = _redact(SECRET_INPUT)
    assert isinstance(result, str), f"باید str باشد: {type(result)}"
    assert "1234567890:AA" not in result, (
        f"FAIL: redact در شرایطِ عادی توکن را نشست — pass-through شده؟ {result!r}")


if __name__ == "__main__":
    import harness
    failed = harness.run([
        ("#131: _redact fail-closed روی exception", test_redact_fail_closed_on_exception),
        ("#131: _redact fail-closed روی ImportError", test_redact_fail_closed_on_import_error),
        ("#131: _redact_pii fail-closed روی ImportError", test_redact_pii_fail_closed_on_import_error),
        ("#131: _redact_pii fail-closed روی AttributeError", test_redact_pii_fail_closed_on_attribute_error),
        ("#131: redact normal operation", test_redact_normal_operation),
    ])
    sys.exit(1 if failed else 0)
