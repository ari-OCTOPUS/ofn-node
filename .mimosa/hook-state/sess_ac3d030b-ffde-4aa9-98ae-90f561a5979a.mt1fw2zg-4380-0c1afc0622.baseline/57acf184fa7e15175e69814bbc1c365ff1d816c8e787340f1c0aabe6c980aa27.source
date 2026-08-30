#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_menu_contract — قراردادِ منشور (TG-UI-CHARTER-2026-07-31) روی منوی بات.

W1 لِین A (رأی‌های ۱–۴ + قاعدهٔ UX §۶.۵):
  · منوی DM ‏≤۱۰ فرمان و فقط شخصی/وضعیتی — بلوکِ قیفِ لید/بیزنس هرگز.
  · منو scope-دار ثبت می‌شود (BotCommandScopeAllPrivateChats) و منوی گروه
    **خالی** می‌شود (رابطِ گروه فارسیِ طبیعی است، نه اسلش).
  · نشانگرِ ثبت محتوایی است (هش) — تغییرِ فهرست دقیقاً یک ثبتِ مجدد.
  · تک-نویسندگیِ منوی باتِ inner: مرکز هرگز نمی‌نویسدش (outer-bot-12).
  · فرمان‌های حذف‌شده از منو، handler ِ تایپی‌شان می‌ماند (W3 مصرفشان می‌کند).

