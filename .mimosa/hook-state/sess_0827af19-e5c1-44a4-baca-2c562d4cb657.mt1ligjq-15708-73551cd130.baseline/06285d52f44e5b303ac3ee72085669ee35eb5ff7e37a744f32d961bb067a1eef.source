#!/usr/bin/env python3
"""test_chat_log.py — سرور-ساید Chat Log (سیو گفتگو در وب‌اپ)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("chat-log")
_OPS = harness.SELF_OPS

sys.path.insert(0, str(_OPS))
sys.path.insert(0, str(_OPS / "owner_console"))

import chat_log as cl  # noqa: E402


def _fresh():
    """isolated state dir برای تست — هرگز لاگ واقعی را لمس نمی‌کند."""
    cl.STATE_DIR = Path(ENV["ops"]) / "state"
    cl.CHAT_FILE = cl.STATE_DIR / "chat" / "chat-log.jsonl"


def t_append_writes_jsonl():
    _fresh()
    r = cl.append(role="owner", kind="chat", text="سلام اختاپوس", run_id="run_abc")
    assert r["ok"] is True
    assert cl.CHAT_FILE.is_file()
    rows = cl.recent(limit=10)
    assert len(rows) == 1
    assert rows[0]["role"] == "owner"
    assert rows[0]["text"] == "سلام اختاپوس"


def t_recent_newest_first():
    _fresh()
    cl.append(role="owner", kind="chat", text="پیام ۱")
    cl.append(role="collaborator", kind="chat", text="پاسخ ۱")
    rows = cl.recent(limit=10)
    assert rows[0]["text"] == "پاسخ ۱"
    assert rows[1]["text"] == "پیام ۱"


def t_redact_initdata_never_saved():
    _fresh()
    evil = "initData=query_id=AA1&user=%7B%22id%22%3A42%7D"
    cl.append(role="owner", kind="chat", text="hi " + evil)
    rows = cl.recent(limit=10)
    assert "query_id=AA1" not in rows[0]["text"]
    assert "initData=<redacted>" in rows[0]["text"]


def t_redact_secret_patterns():
    _fresh()
    cl.append(role="owner", kind="chat",
              text="my api_key=sk-1234567890abcdef should not leak")
    rows = cl.recent(limit=10)
    assert "sk-1234567890abcdef" not in rows[0]["text"]
    assert "<redacted>" in rows[0]["text"]


def t_limit():
    _fresh()
    for i in range(15):
        cl.append(role="owner", kind="chat", text=f"msg-{i}")
    assert len(cl.recent(limit=5)) == 5
    assert len(cl.recent(limit=30)) == 15


def t_empty_when_no_file():
    _fresh()
    if cl.CHAT_FILE.is_file():
        cl.CHAT_FILE.unlink()
    assert cl.recent(limit=10) == []
    assert cl.as_context_block() == ""


def t_fail_soft_bad_dir():
    _fresh()
    # یک فایل به‌جای دایرکتوری → mkdir شکست می‌خورد → fail-soft بدون raise
    blocker = Path(ENV["ops"]) / "state" / "chat-blocker"
    blocker.parent.mkdir(parents=True, exist_ok=True)
    blocker.write_text("not a dir", encoding="utf-8")
    cl.CHAT_FILE = blocker / "sub" / "y.jsonl"
    r = cl.append(role="owner", kind="chat", text="بدون دایرکتوری")
    assert r["ok"] is False  # raise نمی‌کند؛ fail-soft
    blocker.unlink()


def t_may_authorize_always_false():
    _fresh()
    cl.append(role="owner", kind="chat", text="authorize?")
    rows = cl.recent(limit=10)
    assert rows[0]["may_authorize"] is False


def t_as_context_block_contains_roles():
    _fresh()
    cl.append(role="owner", kind="chat", text="دربارهٔ هدف من")
    cl.append(role="collaborator", kind="chat", text="پاسخ")
    block = cl.as_context_block(limit=4)
    assert "مالک" in block
    assert "اختاپوس" in block


def t_run_id_and_model_source_preserved():
    _fresh()
    cl.append(role="collaborator", kind="chat", text="جواب",
              run_id="run_xyz", model_source="secondary:deepseek")
    rows = cl.recent(limit=10)
    assert rows[0]["run_id"] == "run_xyz"
    assert rows[0]["model_source"] == "secondary:deepseek"


def t_redact_len_cap():
    _fresh()
    long_text = "x" * 5000
    cl.append(role="owner", kind="chat", text=long_text)
    rows = cl.recent(limit=10)
    assert len(rows[0]["text"]) <= 2000


ALL = [v for k, v in sorted(globals().items()) if k.startswith("t_")]


def main():
    failed = 0
    for fn in ALL:
        try:
            fn()
            print(f"  ✅ {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  ❌ {fn.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  ❌ {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\nchat_log: {len(ALL) - failed}/{len(ALL)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
