"""test_organ_console.py — Wave 1 (2026-07-15): تبِ 🦾 اندام‌ها.
لیستِ صادقِ legها + توگلِ فعال/غیرفعال از مسیرِ موجودِ flag/flaggo (توکنِ یک‌مصرف + تأییدِ
دومرحله‌ای). صفر مسیرِ mutationِ جدید — فقط data + reuseِ handlerهای ممیزی‌شده."""
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness
ENV = harness.setup("organ_console")

from approval_channel import TelegramApprovalChannel  # noqa: E402


def _chan():
    return TelegramApprovalChannel()


def t_a_organs_registered_in_gates():
    assert "organs" in TelegramApprovalChannel.TAB_PAGES
    for k in ("ziman", "cartographer", "mining"):
        assert k in TelegramApprovalChannel.FLAG_KEYS, k
        assert k in TelegramApprovalChannel.ACT_ALLOWLIST["flag"], k
        assert k in TelegramApprovalChannel.ACT_ALLOWLIST["flaggo"], k
    # هیچ verbِ پولی اضافه نشده
    assert TelegramApprovalChannel.MONEY_VERBS == frozenset()


def t_b_organs_command_lists_all_legs():
    out = _chan().handle_command("/organs")
    assert isinstance(out, dict), out
    txt = out["text"]
    for label in ("Lead", "Ziman", "Cartographer", "Mining", "Crypto", "Accounting", "Knowledge"):
        assert label in txt, label
    assert "اندام" in txt and "فعال:" in txt


def t_c_toggle_buttons_are_tokened_flag_verbs():
    kb = _chan()._tab_keyboard("organs")["inline_keyboard"]
    cds = [b["callback_data"] for row in kb for b in row]
    for key in ("lead", "ziman", "cartographer", "mining"):
        assert any(cd.startswith(f"act:flag:{key}:") and len(cd.split(":")) == 4 for cd in cds), key
    assert any(cd.startswith("act:doctor:run:") for cd in cds)   # دکمهٔ دکتر
    assert "menu:main" in cds


def t_d_current_flag_reflects_live_env():
    ch = _chan()
    os.environ.pop("OCTOPUS_WIRE_MINING", None)
    assert ch._current_flag("OCTOPUS_WIRE_MINING") is False
    os.environ["OCTOPUS_WIRE_MINING"] = "1"
    try:
        assert ch._current_flag("OCTOPUS_WIRE_MINING") is True
    finally:
        os.environ.pop("OCTOPUS_WIRE_MINING", None)


def t_e_toggle_confirm_mints_flaggo_token():
    os.environ.pop("OCTOPUS_WIRE_ZIMAN", None)     # خاموش → کارت باید «روشن کن» + توکنِ flaggo بدهد
    card = _chan()._act_flag_confirm("ziman")
    assert isinstance(card, dict)
    cds = [b["callback_data"] for row in card["reply_markup"]["inline_keyboard"] for b in row]
    assert any(cd.startswith("act:flaggo:ziman:") for cd in cds), cds
    assert "OCTOPUS_WIRE_ZIMAN" in card["text"]


def t_f_render_never_crashes():
    r = _chan()._render_tab("organs")
    assert isinstance(r, dict) and "text" in r and "reply_markup" in r


if __name__ == "__main__":
    for f in (t_a_organs_registered_in_gates, t_b_organs_command_lists_all_legs,
              t_c_toggle_buttons_are_tokened_flag_verbs, t_d_current_flag_reflects_live_env,
              t_e_toggle_confirm_mints_flaggo_token, t_f_render_never_crashes):
        f()
        print("ok", f.__name__)
    print("PASS test_organ_console")
