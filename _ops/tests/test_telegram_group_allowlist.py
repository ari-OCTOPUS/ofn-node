#!/usr/bin/env python3
"""تست گروه‌پذیریِ کاکپیت تلگرام (رأی مالک 2026-07-17 «یک ربات واحد، DM+گروه»).

$0 آفلاین. نگاه می‌دارد که:
  · نبودِ TELEGRAM_ALLOWED_CHAT_IDS → فقط owner (byte-identical با قبل، هیچ regression).
  · حضورِ TELEGRAM_ALLOWED_CHAT_IDS → owner + گروه‌ها اضافه؛ junk skip.
  · پاسخ به همان chat_id که فرمان از آن آمد (نه همیشه owner) — send_text(chat_id=...).
  · handle_command chat_id می‌پذیرد (backward-compat: None = قبل).
  · شاخهٔ delegationِ langar fail-soft است: نبودِ langar → ربات برای بقیه کار می‌کند.

مرتبط: approval_channel.py:_allowed_chat_ids, send_text(chat_id), handle_command(chat_id),
       شاخهٔ langar_bridge_dispatch. langar_bridge.py لمس نمی‌شود در این تست (تنها fail-soft).
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("telegram-group-allowlist")
import approval_channel as ac  # noqa: E402
from approval_channel import TelegramApprovalChannel as TC  # noqa: E402


def t_a_allowlist_byte_identical_when_env_unset():
    """نبودِ env → فقط owner (هیچ regression)."""
    os.environ.pop("TELEGRAM_ALLOWED_CHAT_IDS", None)
    a = ac._allowed_chat_ids(6150431610)
    assert a == frozenset([6150431610]), f"FAIL: {a}"
    # owner=None → مجموعهٔ خالی (نه guess، نه crash)
    assert ac._allowed_chat_ids(None) == frozenset(), "FAIL: owner=None must be empty"


def t_b_allowlist_adds_group_ids_skips_junk():
    """حضورِ env → owner + گروه‌ها اضافه؛ junk/خالی skip (هرگز guess)."""
    os.environ["TELEGRAM_ALLOWED_CHAT_IDS"] = "-1001234567890, -1009876543210, junk, ,abc"
    try:
        a = ac._allowed_chat_ids(6150431610)
        assert a == frozenset([6150431610, -1001234567890, -1009876543210]), f"FAIL: {a}"
        assert -1001234567890 in a, "FAIL: group missing"
        assert "junk" not in a and "abc" not in a, "FAIL: junk accepted"
    finally:
        os.environ.pop("TELEGRAM_ALLOWED_CHAT_IDS", None)


def t_c_channel_allowed_set_in_init():
    """TelegramApprovalChannel._allowed از init ساخته می‌شود (owner + env)."""
    os.environ.pop("TELEGRAM_ALLOWED_CHAT_IDS", None)
    c = TC(token="FAKE", owner_chat_id=6150431610,
           http_get=lambda *a, **k: {}, http_post=lambda *a, **k: {"ok": True})
    assert c._allowed == frozenset([6150431610]), f"FAIL: {c._allowed}"
    assert c.wired is True


def t_d_send_text_targets_provided_chat_id():
    """send_text(chat_id=...) به همان chat می‌رود (نه همیشه owner). گروه‌پذیری."""
    sent = []
    def fake_post(url, body, timeout_s=10.0):
        sent.append(body)
        return {"ok": True}
    c = TC(token="FAKE", owner_chat_id=6150431610,
           http_get=lambda *a, **k: {}, http_post=fake_post)
    # به owner (پیش‌فرض)
    c.send_text("hello-owner")
    assert sent and sent[-1]["chat_id"] == 6150431610, f"FAIL owner-default: {sent}"
    # به گروه
    c.send_text("hello-group", chat_id=-1001234567890)
    assert sent[-1]["chat_id"] == -1001234567890, f"FAIL group-target: {sent}"


def t_e_handle_command_accepts_chat_id_kw():
    """handle_command(text, chat_id=...) کار می‌کند (backward-compat با None)."""
    c = TC(token="FAKE", owner_chat_id=6150431610,
           http_get=lambda *a, **k: {}, http_post=lambda *a, **k: {"ok": True})
    # None = قبل (owner)
    r1 = c.handle_command("/status")
    assert r1 is not None, "FAIL: /status returned None (owner)"
    # chat_id گروه — نباید crash
    r2 = c.handle_command("/status", chat_id=-1001234567890)
    assert r2 is not None, "FAIL: /status returned None (group chat_id)"


def t_f_unknown_command_returns_none():
    """دستورِ ناشناخته → None (تا مسیرهای دیگر فعال بمانند؛ شاخهٔ langar هم None می‌دهد)."""
    c = TC(token="FAKE", owner_chat_id=6150431610,
           http_get=lambda *a, **k: {}, http_post=lambda *a, **k: {"ok": True})
    assert c.handle_command("/this-does-not-exist-xyz") is None, "FAIL: unknown should be None"


def t_g_langar_bridge_dispatch_fail_soft_when_absent():
    """اگر langar در دسترس نباشد، langar_bridge_dispatch → None (fail-soft، ربات زنده)."""
    # import تنبل: فراخوانی بدونِ langar نصب → None
    r = ac.langar_bridge_dispatch("/pf_status", chat_id=-1001234567890, owner=6150431610)
    # اگر langar هست، احتمالاً رشته‌ای برمی‌گرداند؛ اگر نیست، None. هر دو قابل‌قبول
    # به‌شرطی که crash نکند. تستِ کلیدی: هیچ استثنایی پرتاب نمی‌شود.
    assert r is None or isinstance(r, (str, dict)), f"FAIL: unexpected type {type(r)}"


def main():
    tests = [
        t_a_allowlist_byte_identical_when_env_unset,
        t_b_allowlist_adds_group_ids_skips_junk,
        t_c_channel_allowed_set_in_init,
        t_d_send_text_targets_provided_chat_id,
        t_e_handle_command_accepts_chat_id_kw,
        t_f_unknown_command_returns_none,
        t_g_langar_bridge_dispatch_fail_soft_when_absent,
    ]
    n_ok = 0
    for t in tests:
        try:
            t()
            print(f"  ✅ {t.__name__}")
            n_ok += 1
        except AssertionError as e:
            print(f"  ❌ {t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            print(f"  💥 {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{'✅ ALL GREEN' if n_ok == len(tests) else f'❌ {len(tests)-n_ok} FAILED'} ({n_ok}/{len(tests)})")
    return 0 if n_ok == len(tests) else 1


if __name__ == "__main__":
    sys.exit(main())
