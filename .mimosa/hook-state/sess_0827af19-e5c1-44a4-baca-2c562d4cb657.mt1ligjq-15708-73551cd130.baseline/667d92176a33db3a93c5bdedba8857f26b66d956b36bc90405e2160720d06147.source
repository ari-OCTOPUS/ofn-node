"""تست‌های رجیستری + adapterِ تلگرامِ زیمان (G6 سمتِ ziman-agent).

به‌صورتِ بسته import می‌شود تا importهای نسبی (from .product) کار کنند.
"""
import sys
from pathlib import Path

AGENT = Path(__file__).resolve().parent.parent      # ziman-agent/
sys.path.insert(0, str(AGENT))

from ziman.command_registry import ZimanCommandRegistry  # noqa: E402
from ziman.telegram_adapter import ZimanTelegramAdapter  # noqa: E402


def test_registry_classifies_and_resolves_alias():
    r = ZimanCommandRegistry.load()
    assert r.classify("/approve")["risk"] == "RED"
    assert r.classify("/status")["risk"] == "GREEN"
    assert r.canonical("/ziman_status") == "/status"
    assert r.classify("/nope")["known"] is False       # fail-closed


def test_adapter_accepts_canonical_and_legacy():
    a = ZimanTelegramAdapter(capacity_ceiling=30, inventory_hint=20)
    # هر دو باید همان دایجستِ وضعیت را بدهند
    assert a.route("/status") == a.route("/ziman_status")
    assert "Ziman" in a.route("/status")


def test_adapter_catalog_digest_uses_real_catalog():
    a = ZimanTelegramAdapter()
    out = a.route("/catalog")
    # اگر کاتالوگ در repo باشد باید شمارش بدهد؛ در چک‌اوتِ دیگر پیامِ امن
    assert ("کل=" in out) or ("در دسترس نیست" in out) or ("خالی" in out)


def test_adapter_governance_tag():
    a = ZimanTelegramAdapter()
    assert a._governance_tag("/approve").startswith("⟦RED")
    assert a._governance_tag("/status").startswith("⟦GREEN")
    assert a._governance_tag("/nope") == ""


def test_ziman_content_alias_routes_like_catalog():
    """رگرسیونِ یافتهٔ #3: /ziman_content (alias→/catalog) و /catalog باید یکی باشند."""
    a = ZimanTelegramAdapter()
    assert a.route("/ziman_content") == a.route("/catalog")


def test_unknown_command_still_safe():
    a = ZimanTelegramAdapter()
    assert "Unknown command" in a.route("/definitely_unknown")
