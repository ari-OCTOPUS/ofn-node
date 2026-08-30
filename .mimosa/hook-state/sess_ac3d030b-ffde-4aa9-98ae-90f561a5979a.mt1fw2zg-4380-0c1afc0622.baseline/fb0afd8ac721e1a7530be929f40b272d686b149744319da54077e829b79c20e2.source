"""Test env — dummy keys so config.py's fail-fast passes without a real .env.

Real env vars (if set) win over these; .env placeholders are overridden
because pydantic-settings gives process env priority over env_file.
"""
import os

_DUMMY = {
    "ANTHROPIC_API_KEY": "sk-ant-test-dummy",
    "TELEGRAM_BOT_TOKEN": "1:test-dummy",
    "TELEGRAM_CHAT_ID": "123",
    "TAVILY_API_KEY": "tvly-test-dummy",
    "PLANNING_ALERTS_API_KEY": "test-dummy",
}
for _k, _v in _DUMMY.items():
    os.environ.setdefault(_k, _v)