هر بند طوری نوشته شده که جهشِ معکوس (برگرداندنِ بلوکِ قیف، برداشتنِ scope،
push ِ دوبارهٔ منوی inner) قرمزش کند.
"""
import json
import os
import re
import shutil
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))

import harness

ENV = harness.setup("tg-menu-contract")

sys.path.insert(0, str(_HERE.parent / "telegram_center"))

import opslib   # noqa: E402
import center   # noqa: E402

CFG_PATH = opslib.STATE_DIR / "telegram" / "center-config.json"

# بلوکِ ۹تاییِ قیفِ لید + خویشاوندانِ بیزنسی که رأی ۴ از منوی DM بیرون کرد.
FUNNEL_AND_BUSINESS = {"lead", "funnel", "won", "lost", "paid", "sent",
                       "replied", "meeting", "quote", "deal", "revenue"}


class FakeClient:
    """کلاینتِ ساختگی — فقط ثبتِ فراخوان‌ها؛ صفر شبکه."""

    def __init__(self, owner_id=777):
        self.owner_id = owner_id
        self.owner_chat_id = owner_id
        self.calls: list = []
        self._next_mid = 100
        self._next_topic = 10

    def wired(self):
        return True

    def send(self, text, *, topic_id=None, keyboard=None, chat_id=None,
             pin=False, stream=None):
        self.calls.append(("send", {"text": text, "topic_id": topic_id,
                                    "chat_id": chat_id, "pin": pin}))
        self._next_mid += 1
        return self._next_mid

    def edit(self, message_id, text, keyboard=None, chat_id=None):
        self.calls.append(("edit", {"message_id": message_id}))
        return True

    def pin_message(self, message_id, chat_id=None):
        return True

    def create_topic(self, name, chat_id=None):
        self._next_topic += 1
        return self._next_topic

    def set_commands(self, commands, scope=None):
        self.calls.append(("set_commands", {"commands": list(commands),
                                            "scope": scope}))
        return True

    def delete_commands(self, scope=None):
        self.calls.append(("delete_commands", {"scope": scope}))
        return True

    def poll_updates(self, offset=0, timeout_s=25):
        return []

    def answer_callback(self, callback_id, text=""):
        self.calls.append(("answer", {"id": callback_id, "text": text}))
        return True

    def is_owner(self, update):
        frm = ((update.get("message") or {}).get("from")
               or (update.get("callback_query") or {}).get("from") or {})
        return frm.get("id") == self.owner_id

    def named(self, kind):
        return [c for k, c in self.calls if k == kind]


def _reset():
    shutil.rmtree(opslib.STATE_DIR / "telegram", ignore_errors=True)


def _setup_center():
    fc = FakeClient()
    c = center.Center(client=fc, clock=lambda: 1000.0, render_mod=None)
    assert c.ensure_setup() is True
    return fc, c


# ── شکلِ منو ────────────────────────────────────────────────────────────────
def t_a_private_menu_is_at_most_ten_commands():
    """قاعدهٔ UX §۶.۵ — ‏≤۱۰ فرمانِ اسلش."""
    assert len(center.COMMANDS) <= 10, \
        f"منوی DM ‏{len(center.COMMANDS)} فرمان دارد — سقفِ منشور ۱۰ است"


def t_b_no_funnel_or_business_name_in_the_dm_menu():
    """رأی ۴ + رأی صریح «نقاشی/پول/زیمان هرگز در DM»."""
    names = {c for c, _ in center.COMMANDS}
    leaked = sorted(names & FUNNEL_AND_BUSINESS)
    assert not leaked, f"فرمانِ قیف/بیزنس به منوی DM برگشت: {leaked}"


def t_c_removed_commands_keep_their_typed_handlers():
    """حذف از منو ≠ حذفِ قابلیت: handler ِ تایپی می‌ماند (W3 لازمش دارد)."""
    src = (Path(center.__file__)).read_text("utf-8")
    i = src.index("handlers = {")
    j = src.index("fn = handlers.get(cmd)", i)
    table = src[i:j]
    for cmd in sorted(FUNNEL_AND_BUSINESS):
        assert f'"/{cmd}"' in table, \
            f"/{cmd} از جدولِ handler هم حذف شد — قرارداد فقط حذف از منو بود"


# ── ثبتِ scope-دار ──────────────────────────────────────────────────────────
def t_d_the_private_scope_is_actually_passed_to_set_commands():
    """جهشِ «scope را ننویس» باید قرمز شود — نه فقط شکلِ ثابتِ فهرست."""
    _reset()
    fc, _ = _setup_center()
    sc = fc.named("set_commands")
    assert len(sc) == 1, sc
    assert [c for c, _ in center.COMMANDS] == [c for c, _ in sc[0]["commands"]]
    assert sc[0]["scope"] == {"type": "all_private_chats"}, \
        f"منو بدونِ scope ثبت شد: {sc[0]['scope']!r}"


def t_e_the_group_menu_is_emptied_with_the_group_scope():
    """منوی گروه = خالی (deleteMyCommands روی all_group_chats) — رابطِ گروه
    فارسیِ طبیعیِ LEG_VERBS است، منوی اسلش آن‌جا فقط گمراهی است."""
    _reset()
    fc, _ = _setup_center()
    dc = fc.named("delete_commands")
    # دو پاک‌سازی در بوتِ اول: scope ِ گروه + scope ِ default (کشفِ readback ِ
    # deploy ِ ۰۷-۳۱: لیستِ کهنهٔ default روی سرور، fallback ِ گروه‌ها بود).
    assert len(dc) == 2, f"منوی گروه/default پاک نشد: {dc}"
    scopes = [d.get("scope") for d in dc]
    assert {"type": "all_group_chats"} in scopes, dc
    assert None in scopes or {} in scopes, f"پاک‌سازیِ default غایب: {dc}"


def t_f_menu_registration_happens_exactly_once_per_content_change():
    """نشانگرِ محتوایی: بوتِ دوم صفر ثبت؛ دستکاریِ هش ⇒ دقیقاً یک ثبتِ دیگر."""
    _reset()
    fc, c = _setup_center()
    assert len(fc.named("set_commands")) == 1
    assert c.ensure_setup() is True
    assert len(fc.named("set_commands")) == 1, "بوتِ دوم دوباره ثبت کرد"
    assert len(fc.named("delete_commands")) == 2, "بوتِ دوم دوباره پاک کرد"
    cfg = json.loads(CFG_PATH.read_text("utf-8"))
    assert cfg.get("commands_set_v2"), "نشانگرِ محتوایی نوشته نشد"
    cfg["commands_set_v2"] = "stale-hash"
    CFG_PATH.write_text(json.dumps(cfg, ensure_ascii=False), "utf-8")
    assert c.ensure_setup() is True
    assert len(fc.named("set_commands")) == 2, \
        "تغییرِ محتوا (هشِ کهنه) ثبتِ مجدد را ماشه نزد"


def t_g_a_client_without_scope_support_still_gets_a_menu():
    """کلاینتِ قدیمی (بدونِ پارامترِ scope) ⇒ fallback ِ بدونِ scope، نه سکوت.
    (قراردادِ میان-لِین: tg_api ِ لِین C ممکن است دیرتر برسد.)"""
    _reset()

    class OldClient(FakeClient):
        def set_commands(self, commands):          # بدونِ scope — عمداً
            self.calls.append(("set_commands", {"commands": list(commands),
                                                "scope": "unsupported"}))
            return True

    fc = OldClient()
    c = center.Center(client=fc, clock=lambda: 1000.0, render_mod=None)
    assert c.ensure_setup() is True
    sc = fc.named("set_commands")
    assert len(sc) == 1 and sc[0]["scope"] == "unsupported", sc


# ── تک-نویسندگیِ منوی inner ─────────────────────────────────────────────────
def t_h_center_never_writes_the_inner_bot_menu():
    """outer-bot-12: دو پروسه منوی باتِ inner را با دو فهرست می‌نوشتند.
    از امروز نویسندهٔ منوی inner فقط approval_channel است؛ مرکز هیچ."""
    _reset()
    os.environ["OCTOPUS_TG_SPLIT_V1"] = "1"
    try:
        fc = FakeClient()
        c = center.Center(client=fc, clock=lambda: 1000.0, render_mod=None)
        inner = FakeClient()
        c._inner = inner
        assert c.ensure_setup() is True
        assert inner.named("set_commands") == [], "مرکز منوی inner را نوشت"
        assert inner.named("delete_commands") == [], "مرکز منوی inner را پاک کرد"
    finally:
        os.environ.pop("OCTOPUS_TG_SPLIT_V1", None)
    # و در سطحِ سورس: مسیرِ push ِ قدیمی (نشانگرِ commands_set_inner) برنگشته.
    src = Path(center.__file__).read_text("utf-8")
    assert "commands_set_inner" not in src, \
        "push ِ منوی inner به مرکز برگشت — تک-نویسندگی نقض شد"


def t_i_the_len_marker_survives_for_the_discoverability_guard():
    """گاردِ discoverability متنِ `commands_set != len(COMMANDS)` را می‌سنجد —
    نشانگرِ محتوایی جایگزینش نشده، کنارش نشسته."""
    src = Path(center.__file__).read_text("utf-8")
    assert 'cfg.get("commands_set") != len(COMMANDS)' in src
    assert "commands_set_v2" in src


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_menu_contract: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
