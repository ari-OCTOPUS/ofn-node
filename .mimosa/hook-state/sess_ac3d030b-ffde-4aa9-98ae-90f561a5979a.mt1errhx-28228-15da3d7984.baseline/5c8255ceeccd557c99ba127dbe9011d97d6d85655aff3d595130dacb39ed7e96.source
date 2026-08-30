"""Config — fail-fast & placeholder detection (dummy env set by conftest)."""
from config import _is_placeholder, settings


def test_placeholder_detection():
    assert _is_placeholder("")
    assert _is_placeholder("  ")
    assert _is_placeholder("<ROTATE-ME-new-key>")
    assert _is_placeholder("sk-ant-api03-xxxxxxxx")
    assert _is_placeholder("your-key-here")
    assert not _is_placeholder("sk-ant-real-abc123")
    assert not _is_placeholder("7234567890:AAGdfgXYZ")


def test_required_keys_all_present_in_test_env():
    assert settings.missing_required() == []


def test_required_keys_list_is_complete():
    assert set(settings.REQUIRED_KEYS) == {
        "anthropic_api_key",
        "telegram_bot_token",
        "telegram_chat_id",
        "tavily_api_key",
        "planning_alerts_api_key",
    }
